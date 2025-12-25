import logging
import math
from turtle import left, right
import numpy as np
import numpy.ma as ma
from pathlib import Path
import matplotlib.pyplot as plt
from enum import Enum
from scipy.ndimage import label, sum_labels, find_objects
import pymupdf as pdf
import wx
from tqdm import tqdm
from matplotlib import use, get_backend
from typing import Literal

from .common import A4_rect, rect_cm, list_to_html, list_to_html_aligned, get_rect_from_text, dict_to_html, dataframe_to_html, single_line_to_html
from .common import inches2cm, pts2cm, cm2pts, cm2inches, DefaultLayoutA4, NamedTemporaryFile, pt2inches, TemporaryDirectory
from ..wolf_array import WolfArray, header_wolf, vector, zone, Zones, wolfvertex as wv, wolfpalette
from ..PyVertexvectors import vector, zone, Zones, wolfvertex as wv
from ..PyCrosssections import crosssections, profile
from ..PyTranslate import _
from .pdf import PDFViewer

class CSvsDEM_MainLayout(DefaultLayoutA4):
    """
    Layout for comparing cross-sections, array and Lidar LAZ in a report.

    1 cadre pour la zone traitée avec photo de fond ign + contour vectoriel
    1 cadre avec zoom plus large min 250m
    1 cadre avec matrice ref + contour vectoriel
    1 cadre avec matrice à comparer + contour vectoriel
    1 cadre avec différence
    1 cadre avec valeurs de synthèse

    1 cadre avec histogramme
    1 cadre avec histogramme des différences
    """

    def __init__(self, title:str, filename = '', ox = 0, oy = 0, tx = 0, ty = 0, parent=None, is2D=True, idx = '', plotted = True, mapviewer=None, need_for_wx = False, bbox = None, find_minmax = True, shared = False, colors = None):
        super().__init__(title, filename, ox, oy, tx, ty, parent, is2D, idx, plotted, mapviewer, need_for_wx, bbox, find_minmax, shared, colors)

        useful = self.useful_part

        width = useful.xmax - useful.xmin
        height = useful.ymax - useful.ymin

        self._map = self.add_element("Map", width=10., height=10., x = useful.xmin, y=useful.ymax - 10.)

        self._summaries = self.add_element_repeated("Summary", width= width - 10. - self.padding, height=5. - self.padding/2.,
                                                 first_x=self._map.xmax + self.padding, first_y=self._map.ymin,
                                                 count_x=1, count_y=2, padding=0.5)

        self._tables = self.add_element_repeated("Tables", width= (width-self.padding) / 2, height= 10.,
                                                 first_x=useful.xmin, first_y=useful.ymin,
                                                 count_x=2, count_y=1, padding=0.5)

        self._legend_tables = self.add_element_repeated("Legend Tables", width= (width-self.padding) / 2, height= 0.5,
                                                    first_x=useful.xmin, first_y=self._tables.ymax + 0.2 ,
                                                    count_x=2, count_y=1, padding=0.5)

        self._histogram = self.add_element("Histogram", width= width, height= 3.,
                                                 x=useful.xmin, y=self._legend_tables.ymax + 0.2)

class CSvsDEM_IndividualLayout(DefaultLayoutA4):

    def __init__(self, title:str, filename = '', ox = 0, oy = 0, tx = 0, ty = 0, parent=None, is2D=True, idx = '', plotted = True, mapviewer=None, need_for_wx = False, bbox = None, find_minmax = True, shared = False, colors = None):
        super().__init__(title, filename, ox, oy, tx, ty, parent, is2D, idx, plotted, mapviewer, need_for_wx, bbox, find_minmax, shared, colors)

        useful = self.useful_part

        width = useful.xmax - useful.xmin
        height = useful.ymax - useful.ymin

        self._maps = self.add_element_repeated("Maps", width= (width-self.padding) / 2, height=9., count_x=2, count_y=1, first_x=useful.xmin, first_y=useful.ymax - 9.)

        self._cs = self.add_element("Cross-Sections", width= width, height=9., x=useful.xmin, y=self._maps.ymin - 9. - self.padding)

        self._dem = self.add_element("DEM", width= (width - self.padding) / 3, height=5., x = useful.xmin, y=useful.ymin)
        self._compare_cs = self.add_element("Comparison", width= (width - self.padding) * 2 / 3, height=5., x = self._dem.xmax + self.padding, y=useful.ymin)

class CSvsDEM():
    """
    Class to manage the difference between a unique cross-section and a DEM.
    """

    def __init__(self, data_group:list, idx:int, dem: WolfArray, title:str = "", index_group:int = 0,index_cs:int = 0, rebinned_dem:WolfArray = None):

        self._dpi = 600
        self.default_size_hitograms = (12, 6)
        self.default_size_arrays = (10, 10)
        self._fontsize = 6

        self._data_group = data_group
        self._idx = idx

        self.dem = dem
        self._rebinned_dem:WolfArray = rebinned_dem

        if self.dem.nbnotnull > 1_000_000 and self._rebinned_dem is None:
            logging.warning("The DEM has more than 1 million valid cells. Plotting a rebin one.")
            self._rebinned_dem = WolfArray(mold=dem)
            self._rebinned_dem.rebin(10)
            self._rebinned_dem.mypal = dem.mypal

        self._cs: profile
        self._cs = data_group[idx]['profile']

        assert isinstance(self.dem, WolfArray), "DEM must be a WolfArray instance."
        assert isinstance(self._cs, profile), "Cross-section must be a profile instance."

        self.title = title
        self.index_cs = index_cs
        self.index_group = index_group

        self._background = 'IGN'

    @property
    def differences(self) -> tuple[float, float]:
        """ Get the difference between the cross-section and the DEM at extremities. """

        if not isinstance(self.dem, WolfArray):
            raise TypeError("DEM must be an instance of WolfArray")

        # Get the DEM value at the cross-section location
        dem_value = self.dem.get_value(self._cs[0].x, self._cs[0].y)

        if dem_value is None or ma.is_masked(dem_value):
            return np.nan

        # Get the cross-section value (assuming it's a single value at this point)
        cs_value = self._cs[0].z

        if cs_value is None or ma.is_masked(cs_value):
            return np.nan

        diff_left = cs_value - dem_value

        dem_value = self.dem.get_value(self._cs[-1].x, self._cs[-1].y)
        if dem_value is None or ma.is_masked(dem_value):
            return np.nan
        cs_value = self._cs[-1].z
        if cs_value is None or ma.is_masked(cs_value):
            return np.nan
        diff_right = cs_value - dem_value
        return diff_left, diff_right

    def __str__(self):

        l_diff, r_diff = self.differences

        ret = self._label + '\n'
        ret += _("Group : ") + str(self._idx) + '\n'
        ret += _("Section : ") + str(self._cs.myname) + '\n'
        ret += _("Left coordinates (X, Y) : ({:3f},{:3f})").format(self._cs[0].x, self._cs[0].y) + '\n'
        ret += _("Right coordinates (X, Y) : ({:3f},{:3f})").format(self._cs[-1].x, self._cs[-1].y) + '\n'
        ret += _("Left difference : {:3f}").format(l_diff) + '\n'
        ret += _("Right difference : {:3f}").format(r_diff) + '\n'

        return ret

    def set_palette_distribute(self, minval:float, maxval:float, step:int=0):
        """
        Set the palette for both arrays.
        """
        self.dem.mypal.distribute_values(minval, maxval, step)

    def set_palette(self, values:list[float], colors:list[tuple[int, int, int]]):
        """
        Set the palette for both arrays based on specific values.
        """
        self.dem.mypal.set_values_colors(values, colors)

    def plot_position_grey(self, figax:tuple[plt.Figure, plt.Axes]=None, size_around:float=250) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the reference array with a background.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        h = self.dem.get_header()
        h.origx = (self._cs[0].x + self._cs[-1].x)/2. - size_around
        h.origy = (self._cs[0].y + self._cs[-1].y)/2. - size_around
        h.dx = size_around * 2
        h.dy = size_around * 2
        h.nbx = 1
        h.nby = 1

        new = WolfArray(srcheader=h)
        new.array.mask[:,:] = True

        if self._background.upper() == 'IGN' or self._background.upper() == 'NGI':
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Cartoweb= True,
                                        cat = 'topo_grey',
                                        )
        else:
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Cartoweb= False,
                                        cat = 'topo_grey',
                                        )

        copy = self._cs.deepcopy()
        copy.myprop.width = 1
        copy.myprop.color = 0xFF0000
        copy.plot_matplotlib(ax=ax)
        self._cs._plot_extremities(ax, s=10)

        self.plot_cs_in_group(figax=figax, width=1, color=0x0000FF)

        return fig, ax


    def plot_position(self, figax:tuple[plt.Figure, plt.Axes]=None,
                      width:int = 3,
                      color:int = 0xFF0000) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the dem array.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        h = self.dem.get_header()
        h.dx = h.nbx * h.dx
        h.dy = h.nby * h.dy
        h.nbx = 1
        h.nby = 1

        new_array = WolfArray(srcheader=h)
        new_array.array.mask[:,:] = True

        if self._background.upper() == 'IGN' or self._background.upper() == 'NGI':
            new_array.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        IGN= True,
                                        cat = 'orthoimage_coverage',
                                        )

        elif self._background.upper() == 'WALONMAP':
            new_array.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Walonmap= True,
                                        cat = 'IMAGERIE/ORTHO_2022_ETE',
                                        )
        else:
            new_array.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Walonmap= False,
                                        )


        copy = self._cs.deepcopy()
        copy.myprop.width = width
        copy.myprop.color = color
        copy.plot_matplotlib(ax=ax)
        del copy

        return fig, ax

    def plot_position_around(self,
                             figax:tuple[plt.Figure, plt.Axes]=None,
                             size_around:float = 50.,
                             width:int = 3,
                             color:int = 0xFF0000,
                             s_extremities:int = 50,
                             colors_extremities:tuple[str, str] = ('blue', 'green')) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the dem array.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        # search bounds in group
        min_x = min([sect['profile'].xmin for sect in self._data_group])
        max_x = max([sect['profile'].xmax for sect in self._data_group])
        min_y = min([sect['profile'].ymin for sect in self._data_group])
        max_y = max([sect['profile'].ymax for sect in self._data_group])

        h = self.dem.get_header()
        h.origx = min_x - size_around
        h.origy = min_y - size_around
        h.dx = (max_x - min_x + size_around * 2)
        h.dy = (max_y - min_y + size_around * 2)
        h.nbx = 1
        h.nby = 1

        new_array = WolfArray(srcheader=h)
        new_array.array.mask[:,:] = True

        if self._background.upper() == 'IGN' or self._background.upper() == 'NGI':
            new_array.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        IGN= True,
                                        cat = 'orthoimage_coverage',
                                        )

        elif self._background.upper() == 'WALONMAP':
            new_array.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Walonmap= True,
                                        cat = 'IMAGERIE/ORTHO_2022_ETE',
                                        )
        else:
            new_array.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Walonmap= False,
                                        )


        copy = self._cs.deepcopy()
        copy.myprop.width = width
        copy.myprop.color = color
        copy.plot_matplotlib(ax=ax)
        self._cs._plot_extremities(ax, s=s_extremities, colors=colors_extremities)

        self.plot_cs_in_group(figax=figax, width=2, color=0x0000FF)

        return fig, ax

    def plot_cs_in_group(self, figax:tuple[plt.Figure, plt.Axes]=None,
                         width:int = 2,
                         color:int = 0x0000FF) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the others cross-sections in the group if exists.
        """

        if len(self._data_group) <= 1:
            return figax

        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        for idx, sect in enumerate(self._data_group):
            if idx == self._idx:
                continue

            cs:profile
            cs = sect['profile']
            copy = cs.deepcopy()
            copy.myprop.width = width
            copy.myprop.color = color
            copy.plot_matplotlib(ax=ax)
            del copy

        return fig, ax

    def plot_dem_around(self,
                             figax:tuple[plt.Figure, plt.Axes]=None,
                             size_around:float = 10.,
                             width:int = 3,
                             color:int = 0xFF0000,
                             s_extremities:int = 50,
                             colors_extremities:tuple[str, str] = ('blue', 'green')) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the dem array.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        h = self.dem.get_header()
        h.origx = (self._cs[0].x + self._cs[-1].x)/2. - size_around
        h.origy = (self._cs[0].y + self._cs[-1].y)/2. - size_around
        h.dx = size_around * 2
        h.dy = size_around * 2
        h.nbx = 1
        h.nby = 1

        new_array = WolfArray(mold = self.dem, crop=h.get_bounds())
        new_array.updatepalette()
        new_array.plot_matplotlib(figax=figax, figsize = self.default_size_arrays, first_mask_data=False, with_legend=True, update_palette= False)

        copy = self._cs.deepcopy()
        copy.myprop.width = width
        copy.myprop.color = color
        copy.plot_matplotlib(ax=ax)
        self._cs._plot_extremities(ax, s=s_extremities, colors=colors_extremities)

        ax.legend(fontsize=6)

        return fig, ax


    def plot_position_scaled(self, scale = 4,
                             figax:tuple[plt.Figure, plt.Axes]=None,
                             width:int = 3,
                             color:int = 0xFF0000) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the reference array.

        :param scale: Scale factor to apply to the extent of the DEM. For example, scale=1 will double the extent, scale=2 will triple it, etc.
        :param figax: Tuple of (Figure, Axes) to plot on. If None, a new figure and axes will be created.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        h = self.dem.get_header()
        a_width = h.nbx * h.dx
        a_height = h.nby * h.dy

        h.origx += -a_width * scale / 2
        h.origy += -a_height *scale / 2
        h.nbx = 1
        h.nby = 1
        h.dx = a_width *(scale + 1)
        h.dy = a_height *(scale + 1)

        new = WolfArray(srcheader=h)
        new.array.mask[:,:] = True

        if self._background.upper() == 'IGN' or self._background.upper() == 'NGI':
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        IGN= True,
                                        cat = 'orthoimage_coverage')
        elif self._background.upper() == 'WALONMAP':
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Walonmap= True,
                                        cat = 'IMAGERIE/ORTHO_2022_ETE')
        else:
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Walonmap= False)

        copy = self._cs.deepcopy()
        copy.myprop.width = width
        copy.myprop.color = color
        copy.plot_matplotlib(ax=ax)
        del copy

        return fig, ax

    def plot_dem(self, figax:tuple[plt.Figure, plt.Axes]=None) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the reference array.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        if self._rebinned_dem is not None:
            self._rebinned_dem.plot_matplotlib(figax=figax, figsize = self.default_size_arrays, first_mask_data=False, with_legend=True, update_palette= False)
        else:
            self.dem.plot_matplotlib(figax=figax, figsize = self.default_size_arrays, first_mask_data=False, with_legend=True, update_palette= False)

        copy = self._cs.deepcopy()
        copy.myprop.width = 5
        copy.myprop.color = 0xFF0000
        copy.plot_matplotlib(ax=ax)
        del copy

        return fig, ax

    def plot_cs(self, figax:tuple[plt.Figure, plt.Axes]=None) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the cross section to compare.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        old_plotted = self.dem.plotted
        self.dem.plotted = True
        self._cs.plot_cs(fig = fig, ax= ax, linked_arrays={"DEM": self.dem})
        self.dem.plotted = old_plotted

        return fig, ax

    def plot_cs_min_at_x0(self, figax:tuple[plt.Figure, plt.Axes]=None) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the cross section to compare.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        self._cs._plot_only_cs_min_at_x0(fig = fig, ax= ax, label = 'Cross-Section', style='solid', lw=2)

        return fig, ax

    def plot_cs_limited(self, figax:tuple[plt.Figure, plt.Axes]=None, tolerance:float = 1.) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the cross section to compare.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        old_plotted = self.dem.plotted
        self.dem.plotted = True
        self._cs.plot_cs(fig = fig, ax= ax, linked_arrays={"DEM": self.dem}, forceaspect=False)
        self.dem.plotted = old_plotted

        minz_cs = self._cs.zmin - tolerance
        maxz_cs = self._cs.zmax + tolerance

        # round to 0 decimals but keep as float
        minz_cs = round(minz_cs, 0)
        maxz_cs = math.ceil(maxz_cs)

        ax.set_ylim(minz_cs, maxz_cs)

        return fig, ax

    def plot_up_down_min_at_x0(self, figax:tuple[plt.Figure, plt.Axes]=None, n_iter = 2) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the cross section to compare.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        self._cs._plot_only_cs_min_at_x0(fig = fig, ax= ax, label = _('Cross-Section'), style='solid', lw=2)

        n_iter_up = n_iter
        n_iter_down = n_iter

        cs_up = self._cs.up
        while n_iter_up > 0 and cs_up is not None:
            if cs_up is self._cs:
                break
            cs_up._plot_only_cs_min_at_x0(fig = fig, ax= ax, style='dashed', label = _('Upstream {}').format(n_iter - n_iter_up + 1), col_ax='green', lw = n_iter_up, alpha= 1 - (n_iter - n_iter_up + 1 ) * 0.25)
            cs_up = cs_up.up
            n_iter_up -= 1

        cs_down = self._cs.down
        while n_iter_down > 0 and cs_down is not None:
            if cs_down is self._cs:
                break
            cs_down._plot_only_cs_min_at_x0(fig = fig, ax= ax, style='dashed', label = _('Downstream {}').format(n_iter - n_iter_down + 1), col_ax='blue', lw = n_iter_down + 1, alpha= 1 - (n_iter - n_iter_down + 1) * 0.25)
            cs_down = cs_down.down
            n_iter_down -= 1

        ax.legend(fontsize=6)

        return fig, ax

    def _complete_report(self, page:CSvsDEM_IndividualLayout):

        """
        Complete the report with the arrays and histograms.
        """
        useful = page.useful_part

        # Plot reference array
        key_fig = [('Maps_0-0', self.plot_position_around),
                   ('Maps_1-0', self.plot_position_grey),
                   ('Cross-Sections', self.plot_cs_limited),
                   ('DEM', self.plot_dem_around),
                   ('Comparison', self.plot_up_down_min_at_x0),
                   ]

        keys = page.keys
        for key, fig_routine in key_fig:
            if key in keys:

                rect = page.layout[key]

                fig, ax = fig_routine()

                # set size to fit the rectangle
                fig.set_size_inches(pt2inches(rect.width), pt2inches(rect.height))

                if 'Histogram' in key:
                    fig.tight_layout()

                # convert canvas to PNG and insert it into the PDF
                temp_file = NamedTemporaryFile(delete=False, suffix='.png')
                fig.savefig(temp_file, format='png', bbox_inches='tight', dpi=self._dpi)
                page._page.insert_image(page.layout[key], filename = temp_file.name)
                # delete the temporary file
                temp_file.delete = True
                temp_file.close()

                # Force to delete fig
                plt.close(fig)
            else:
                logging.warning(f"Key {key} not found in layout. Skipping plot.")

        key = 'Arrays_1-2'
        if key in keys:
            text, css = list_to_html(self._summary_text, font_size='8pt')
            page._page.insert_htmlbox(page.layout[key], text,
                                css=css)

    def create_report(self, output_file: str | Path = None) -> Path:
        """ Create a page report for the array difference. """

        from time import sleep
        if output_file is None:
            output_file = Path(f"array_difference_{self.index_cs}.pdf")

        if output_file.exists():
            logging.warning(f"Output file {output_file} already exists. It will be overwritten.")

        diff_left, diff_right = self.differences
        page = CSvsDEM_IndividualLayout(_("Group {} - Index {} - CS {} - Delta left {:.2f} - Delta right {:.2f}").format(self.index_group, self.index_cs, self._cs.myname, diff_left, diff_right))
        page.create_report()
        self._complete_report(page)
        page.save_report(output_file)
        sleep(0.2)  # Ensure the file is saved before returning

        return output_file


class CompareMultipleCSvsDEM:

    def __init__(self, cross_sections:crosssections | Path | str,
                 dem: WolfArray | str | Path,
                 laz_directory: Path | str = None,
                 support: Path | str | vector = None,
                 threshold_z: float = 0.5,
                 distance_threshold: float = 50.):
        """ Compare multiple cross-sections with a DEM.

        :param cross_sections: Cross-sections to compare. Can be a crosssections object or a path to a vector file (.vecz).
        :param dem: DEM to compare with. Can be a WolfArray object or a path to a raster file.
        :param laz_directory: Directory where the LAZ files are stored (Numpy-Wolf format).
        :param support: Support vector to sort the cross-sections along. Can be a path to a vector file (first vector in the first zone will be used) or a vector object.
        """

        if isinstance(support, (str, Path)):
            if not Path(support).exists():
                logging.error(f"The support file {support} does not exist. Centers will be used.")
                self._support = None
            support = Zones(support)
            self._support = support[(0,0)]  # get the first zone
        elif isinstance(support, vector):
            self._support = support
        else:
            self._support = None
            logging.warning("The support is not a valid file or vector. Centers will be used.")

        self._dpi = 600
        self.default_size_arrays = (10, 10)
        self._fontsize = 6

        if isinstance(dem, (str, Path)):
            dem = WolfArray(dem)

        assert isinstance(dem, WolfArray), "DEM must be a WolfArray instance."

        if isinstance(cross_sections, (str, Path)):
            cross_sections = crosssections(cross_sections, format='vecz', dirlaz=laz_directory)

        assert isinstance(cross_sections, crosssections), "Cross-sections must be a crosssections instance."

        if self._support is None:
            self._support = cross_sections.create_vector_from_centers()

        cross_sections.sort_along(self._support, 'support', downfirst=False)

        assert cross_sections.check_left_right_coherence() == 0, "Cross-sections are not coherent in left/right orientation."

        self._dirlaz = laz_directory
        self._cs = cross_sections

        if self._cs.dirlaz is None or self._cs.dirlaz != self._dirlaz:
            logging.info(f"Setting cross-sections directory for LAZ files to {self._dirlaz}")
            self._cs.dirlaz = self._dirlaz

        self.dem:WolfArray
        self.dem = dem
        self._rebinned_dem:WolfArray = None

        if self.dem.nbnotnull > 1_000_000:
            logging.warning("The DEM has more than 1 million valid cells. Plotting a rebin one.")
            self._rebinned_dem = WolfArray(mold=dem)
            self._rebinned_dem.rebin(10)
            self._rebinned_dem.mypal = dem.mypal

        self.subpages:dict[int, CSvsDEM] = {}

        self._pdf_path = None

        self._background = 'IGN'

        self._groups: list[list[dict['section_id':int, "x": float, "y": float, "diff_left": float, "diff_right": float, "s": float]]]
        self._groups = []

        self._threshold_z = threshold_z
        self._distance_threshold = distance_threshold

        self.find_differences(tolerance = self._threshold_z, distance_threshold = self._distance_threshold)

        logging.info(f"Number of groups of differences: {self.count_groups}")
        logging.info(f"Number of groups of differences greater than 3: {self.count_groups_greater_than(3)}")

    def find_differences(self, tolerance:float = 0.5, distance_threshold:float = 50.):
        """ Find differences between cross-sections and DEM.

        Store the differences in self._diffs as a list of lists of dictionaries with keys: section_id, x, y, diff_left, diff_right.

        We need to group the closest cross-sections that have differences.
        So, we start from the upstream cross-section and go downstream, grouping cross-sections which have differences and are close to each other (less than distance_threshold m apart).

        :param tolerance: Tolerance in meters to consider a difference. If the absolute difference between the cross-section and the DEM is greater than this value, it is considered a difference.
        """

        all_profiles = []

        loc_cs = self._cs.get_upstream()
        loc_profile = loc_cs['cs']

        while loc_profile.down is not loc_profile:

            diff_left  = abs(self.dem.get_value(loc_profile[0].x, loc_profile[0].y) - loc_profile[0].z)
            diff_right = abs(self.dem.get_value(loc_profile[-1].x, loc_profile[-1].y) - loc_profile[-1].z)

            if diff_left > tolerance or diff_right > tolerance:
                all_profiles.append({'profile': loc_profile, 'diff_left': diff_left, 'diff_right': diff_right})

            loc_profile = loc_profile.down

        diff_left  = abs(self.dem.get_value(loc_profile[0].x, loc_profile[0].y) - loc_profile[0].z)
        diff_right = abs(self.dem.get_value(loc_profile[-1].x, loc_profile[-1].y) - loc_profile[-1].z)

        if diff_left > tolerance or diff_right > tolerance:
            all_profiles.append({'profile': loc_profile, 'diff_left': diff_left, 'diff_right': diff_right})

        # grouped differences
        self._groups = []

        all_s = np.array([diff['profile'].s for diff in all_profiles])

        delta_s = all_s[1:] - all_s[:-1]

        # group are defined by a gap greater than distance_threshold
        group = np.where(delta_s > distance_threshold)[0]
        # add the last index
        group = np.append(group, len(all_profiles)-1)

        start = 0
        for g in group:
            new_group = all_profiles[start:g+1]
            self._groups.append(new_group)
            start = g+1

        self._sort_groups_by_inverse_deltaz()

        logging.info(f"Found {len(self._groups)} groups of differences on the left or right bank.")


    @property
    def count_groups(self) -> int:
        """ How many groups of differences are there? """
        return len(self._groups)

    @property
    def count_differences(self) -> int:
        """ Count total number of differences. """
        count = 0
        for group in self._groups:
            count += len(group)
        return count

    def count_groups_greater_than(self, threshold: int) -> int:
        """ How many groups of differences are greater than a given threshold? """
        count = 0
        for group in self._groups:
            if len(group) > threshold:
                count += 1
        return count

    def _diff_to_dict(self):
        """ Compile dict in list of lists to a  single dictionary """

        diff_dict = {}
        for group in self._groups:
            for sect in group:
                prof = sect['profile']
                # copy sect but exclude profile
                diff_dict[prof.myname] = {k: v for k, v in sect.items() if k != 'profile'}
        return diff_dict

    def _diff_to_dataframe(self):
        """ Compile dict in list of lists to a single pandas DataFrame.

        Dataframe columns: x, y, diff
        Dataframe index: profile
        """

        import pandas as pd

        rows_left = []
        rows_right = []
        for i_group, group in enumerate(self._groups):
            for sect in group:
                prof = sect['profile']

                diff_left = sect['diff_left']
                diff_right = sect['diff_right']

                if diff_left > self._threshold_z:
                    left_vert = prof[0]
                    row = {'profile': prof.myname, 'x': round(left_vert.x,2), 'y': round(left_vert.y,2), 'diff': round(diff_left,2), 'group':i_group +1}
                    rows_left.append(row)
                if diff_right > self._threshold_z:
                    right_vert = prof[-1]
                    row = {'profile': prof.myname, 'x': round(right_vert.x,2), 'y': round(right_vert.y,2), 'diff': round(diff_right,2), 'group':i_group +1}
                    rows_right.append(row)

        # Sort by diff descending
        rows_left = sorted(rows_left, key=lambda x: x['diff'], reverse=True)
        rows_right = sorted(rows_right, key=lambda x: x['diff'], reverse=True)

        return pd.DataFrame(rows_left[:min(10, len(rows_left))]), pd.DataFrame(rows_right[:min(10, len(rows_right))])

    @property
    def _all_XY_diff(self):
        """ Get all X and Y coordinates of the differences. """
        all_left = []
        all_right = []
        for group in self._groups:
            for item in group:
                prof = item["profile"]
                left_vert = prof[0]
                right_vert = prof[-1]

                diff_left = item["diff_left"]
                diff_right = item["diff_right"]
                if diff_left > self._threshold_z:
                    all_left.append((left_vert.x, left_vert.y, diff_left))
                if diff_right > self._threshold_z:
                    all_right.append((right_vert.x, right_vert.y, diff_right))

        return all_left, all_right

    @property
    def _all_differences_as_np(self) -> np.ndarray:
        """ Get all differences as a single array. """
        all_diffs = []
        for group in self._groups:
            for item in group:
                diff_left = item["diff_left"]
                diff_right = item["diff_right"]
                if diff_left > self._threshold_z:
                    all_diffs.append(item["diff_left"])
                if diff_right > self._threshold_z:
                    all_diffs.append(item["diff_right"])

        return np.array(all_diffs)

    @property
    def _all_left_differences_as_np(self) -> np.ndarray:
        """ Get all left differences as a single array. """
        all_diffs = []
        for group in self._groups:
            for item in group:
                diff_left = item["diff_left"]
                if diff_left > self._threshold_z:
                    all_diffs.append(item["diff_left"])

        return np.array(all_diffs)

    @property
    def _all_right_differences_as_np(self) -> np.ndarray:
        """ Get all right differences as a single array. """
        all_diffs = []
        for group in self._groups:
            for item in group:
                diff_right = item["diff_right"]
                if diff_right > self._threshold_z:
                    all_diffs.append(item["diff_right"])

        return np.array(all_diffs)

    def plot_histogram_differences(self, figax:tuple[plt.Figure, plt.Axes]=None, density = True, alpha = 0.3, **kwargs) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot histogram of all differences.
        """
        if figax is None:
            figax = plt.subplots(figsize=(8, 3))

        fig, ax = figax

        difference_data = self._all_differences_as_np
        ax.hist(difference_data, bins= min(100, int(len(difference_data)/4)), density=density, alpha=alpha, **kwargs)

        diff_left = self._all_left_differences_as_np
        diff_right = self._all_right_differences_as_np
        ax.hist(diff_left, bins= min(100, int(len(diff_left)/4)), density=density, alpha=alpha, color='green', label='Left bank', **kwargs)
        ax.hist(diff_right, bins= min(100, int(len(diff_right)/4)), density=density, alpha=alpha, color='orange', label='Right bank', **kwargs)

        # ax.set_xlabel("Value")
        # ax.set_ylabel("Frequency")

        # set font size of the labels
        ax.tick_params(axis='both', which='major', labelsize=6)
        for label in ax.get_xticklabels():
            label.set_fontsize(self._fontsize)
        for label in ax.get_yticklabels():
            label.set_fontsize(self._fontsize)
        # and gfor the label title
        ax.set_xlabel(ax.get_xlabel(), fontsize=self._fontsize)
        ax.set_ylabel(ax.get_ylabel(), fontsize=self._fontsize)

        # Add median and mean lines
        mean_val = np.mean(difference_data)
        median_val = np.median(difference_data)
        ax.axvline(mean_val, color='r', linestyle='dashed', linewidth=1, label=f'Mean: {mean_val:.2f}')
        ax.axvline(median_val, color='g', linestyle='dashed', linewidth=1, label=f'Median: {median_val:.2f}')

        ax.legend(fontsize=self._fontsize)

        return fig, ax

    def _read_differences_json(self, differences: Path | str) -> list[list[dict['section_id':int, "x": float, "y": float, "diff": float]]]:
        """ Differences file is a JSON file with the following structure:

        List of lists with: "section_id", "x", "y", "diff".

        List of lists because we want to store groups of cross-sections that are close to each other.
        """

        if not Path(differences).exists():
            logging.error(f"The differences file {differences} does not exist.")
            return []

        import json
        with open(differences, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    def plot_dem_with_background(self, figax:tuple[plt.Figure, plt.Axes]=None) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the reference array with a background.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        h = self.dem.get_header()
        width = h.nbx * h.dx
        height = h.nby * h.dy
        h.dx = width
        h.dy = height
        h.nbx = 1
        h.nby = 1

        new = WolfArray(srcheader=h)
        new.array.mask[:,:] = True

        if self._background.upper() == 'IGN' or self._background.upper() == 'NGI':

            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        IGN= True,
                                        cat = 'orthoimage_coverage',
                                        )
        elif self._background.upper() == 'WALONMAP':
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Walonmap= True,
                                        cat = 'IMAGERIE/ORTHO_2022_ETE',
                                        )
        else:
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Walonmap= False,
                                        )
        return fig, ax

    def plot_cartoweb(self, figax:tuple[plt.Figure, plt.Axes]=None) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the reference array with a background.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        h = self.dem.get_header()
        width = h.nbx * h.dx
        height = h.nby * h.dy
        h.dx = width
        h.dy = height
        h.nbx = 1
        h.nby = 1

        new = WolfArray(srcheader=h)
        new.array.mask[:,:] = True

        if self._background.upper() == 'IGN' or self._background.upper() == 'NGI':
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Cartoweb= True,
                                        cat = 'overlay',
                                        )
        else:
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Cartoweb= False,
                                        cat = 'overlay',
                                        )
        return fig, ax

    def plot_background_grey(self, figax:tuple[plt.Figure, plt.Axes]=None) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the reference array with a background.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        h = self.dem.get_header()
        width = h.nbx * h.dx
        height = h.nby * h.dy
        h.dx = width
        h.dy = height
        h.nbx = 1
        h.nby = 1

        new = WolfArray(srcheader=h)
        new.array.mask[:,:] = True

        if self._background.upper() == 'IGN' or self._background.upper() == 'NGI':
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Cartoweb= True,
                                        cat = 'topo_grey',
                                        )
        else:
            new.plot_matplotlib(figax=figax, figsize = self.default_size_arrays,
                                        first_mask_data=False, with_legend=False,
                                        update_palette= False,
                                        Cartoweb= False,
                                        cat = 'topo_grey',
                                        )
        return fig, ax

    def plot_dem(self, figax:tuple[plt.Figure, plt.Axes]=None, use_rebin_if_exists:bool=True) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the reference array.
        """
        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        if use_rebin_if_exists and self._rebinned_dem is not None:
            self._rebinned_dem.plot_matplotlib(figax=figax, figsize = self.default_size_arrays, first_mask_data=False, with_legend=True, update_palette= False)
        else:
            self.dem.plot_matplotlib(figax=figax, figsize = self.default_size_arrays, first_mask_data=False, with_legend=True, update_palette= False)

        return fig, ax

    def plot_XY(self, figax:tuple[plt.Figure, plt.Axes]=None,
                s:float=10, alpha:float=0.5,
                colorized_diff:bool=False,
                default_color=('blue', 'red'),
                which_ones:Literal['left', 'right', 'all'] = 'all') -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the XY of the differences.

        :param figax: Tuple of (Figure, Axes) to plot on. If None, a new figure and axes will be created.
        :param s: Size of the points.
        :param alpha: Alpha of the points.
        :param colorized_diff: If True, the points will be colored based on the difference value.
        :param default_color: If colorized_diff is False, the points will be colored with these colors for left and right.
        :param which_ones: Which points to plot. Can be 'left', 'right', or 'all'.
        """

        if figax is None:
            figax = plt.subplots()

        fig, ax = figax

        lefts, rights = self._all_XY_diff

        if colorized_diff:
            if which_ones == 'left' or which_ones == 'all':
                x,y,diff = zip(*lefts)
                ax.scatter(x, y, c=diff, cmap='bwr', s=s, alpha=alpha)

            if which_ones == 'right' or which_ones == 'all':
                x,y,diff = zip(*rights)
                ax.scatter(x, y, c=diff, cmap='bwr', s=s, alpha=alpha)
        elif default_color is not None:
            left_color, right_color = default_color

            if which_ones == 'left' or which_ones == 'all':
                x,y,_ = zip(*lefts)
                ax.scatter(x, y, color=left_color, s=s, alpha=alpha)
            if which_ones == 'right' or which_ones == 'all':
                x,y,_ = zip(*rights)
                ax.scatter(x, y, color=right_color, s=s, alpha=alpha)
        else:
            if which_ones == 'left' or which_ones == 'all':
                x,y,_ = zip(*lefts)
                ax.scatter(x, y, color='blue', s=s, alpha=alpha)
            if which_ones == 'right' or which_ones == 'all':
                x,y,_ = zip(*rights)
                ax.scatter(x, y, color='red', s=s, alpha=alpha)

        ax.set_aspect('equal', 'box')
        fig.tight_layout()

        return fig, ax

    def plot_mainpage_map(self) -> tuple[plt.Figure, plt.Axes]:
        """ Plot the main page map with all differences. """

        fig, ax = self.plot_background_grey()

        self.plot_XY(figax=(fig, ax), colorized_diff=True)

        return fig, ax

    def _summary_dem(self) -> list:
        """ Summary of the DEM. """

        return [
            f"Number of cells: {self.dem.nbnotnull}",
            f"Resolution (m): {self.dem.dx} x {self.dem.dy}",
            f"Extent: ({self.dem.origx}, {self.dem.origy}) - ({self.dem.origx + self.dem.nbx * self.dem.dx}, {self.dem.origy + self.dem.nby * self.dem.dy})",
            f"Width x Height (m): {self.dem.nbx * self.dem.dx} x {self.dem.nby * self.dem.dy}",
        ]

    def _summary_differences(self) -> list:
        """ Summary of the differences. """

        all_diff = self._all_differences_as_np
        all_diff_left = self._all_left_differences_as_np
        all_diff_right = self._all_right_differences_as_np
        return [
            f"Number of groups: {self.count_groups}",
            f"Number of cross-sections: {self.count_differences}",
            f"Median difference (m): {np.median(all_diff):.3f}",
            f"Min difference (m): {np.min(all_diff):.3f}",
            f"Max difference (m): {np.max(all_diff):.3f}",
            f"Left - Median difference (m): {np.median(all_diff_left):.3f}",
            f"Left - Min difference (m): {np.min(all_diff_left):.3f}",
            f"Left - Max difference (m): {np.max(all_diff_left):.3f}",
            f"Right - Median difference (m): {np.median(all_diff_right):.3f}",
            f"Right - Min difference (m): {np.min(all_diff_right):.3f}",
            f"Right - Max difference (m): {np.max(all_diff_right):.3f}",
        ]

    def __str__(self):


        ret = [_("Array information :")]
        ret.extend(self._summary_dem())
        ret.append("")
        ret.append(_("Differences information :"))
        ret.extend(self._summary_differences())

        return "\n".join(ret)

    def get_group_info(self, i_group:int) -> str:
        """ Get information about a specific group of differences. """
        if i_group < 0 or i_group >= self.count_groups:
            raise IndexError(f"Group index {i_group} out of range. There are {self.count_groups} groups.")

        group = self._groups[i_group]

        ret = [f"Group {i_group + 1} - Number of cross-sections: {len(group)}"]
        for sect in group:
            prof = sect['profile']
            diff_left = sect['diff_left']
            diff_right = sect['diff_right']
            ret.append(f"  - Cross-section {prof.myname}: Left difference = {diff_left:.3f} m, Right difference = {diff_right:.3f} m")

        return "\n".join(ret)

    def print_left_differences(self) -> str:
        """ Print all left differences. """

        ret = [_("Left bank differences:")]

        # Sort differences
        left_diffs = []
        for group in self._groups:
            for sect in group:
                prof = sect['profile']
                diff_left = sect['diff_left']
                if diff_left > self._threshold_z:
                    left_diffs.append((prof.myname, diff_left))
        left_diffs.sort(key=lambda x: x[1], reverse=True)
        for name, diff in left_diffs:
            ret.append(f"  - Cross-section {name}: {diff:.3f} m")

        return "\n".join(ret)

    def print_right_differences(self) -> str:
        """ Print all right differences. """

        ret = [_("Right bank differences:")]

        # Sort differences
        right_diffs = []
        for group in self._groups:
            for sect in group:
                prof = sect['profile']
                diff_right = sect['diff_right']
                if diff_right > self._threshold_z:
                    right_diffs.append((prof.myname, diff_right))
        right_diffs.sort(key=lambda x: x[1], reverse=True)
        for name, diff in right_diffs:
            ret.append(f"  - Cross-section {name}: {diff:.3f} m")

        return "\n".join(ret)

    def _complete_report_mainpage(self, page:CSvsDEM_MainLayout):
        """ Complete the report with the global summary and individual differences. """

        key_fig = [('Map', self.plot_mainpage_map),
                   ('Histogram', self.plot_histogram_differences),
                   ]

        key_list = [('Summary_0-0', self._summary_dem),
                   ('Summary_0-1', self._summary_differences),
                   ]

        df_left, df_right = self._diff_to_dataframe()
        key_table = [('Tables_0-0', df_left),
                   ('Tables_1-0', df_right),
                   ]

        legend_table = [('Legend Tables_0-0', _('Main Differences on Left extremity [m]')),
                        ('Legend Tables_1-0', _('Main Differences on Right extremity [m]')),]

        for key, legend in legend_table:
            if key in page.keys:
                rect = page.layout[key]
                text, css = single_line_to_html(legend, font_size='10pt')
                page._page.insert_htmlbox(rect, text, css=css)
            else:
                logging.warning(f"Key {key} not found in layout. Skipping legend text.")

        keys = page.keys
        for key, fig_routine in key_fig:
            if key in keys:

                rect = page.layout[key]

                fig, ax = fig_routine()

                # set size to fit the rectangle
                fig.set_size_inches(pt2inches(rect.width), pt2inches(rect.height))

                # convert canvas to PNG and insert it into the PDF
                temp_file = NamedTemporaryFile(delete=False, suffix='.png')
                fig.savefig(temp_file, format='png', bbox_inches='tight', dpi=self._dpi)
                page._page.insert_image(page.layout[key], filename=temp_file.name)
                # delete the temporary file
                temp_file.delete = True
                temp_file.close()

                # Force to delete fig
                plt.close(fig)
            else:
                logging.warning(f"Key {key} not found in layout. Skipping plot.")

        for key, txt_routine in key_list:
            if key in keys:
                rect = page.layout[key]
                text, css = list_to_html(txt_routine(), font_size='8pt')
                page._page.insert_htmlbox(rect, text, css=css)
            else:
                logging.warning(f"Key {key} not found in layout. Skipping text.")

        for key, df in key_table:
            if key in keys:
                rect = page.layout[key]
                text, css = dataframe_to_html(df, font_size='8pt')
                page._page.insert_htmlbox(rect, text, css=css)
            else:
                logging.warning(f"Key {key} not found in layout. Skipping text.")

    def _sort_groups_by_inverse_deltaz(self):
        """ Sort the groups by the maximum difference in descending order. """
        self._groups.sort(key=lambda group: max(max(item['diff_left'], item['diff_right']) for item in group), reverse=True)

    def _create_subpages(self):
        """ Complete the report with the individual sections. """

        for i_group, group in enumerate(self._groups):
            for i_sect, sect in enumerate(group):
                self.subpages[(i_group, i_sect)] = CSvsDEM(group,
                                                           i_sect,
                                                           self.dem,
                                                           title = _('Group n° {} - Section n° {}').format(i_group+1, sect['profile'].myname),
                                                           index_group= i_group + 1,
                                                           index_cs = i_sect + 1,
                                                           rebinned_dem=self._rebinned_dem)

    def create_report(self, output_file: str | Path = None,
                      append_subpages: bool = True,
                      nb_max_pages:int = -1) -> None:
        """ Create a page report for the array comparison. """

        if output_file is None:
            output_file = Path(f"compare_cs_dem_report.pdf")

        if output_file.exists():
            logging.warning(f"Output file {output_file} already exists. It will be overwritten.")

        mainpage = CSvsDEM_MainLayout(_("Comparison Report - Cross-Sections vs DEM"))
        mainpage.create_report()
        self._complete_report_mainpage(mainpage)

        if append_subpages:

            if nb_max_pages < 0:
                nb_max_pages = self.count_differences
            elif nb_max_pages > self.count_differences:
                logging.warning(f"Requested {nb_max_pages} differences, but only {self.count_differences} are available. Using all available differences.")
            elif nb_max_pages < self.count_differences:
                logging.info(f"Limiting to {nb_max_pages} differences.")

            # features_to_treat = [feature for feature in self._groups[:nb_max_pages]]


            self._create_subpages()

            with TemporaryDirectory() as temp_dir:

                all_pdfs = []

                nbpages = 0
                for idx, onepage in tqdm(self.subpages.items(), desc="Preparing individual difference reports", total=nb_max_pages):
                    if nbpages >= nb_max_pages:
                        break

                    all_pdfs.extend([onepage.create_report(Path(temp_dir) / f"temp_report_{idx[0]}_{idx[1]}.pdf")])
                    nbpages += 1

                for pdf_file in tqdm(all_pdfs, desc="Compiling PDFs"):
                    mainpage._doc.insert_file(pdf_file)

        # create a TOC
        mainpage._doc.set_toc(mainpage._doc.get_toc())

        mainpage.save_report(output_file)
        self._pdf_path = output_file

    @property
    def pdf_path(self) -> Path:
        """ Return the path to the generated PDF report. """
        if hasattr(self, '_pdf_path'):
            return self._pdf_path
        else:
            raise AttributeError("PDF path not set. Please create the report first.")

    def __getitem__(self, index: int | tuple):
        """ Get the group or a specific difference.
        """

        if isinstance(index, tuple):
            if len(index) != 2:
                raise IndexError("Tuple index must have exactly two elements: (group_index, difference_index).")
            group_index, diff_index = index
            if group_index < 0 or group_index >= self.count_groups:
                raise IndexError("Group index out of range.")
            group = self._groups[group_index]
            if diff_index < 0 or diff_index >= len(group):
                raise IndexError("Difference index out of range.")
            return group[diff_index]
        else:
            if index < 0 or index >= self.count_groups:
                raise IndexError("Group index out of range.")
            return self._groups[index]

class CompareCSvsDEM_wx(PDFViewer):

    def __init__(self, cross_sections: crosssections | Path | str,
                 dem: WolfArray | str | Path,
                 laz_directory: Path | str = None,
                 support: Path | str | vector = None,
                 threshold_z: float = 0.5,
                 distance_threshold: float = 50.0,
                 dpi:int=150,
                 nb_max_groups:int=-1,
                 **kwargs):
        """ Initialize the Report Viewer for comparison """

        super(CompareCSvsDEM_wx, self).__init__(None, **kwargs)

        use('agg')

        if isinstance(cross_sections, (str, Path)):
            if not Path(cross_sections).exists():
                logging.error(f"The cross-sections file {cross_sections} does not exist.")
                dlg = wx.MessageDialog(self,
                                       _("The cross-sections file does not exist."),
                                       _("Warning"),
                                       wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()
                return

        self._report = CompareMultipleCSvsDEM(cross_sections=cross_sections,
                                             dem=dem,
                                             laz_directory=laz_directory,
                                             support=support,
                                             threshold_z=threshold_z,
                                             distance_threshold=distance_threshold)

        pgbar = wx.ProgressDialog(_("Generating Report"),
                                   _("Please wait while the report is being generated..."),
                                   maximum=100,
                                   parent=self,
                                   style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)

        self._report._dpi = dpi
        self._report.create_report(nb_max_pages = nb_max_groups)

        pgbar.Update(100, _("Report generation completed."))
        pgbar.Destroy()

        # Load the PDF into the viewer
        if self._report.pdf_path is None:
            logging.error("No report created. Cannot load PDF.")
            return

        self.load_pdf(self._report.pdf_path)
        self.viewer.SetZoom(-1)  # Fit to width

        # Set the title of the frame
        self.SetTitle("Comparison of cross-sections and DEM - Report")

        self.Bind(wx.EVT_CLOSE, self.on_close)

        use('wxagg')

    def on_close(self, event):
        """ Handle the close event to clean up resources """
        self.viewer.pdfdoc.pdfdoc.close()
        self.Destroy()
