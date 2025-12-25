""" Create a report on a simple simulation from wolfgpu """

import sys
import wx
import os
import platform
from pathlib import Path
import logging
import numpy as np
from tempfile import NamedTemporaryFile
from datetime import datetime as dt

import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

import pymupdf as pdf
from wolfgpu.simple_simulation import SimpleSimulation, TimeStepStrategy, InfiltrationInterpolation
from wolfgpu.simple_simulation import InfiltrationChronology, SimulationDuration, SimulationDurationType
from wolfgpu.simple_simulation import boundary_condition_2D, BoundaryConditionsTypes

from .pdf import PDFViewer
from .common import cm2pts, A4_rect, rect_cm, cm2inches, list_to_html, list_to_html_aligned, get_rect_from_text
from ..wolf_array import WolfArray, header_wolf
from ..PyTranslate import _
from .. import __version__ as wolfhece_version
from wolfgpu.version import __version__ as wolfgpu_version

class SimpleSimGPU_Report():

    def __init__(self, sim:SimpleSimulation | Path | str, **kwargs):
        """ Initialize the Simple Simulation GPU Report Viewer """

        self._summary = {}
        self._doc = None

        if isinstance(sim, Path):
            try:
                self._sim = SimpleSimulation.load(sim)
            except Exception as e:
                logging.error(f"Failed to load simulation from path {sim}: {e}")
                self._sim = None
                self._summary['errors'] = e
                return
        elif isinstance(sim, str):
            try:
                self._sim = SimpleSimulation.load(Path(sim))
            except Exception as e:
                logging.error(f"Failed to load simulation from string path {sim}: {e}")
                self._sim = None
                self._summary['errors'] = e
                return
        elif not isinstance(sim, SimpleSimulation):
            try:
                self._sim = sim
            except Exception as e:
                logging.error(f"Failed to set simulation: {e}")
                self._sim = None
                self._summary['errors'] = e
                return
        else:
            logging.error("Invalid type for simulation. Must be SimpleSimulation, Path, or str.")
            return

        self._summary['warnings'] = self._summary_warnings()
        self._summary['errors'] = self._summary_errors()

    def _summary_versions(self):
        """ Find the versions of the simulation, wolfhece and the wolfgpu package """
        import json

        sim = self._sim

        with open(sim.path / "parameters.json","r") as pfile:
            data = json.loads(pfile.read())
            spec_version = data["spec_version"]

        group_title = "Versions"
        text = [f"Simulation : {spec_version}",
                f"Wolfhece : {wolfhece_version}",
                f"Wolfgpu : {wolfgpu_version}",
                f"Python : {sys.version.split()[0]}",
                f"Operating System: {os.name}"
                ]

        return group_title, text

    def _summary_spatial_extent(self):
        """ Return the summary of the spatial extent of the simulation """
        sim = self._sim

        group_title = "Spatial Extent"
        text = [f"Lower-left corner [m LBT72]  : ({sim.param_base_coord_ll_x}, {sim.param_base_coord_ll_y})",
                f"Upper-right corner [m LBT72] : ({sim.param_base_coord_ll_x + sim.param_dx * sim.param_nx}, {sim.param_base_coord_ll_y + sim.param_dy * sim.param_ny})",
                f"Resolution [m] : ({sim.param_dx}, {sim.param_dy}) - {sim.param_dx * sim.param_dy} [m²]",
                f"Total Area : {sim.param_dx * sim.param_dy * np.count_nonzero(sim.nap == 1)} [m²] - {sim.param_dx * sim.param_dy * np.count_nonzero(sim.nap == 1) /1e6} [km²]",
                ]

        return group_title, text

    def _summary_number_of_cells(self):
        """ Return the summary of the number of cells in the simulation """
        sim = self._sim

        group_title = "Number of Cells"
        text = [f"X \u2192: {sim.param_nx}",
                f"Y \u2191: {sim.param_ny}",
                f"Total in NAP: {np.count_nonzero(sim.nap == 1)}",
                f"Total in Bathymetry: {np.count_nonzero(sim.bathymetry != 99999.)}",
                ]


        return group_title, text

    def _summary_time_evolution(self):
        """ Return the summary of the time evolution of the simulation """
        sim = self._sim

        group_title = "Time Evolution"
        text = []
        if sim.param_runge_kutta == 1.:
            text.append("Euler explicit 1st order scheme")
        elif sim.param_runge_kutta == 0.5:
            text.append("Runge-Kutta 2nd order scheme (RK22)")
        else:
            text.append(f"Runge-Kutta 1st order scheme (RK21) - {sim.param_runge_kutta} times predictor")

        if sim.param_timestep_strategy == TimeStepStrategy.FIXED_TIME_STEP:
            text.append(f"Fixed time step: {sim.param_timestep} seconds")
        elif sim.param_timestep_strategy == TimeStepStrategy.OPTIMIZED_TIME_STEP:
            text.append("Variable time step")
            text.append(f"Courant-Friedrichs-Lewy condition: {sim.param_courant}")

        text.append(f"Simulation duration: {sim.param_duration}")

        return group_title, text

    def _summary_boundary_conditions(self):
        """ Return the summary of the boundary conditions of the simulation """
        sim = self._sim

        group_title = "Boundary Conditions"
        text = [f"Count: {len(sim.boundary_condition)}"]

        bc_set = {}
        for bc in sim.boundary_condition:
            if bc.ntype not in bc_set:
                bc_set[bc.ntype] = 0
            bc_set[bc.ntype] += 1

        for bc_type, count in bc_set.items():
            if count > 0:
                text.append(f"{count} {bc_type.name}")

        if BoundaryConditionsTypes.FROUDE_NORMAL in bc_set:
            if sim.param_froude_bc_limit_tolerance == 1.0:
                text.append("Froude tolerance is set to 1.0, which can lead to supercritical flow.")
            elif sim.param_froude_bc_limit_tolerance < 1.0:
                text.append(f"Froude tolerance is set to {sim.param_froude_bc_limit_tolerance}, which is a BAD practice.")
            else:
                text.append(f"Froude tolerance is set to {sim.param_froude_bc_limit_tolerance}, which is a GOOD practice.")

        return group_title, text

    def _summary_infiltration(self):
        """ Return the summary of the infiltration conditions of the simulation """
        sim = self._sim

        group_title = "Infiltration Conditions"
        text = []

        if len(sim.infiltrations_chronology) == 0:
            text.append("No infiltration conditions defined.")
            return group_title, text

        text.append(f"Count: {len(sim.infiltrations_chronology)}")
        text.append(f"Interpolation method: {sim.param_infiltration_lerp.name}")

        text.append(f"Rows - number of time positions: {len(sim.infiltrations_chronology)}")
        text.append(f"Columns - number of infiltration zones: {len(sim.infiltrations_chronology[0][1])}")
        text.append(f"Starting time [s]: {sim.infiltrations_chronology[0][0]}")
        text.append(f"Ending time [s]: {sim.infiltrations_chronology[-1][0]}")
        text.append(f"Ending time [hour]: {sim.infiltrations_chronology[-1][0] / 3600.}")

        nb_mat = np.max(sim.infiltration_zones)
        if nb_mat != len(sim.infiltrations_chronology[0][1]):
            text.append('PROBLEM: The number of infiltration zones in the chronology does not match the number of zones in the simulation.')

        # Count the cells for each infiltration zone
        nb_cells = np.bincount(sim.infiltration_zones[sim.infiltration_zones != 0], minlength=nb_mat + 1)
        # text.append("Number of cells per infiltration zone:")
        for i in range(1, nb_mat + 1):
            text.append(f"Zone {i}: {nb_cells[i]} cells")

        return group_title, text

    def _figure_infiltration(self):
        """ Add the infiltration image to the PDF report """

        sim = self._sim
        fig, ax = sim.plot_infiltration(toshow= False)
        # set font size
        ax.tick_params(axis='both', which='major', labelsize=6)
        for label in ax.get_xticklabels():
            label.set_fontsize(6)
        for label in ax.get_yticklabels():
            label.set_fontsize(6)
        # and gfor the label title
        ax.set_xlabel(ax.get_xlabel(), fontsize=8)
        ax.set_ylabel(ax.get_ylabel(), fontsize=8)
        # and for the legend
        for label in ax.get_legend().get_texts():
            label.set_fontsize(6)
        # remove the titla
        ax.set_title('')
        fig.suptitle('')

        fig.set_size_inches(8, 6)
        fig.tight_layout()

        ax.set_ylabel('Total Q\n[$m^3/s$]')

        return fig

    def _summary_bathymetry(self):
        """ Return the summary of the bathymetry of the simulation """
        sim = self._sim

        group_title = "Bathymetry"
        text = []

        if sim.bathymetry is None:
            text.append("No bathymetry defined.")
            return group_title, text

        text.append(f"NoData value: {sim.bathymetry[0, 0]}")
        if sim.bathymetry[0, 0] != 99999.:
            text.append("Nodata value is not 99999. It is preferable to use this value.")

        np_bath = np.count_nonzero(sim.bathymetry[sim.bathymetry != sim.bathymetry[0, 0]])
        np_nap = np.count_nonzero(sim.nap[sim.nap == 1])
        text.append(f"Number of cells in bathymetry: {np.count_nonzero(sim.bathymetry[sim.bathymetry != sim.bathymetry[0,0]])}")
        if np_nap != np_bath:
            text.append(f"Number of cells in NAP: {np_nap} is not equal to the number of cells in the bathymetry.")
        text.append(f"Minimum bathymetry value: {np.min(sim.bathymetry[sim.bathymetry != 99999.]):.3f} m")
        text.append(f"Maximum bathymetry value: {np.max(sim.bathymetry[sim.bathymetry != 99999.]):.3f} m")

        return group_title, text

    def _summary_initial_conditions(self):
        """ Return the summary of the initial conditions of the simulation """
        sim = self._sim

        group_title = "Initial Conditions"
        text = []

        max_h = np.max(sim.h)
        max_qx = np.max(np.abs(sim.qx))
        max_qy = np.max(np.abs(sim.qy))

        if max_h == 0.:
            text.append("No initial conditions defined. All cells are set to 0.")
            if max_qx != 0. or max_qy != 0.:
                text.append("Warning: Initial conditions for qx and qy are not zero, which is unusual.")
        else:
            text.append(f"Maximum water depth: {max_h} m")
            text.append(f"Number of wetted cells: {np.count_nonzero(sim.h > 0.)}")
            text.append(f"Maximum |qx|: {max_qx} m^2/s")
            text.append(f"Maximum |qy|: {max_qy} m^2/s")

        return group_title, text

    def _figure_histogram_waterdepth(self):
        """ Add the histogram of bathymetry to the PDF report """
        sim = self._sim
        # Plot the histogram of waterdepth adn add it to the PDF
        fig, ax = plt.subplots(figsize=(8, 6))
        # Plot the histogram of water depth

        h_min = np.min(sim.h[sim.nap == 1])
        h_max = np.max(sim.h[sim.nap == 1])

        if h_max > h_min:
            ax.hist(sim.h[sim.h > 0.], bins=100, density=True)
            ax.set_xlim(0, h_max)  # Set xlim to 110% of max value
        ax.set_xlabel('Water Depth [m]')
        ax.set_ylabel('Frequency')

        # set font size of the labels
        ax.tick_params(axis='both', which='major', labelsize=6)
        for label in ax.get_xticklabels():
            label.set_fontsize(6)
        for label in ax.get_yticklabels():
            label.set_fontsize(6)
        # and gfor the label title
        ax.set_xlabel(ax.get_xlabel(), fontsize=8)
        ax.set_ylabel(ax.get_ylabel(), fontsize=8)

        fig.tight_layout()

        return fig

    def _figure_histogram_manning(self):
        """ Add the histogram of bathymetry to the PDF report """
        sim = self._sim
        # Plot the histogram of waterdepth adn add it to the PDF
        fig, ax = plt.subplots(figsize=(8, 6))
        # set font size
        ax.hist(sim.manning[sim.nap == 1], bins=100, density = True)
        # ax.set_title('Histogram of Manning Coefficient')
        ax.set_xlabel('Manning [$\\frac {s} {m^{1/3}} $]')
        ax.set_xlim(0, np.max(sim.manning[sim.nap == 1]) * 1.1)  # Set xlim to 110% of max value
        ax.set_ylabel('Frequency')

        # set font size of the labels
        ax.tick_params(axis='both', which='major', labelsize=6)
        for label in ax.get_xticklabels():
            label.set_fontsize(6)
        for label in ax.get_yticklabels():
            label.set_fontsize(6)
        # and gfor the label title
        ax.set_xlabel(ax.get_xlabel(), fontsize=8)
        ax.set_ylabel(ax.get_ylabel(), fontsize=8)

        fig.tight_layout()

        return fig

    def _summary_bridge(self):
        """ Return the summary of the bridge conditions of the simulation """
        sim = self._sim

        group_title = "Bridge"
        text = []

        if not sim.has_bridge():
            text.append("No bridge defined.")
            return group_title, text

        text.append("Bridge defined.")
        if sim.bridge_roof is not None:
            text.append(f"Number of cells: {np.count_nonzero(sim.bridge_roof != 99999.)}")
            text.append(f"Minimum bridge roof value: {np.min(sim.bridge_roof[sim.bridge_roof != 99999.]):.3f} m")
            text.append(f"Maximum bridge roof value: {np.max(sim.bridge_roof[sim.bridge_roof != 99999.]):.3f} m")
        else:
            text.append("No bridge roof defined.")

        return group_title, text

    def _summary_warnings(self):
        """ Return the summary of the warnings of the simulation """
        sim = self._sim

        group_title = "Warnings"
        text = []

        mann = np.unique(sim.manning[sim.nap == 1])

        if len(mann) == 0:
            text.append("No Manning coefficient defined.")
        elif len(mann) == 1 and mann[0] == 0.:
            text.append("No Manning coefficient defined. All cells are set to 0.")
        elif len(mann) == 1 and mann[0] < 0.:
            text.append(f"Warning: Manning coefficient is set to {mann[0]:.4f} which is negative. This is not a valid value.")
        elif len(mann) == 1 and mann[0] > 0.:
            text.append(f"Manning coefficient is set to {mann[0]:.4f} which is a valid value BUT uniform.")

        h = np.unique(sim.h[sim.nap == 1])
        if len(h) == 0:
            text.append("No water depth defined. All cells are set to 0.")
        elif len(h) == 1 and h[0] == 0.:
            text.append("No water depth defined. All cells are set to 0.")
        elif len(h) == 1 and h[0] < 0.:
            text.append(f"Warning: Water depth is set to {h[0]:.2f} which is negative. This is not a valid value.")
        elif (len(h) == 1 and h[0] > 0.) or (len(h) == 2 and h[0] == 0. and h[1] > 0.):
            text.append(f"Water depth is set to {h[0]:.4f} which is a valid value BUT uniform.")

        wsl = np.unique(sim.h[sim.h > 0.] + sim.bathymetry[sim.h >0.])
        if len(wsl) == 1 and h[0] > 0.:
            text.append(f"Water surface level is set to {wsl[0]:.2f} which is a valid value BUT uniform.")

        qx = np.unique(sim.qx[sim.nap == 1])
        if len(qx) == 0:
            text.append("No initial conditions for qx defined. All cells are set to 0.")
        elif len(qx) == 1 and qx[0] == 0.:
            text.append("No initial conditions for qx defined. All cells are set to 0.")
        elif len(qx) == 1 and qx[0] < 0.:
            text.append(f"Warning: Initial conditions for qx is set to {qx[0]:.2f} which is negative. This is not a valid value.")
        elif len(qx) == 1 and qx[0] > 0.:
            text.append(f"Initial conditions for qx is set to {qx[0]:.2f} which is a valid value BUT uniform.")

        qy = np.unique(sim.qy[sim.nap == 1])
        if len(qy) == 0:
            text.append("No initial conditions for qy defined. All cells are set to 0.")
        elif len(qy) == 1 and qy[0] == 0.:
            text.append("No initial conditions for qy defined. All cells are set to 0.")
        elif len(qy) == 1 and qy[0] < 0.:
            text.append(f"Warning: Initial conditions for qy is set to {qy[0]:.2f} which is negative. This is not a valid value.")
        elif len(qy) == 1 and qy[0] > 0.:
            text.append(f"Initial conditions for qy is set to {qy[0]:.2f} which is a valid value BUT uniform.")

        # test the presence of simul_gpu_results directory
        if not (sim.path / "simul_gpu_results").exists():
            text.append("No 'simul_gpu_results' directory found. The simulation may not have been run or the results are missing.")
        elif not (sim.path / "simul_gpu_results" / "metadata.json").exists():
            text.append("No 'metadata.json' file found in 'simul_gpu_results'. The simulation may not have been run or the results are missing.")
        else:
            # Check the date of the metadata file compared to the parameters.json file
            metadata_file = sim.path / "simul_gpu_results" / "metadata.json"
            parameters_file = sim.path / "parameters.json"
            metadata_date = dt.fromtimestamp(metadata_file.stat().st_mtime)
            parameters_date = dt.fromtimestamp(parameters_file.stat().st_mtime)
            if metadata_date < parameters_date:
                text.append("Warning: The 'metadata.json' file is older than the 'parameters.json' file. The simulation may not have been run with the latest parameters.")

        warn = sim.check_warnings()
        if warn is not None:
            text.append(f"Count: {len(warn)}")
            for w in warn:
                text.append(f"- {w}")
        else:
            text.append("No warnings from wolfgpu.")

        return group_title, text

    def _summary_errors(self):
        """ Return the summary of the errors of the simulation """
        sim = self._sim

        group_title = "Errors"
        text = []

        err = sim.check_errors()
        if err is not None:
            text.append(f"Count: {len(err)}")
            for e in err:
                text.append(f"- {e}")
        else:
            text.append("No errors from wolfgpu.")

        return group_title, text

    def _figure_model_extent(self):
        """ Get the bathymetry figure for the PDF report """
        h = header_wolf()
        h.shape = (self._sim.param_nx, self._sim.param_ny)
        h.set_resolution(self._sim.param_dx, self._sim.param_dy)
        h.set_origin(self._sim.param_base_coord_ll_x, self._sim.param_base_coord_ll_y)

        bath = self._sim.bathymetry
        bat_wa = WolfArray(srcheader=h, np_source=bath, nullvalue= 99999.)

        fig, ax, im = bat_wa.plot_matplotlib(getdata_im= True,
                                             Walonmap= True, cat= 'IMAGERIE/ORTHO_2021',
                                             with_legend= False)

        # set font size of the labels
        ax.tick_params(axis='both', which='major', labelsize=6)
        for label in ax.get_xticklabels():
            label.set_fontsize(6)
        for label in ax.get_yticklabels():
            label.set_fontsize(6)

        return fig

    def summary(self):
        """ Create a dictionnary with the summary of the simulation """

        self._summary['versions'] = self._summary_versions()
        self._summary['spatial_extent'] = self._summary_spatial_extent()
        self._summary['number_of_cells'] = self._summary_number_of_cells()
        self._summary['time_evolution'] = self._summary_time_evolution()
        self._summary['boundary_conditions'] = self._summary_boundary_conditions()
        self._summary['infiltration'] = self._summary_infiltration()
        self._summary['bathymetry'] = self._summary_bathymetry()
        self._summary['initial_conditions'] = self._summary_initial_conditions()
        self._summary['bridge'] = self._summary_bridge()
        self._summary['warnings'] = self._summary_warnings()
        self._summary['errors'] = self._summary_errors()

        return self._summary

    def _layout(self):
        """ Set the layout of the PDF report.

        Each group has a rectangle of 9cm width and 2.5 cm height.

        Title rect is 16 cm width and 1.5 cm height.
        Version rect is 16 cm width and 1 cm height.
        Logo is at the top-right corner of the page (2 cm width x 3 cm height).
        """

        summary = self.summary()

        LEFT_MARGIN = 1  # cm
        TOP_MARGIN = 0.5  # cm
        PADDING = 0.5  # cm

        WIDTH_TITLE = 16  # cm
        HEIGHT_TITLE = 1.5  # cm

        WIDTH_VERSIONS = 16  # cm
        HEIGHT_VERSIONS = .5 # cm

        X_LOGO = 18.5  # Logo starts after the title and versions
        WIDTH_LOGO = 1.5  # cm
        HEIGHT_LOGO = 1.5  # cm

        WIDTH_SUMMARY = 9  # cm
        HEIGHT_SUMMARY = 2.5  # cm

        KEYS_LEFT_COL = ["warnings", "spatial_extent", "number_of_cells",
                         "time_evolution", "boundary_conditions",
                         "infiltration", "bathymetry",
                         "initial_conditions"]
        KEYS_RIGHT_COL = ["errors", "bridge"]

        layout = {}

        layout['title'] = rect_cm(LEFT_MARGIN, TOP_MARGIN, WIDTH_TITLE, HEIGHT_TITLE)
        layout['versions'] = rect_cm(LEFT_MARGIN, TOP_MARGIN + HEIGHT_TITLE + PADDING, WIDTH_VERSIONS, HEIGHT_VERSIONS)
        layout['logo'] = rect_cm(X_LOGO, TOP_MARGIN, WIDTH_LOGO, HEIGHT_LOGO)

        TOP_SUMMARY = TOP_MARGIN + HEIGHT_TITLE + HEIGHT_VERSIONS + 2 * PADDING  # 1.5 cm for title, 1 cm for versions, 0.5 cm padding

        y_summary_left  = TOP_SUMMARY
        y_summary_right = y_summary_left  # 6 groups in the left column

        X_SUMMARY_RIGHT = LEFT_MARGIN + WIDTH_SUMMARY + 2 * PADDING  # Right column starts after the left column

        HEIGHT_MAIN_FIGURE = 3 * HEIGHT_SUMMARY + 2 * PADDING  # cm
        WIDTH_MAIN_FIGURE = WIDTH_SUMMARY #/ 2  # cm

        # y_summary_right += 1.5 * HEIGHT_SUMMARY + 1.5* PADDING  # Move the right column down for the histogram

        for key, text in summary.items():
            if key in KEYS_LEFT_COL:
                layout[key] = rect_cm(LEFT_MARGIN, y_summary_left, WIDTH_SUMMARY, HEIGHT_SUMMARY)
                y_summary_left += HEIGHT_SUMMARY + PADDING
            elif key in KEYS_RIGHT_COL:
                layout[key] = rect_cm(X_SUMMARY_RIGHT, y_summary_right, WIDTH_SUMMARY, HEIGHT_SUMMARY)
                y_summary_right += HEIGHT_SUMMARY + PADDING

        layout['main figure'] = rect_cm(X_SUMMARY_RIGHT, y_summary_right, WIDTH_MAIN_FIGURE, HEIGHT_MAIN_FIGURE)  # Main figure at the bottom
        # layout['manning figure'] = rect_cm(X_SUMMARY_RIGHT + WIDTH_MAIN_FIGURE + PADDING, y_summary_right, WIDTH_MAIN_FIGURE, HEIGHT_MAIN_FIGURE)  # Main figure at the bottom
        y_summary_right += HEIGHT_MAIN_FIGURE + PADDING  # Move the right column down for the main figure

        layout['hydrograms'] = rect_cm(X_SUMMARY_RIGHT, y_summary_right, WIDTH_SUMMARY, 1.5 * HEIGHT_SUMMARY + PADDING)  # Hydrograms at the bottom right
        y_summary_right += 1.5 * HEIGHT_SUMMARY + 1.5 * PADDING  # Move the right column down for the hydrograms

        layout['histogram_waterdepth'] = rect_cm(X_SUMMARY_RIGHT, y_summary_right, WIDTH_SUMMARY /2., 1.5 * HEIGHT_SUMMARY + PADDING)  # Histogram below hydrograms
        layout['histogram_manning'] = rect_cm(X_SUMMARY_RIGHT + WIDTH_SUMMARY/2. + PADDING, y_summary_right, WIDTH_SUMMARY /2., 1.5 * HEIGHT_SUMMARY + PADDING)  # Histogram below hydrograms

        layout['footer'] = rect_cm(LEFT_MARGIN, 28, 19, 1.2)  # Footer at the bottom

        return layout, summary

    def create_report(self):
        """ Create the PDF report for the Simple Simulation GPU """

        if not self._sim:
            logging.error("No simulation data available to create report.")
            return

        # Create a new PDF document
        self._doc = pdf.Document()

        # Add a page
        page = self._doc.new_page()

        layout, summary = self._layout()

        page.insert_htmlbox(layout['title'], f"<h1>GPU Summary - {self._sim.path.name}</h1>",
                                css='h1 {font-size:16pt; font-family:Helvetica; color:#333}')

        for key, text in summary.items():
            rect = layout[key]

            # Add a rectangle for the group
            page.draw_rect(rect, color=(0, 0, 0, .05), width=0.5)


            if key == "versions":
                try:
                    html, css = list_to_html_aligned(text[1], font_size="6pt", font_family="Helvetica")
                    spare_height, scale = page.insert_htmlbox(rect, html, css=css,
                                                              scale_low  = 0.1)

                    if spare_height < 0.:
                        logging.warning("Text overflow in versions box. Adjusting scale.")
                except:
                    logging.error("Failed to insert versions text. Using fallback method.")

            elif key == "infiltration":
                # Add the group title
                page.insert_text((rect.x0 + 1, rect.y0 + cm2pts(.05)), text[0],
                                fontsize=10, fontname="helv", fill=(0, 0, 0), fill_opacity=1.)

                text_left = [txt for txt in text[1] if not txt.startswith("Zone")]
                text_right = [txt for txt in text[1] if txt.startswith("Zone")]

                # Limit text_right to 6 elements max
                if len(text_right) > 6:
                    text_right = text_right[:6]
                    text_right.append("... (more zones)")

                html_left, css = list_to_html(text_left, font_size="8pt", font_family="Helvetica")
                html_right, css = list_to_html(text_right, font_size="8pt", font_family="Helvetica")

                rect_left = pdf.Rect(rect.x0, rect.y0, rect.x0 + rect.width / 2, rect.y1)
                rect_right = pdf.Rect(rect.x0 + rect.width / 2, rect.y0, rect.x1, rect.y1)
                spare_height, scale = page.insert_htmlbox(rect_left, html_left,
                                                            scale_low  = 0.1, css = css)
                if spare_height < 0.:
                    logging.warning("Text overflow in left infiltration box. Adjusting scale.")

                spare_height, scale = page.insert_htmlbox(rect_right, html_right,
                                                            scale_low  = 0.1, css = css)
                if spare_height < 0.:
                    logging.warning("Text overflow in right infiltration box. Adjusting scale.")

            elif key == "warnings" or key == "errors":
                # Add the group title
                if key == "warnings":
                    page.insert_text((rect.x0 + 1, rect.y0 + cm2pts(.05)), text[0],
                                    fontsize=10, fontname="helv", fill=(1, .55, 0), fill_opacity=1.)
                    if len(text[1]) > 1:
                        # draw rectangle in orange
                        page.draw_rect(rect, color=(1, .55, 0), width=2.0, fill = True, fill_opacity=1)
                else:
                    page.insert_text((rect.x0 + 1, rect.y0 + cm2pts(.05)), text[0],
                                    fontsize=10, fontname="helv", fill=(1, 0, 0), fill_opacity=1.)
                    if len(text[1]) > 1:
                        # draw rectangle in red
                        page.draw_rect(rect, color=(1, 0, 0), width=2.0, fill = True, fill_opacity=1)
                try:

                    html, css = list_to_html(text[1], font_size="8pt", font_family="Helvetica")
                    spare_height, scale = page.insert_htmlbox(rect, html,
                                                              scale_low  = 0.1, css = css)

                    if spare_height < 0.:
                        logging.warning("Text overflow in summary box. Adjusting scale.")
                except:
                    logging.error("Failed to insert text. Using fallback method.")

            else:
                # Add the group title
                page.insert_text((rect.x0 + 1, rect.y0 + cm2pts(.05)), text[0],
                                fontsize=10, fontname="helv", fill=(0, 0, 0), fill_opacity=1.)
                try:

                    html, css = list_to_html(text[1], font_size="8pt", font_family="Helvetica")
                    spare_height, scale = page.insert_htmlbox(rect, html,
                                                              scale_low  = 0.1, css = css)

                    if spare_height < 0.:
                        logging.warning("Text overflow in summary box. Adjusting scale.")
                except:
                    logging.error("Failed to insert text. Using fallback method.")

        # aded the Figures
        if 'main figure' in layout:

            rect = layout['main figure']

            fig = self._figure_model_extent()

            # set size to fit the rectangle
            fig.set_size_inches(rect.width / 72, rect.height / 72)

            # convert canvas to PNG and insert it into the PDF
            temp_file = NamedTemporaryFile(delete=False, suffix='.png')
            fig.savefig(temp_file, format='png', bbox_inches='tight', dpi=200)
            page.insert_image(layout['main figure'], filename = temp_file.name)
            # delete the temporary file
            temp_file.delete = True
            temp_file.close()

            # Force to delete fig
            plt.close(fig)

        if 'hydrograms' in layout:

            rect = layout['hydrograms']
            # Get the hydrograms figure from the simulation
            fig = self._figure_infiltration()
            # set size to fit the rectangle
            fig.set_size_inches(rect.width / 72, rect.height / 72)

            fig.tight_layout()
            # convert canvas to PNG and insert it into the PDF
            temp_file = NamedTemporaryFile(delete=False, suffix='.png')
            fig.savefig(temp_file, format='png', bbox_inches='tight', dpi=200)
            page.insert_image(layout['hydrograms'], filename=temp_file.name)
            # delete the temporary file
            temp_file.delete = True
            temp_file.close()

            #force to delete fig
            plt.close(fig)

        if 'histogram_waterdepth' in layout:

            rect = layout['histogram_waterdepth']
            # Get the histogram of bathymetry figure from the simulation
            fig = self._figure_histogram_waterdepth()
            # set size to fit the rectangle
            fig.set_size_inches(rect.width / 72, rect.height / 72)
            fig.tight_layout()
            # convert canvas to PNG and insert it into the PDF
            temp_file = NamedTemporaryFile(delete=False, suffix='.png')
            fig.savefig(temp_file, format='png', bbox_inches='tight', dpi=200)
            page.insert_image(layout['histogram_waterdepth'], filename=temp_file.name)
            # delete the temporary file
            temp_file.delete = True
            temp_file.close()

            # force to delete fig
            plt.close(fig)

        if 'histogram_manning' in layout:
            rect = layout['histogram_manning']
            # Get the histogram of Manning figure from the simulation
            fig = self._figure_histogram_manning()
            # set size to fit the rectangle
            fig.set_size_inches(rect.width / 72, rect.height / 72)
            fig.tight_layout()
            # convert canvas to PNG and insert it into the PDF
            temp_file = NamedTemporaryFile(delete=False, suffix='.png')
            fig.savefig(temp_file, format='png', bbox_inches='tight', dpi=200)
            page.insert_image(layout['histogram_manning'], filename=temp_file.name)
            # delete the temporary file
            temp_file.delete = True
            temp_file.close()

            # force to delete fig
            plt.close(fig)

        rect = layout['logo']
        # Add the logo to the top-right corner
        logo_path = Path(__file__).parent.parent / 'apps' / 'WolfPython2.png'
        if logo_path.exists():
            page.insert_image(rect, filename=str(logo_path), keep_proportion=True,
                              overlay=True)

        # Footer
        # ------
        # Insert the date and time of the report generation, the user and the PC name
        footer_rect = layout['footer']
        footer_text = f"<p>Report generated on {dt.now()} by {os.getlogin()} on {platform.uname().node} - {platform.uname().machine} - {platform.uname().release} - {platform.uname().version}</br> \
        This report does not guarantee the quality of the simulation and in no way commits the software developers.</p>"
        page.insert_htmlbox(footer_rect, footer_text,
                            css='p {font-size:10pt; font-family:Helvetica; color:#BEBEBE; align-text:center}',)


    def save_report(self, output_path: Path | str = None):
        """ Save the report to a PDF file """

        # Save the PDF to a file
        if output_path is None:
            output_path = self._sim.path.with_suffix('.pdf')

        try:
            self._doc.subset_fonts()
            self._doc.save(output_path, garbage=3, deflate=True)
            self._pdf_path = output_path
        except Exception as e:
            logging.error(f"Failed to save the report to {output_path}: {e}")
            logging.error("Please check if the file is already opened.")
            self._pdf_path = None
            return

    @property
    def pdf_path(self):
        """ Return the PDF document """
        return self._pdf_path


class SimpleSimGPU_Report_wx(PDFViewer):

    def __init__(self, sim:SimpleSimulation | Path | str, show:bool=False, **kwargs):
        """ Initialize the Simple Simulation GPU Report Viewer """

        mpl.use('Agg')  # Use a non-interactive backend for matplotlib

        super(SimpleSimGPU_Report_wx, self).__init__(None, **kwargs)

        self._report = SimpleSimGPU_Report(sim, **kwargs)

        if self._report._sim is None:
            logging.error("No simulation data available to create report.")
            dlg = wx.MessageDialog(self, "No simulation data available to create report.\n\nPlease check the errors in the logs.",
                                  "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        self._report.create_report()
        self._report.save_report()

        if self._report.pdf_path is None:
            logging.error("Failed to create the report PDF. Check the logs for more details.")
            return

        # Load the PDF into the viewer
        self.load_pdf(self._report.pdf_path)
        self.viewer.SetZoom(-1)  # Fit to width

        # Set the title of the frame
        self.SetTitle(f"Simple Simulation GPU Report - {self._report._sim.path}")

        self.Bind(wx.EVT_CLOSE, self.on_close)

        if show:
            self.Show()

        mpl.use('WxAgg')  # Reset matplotlib to use the WxAgg backend for other plots

    def on_close(self, event):
        """ Handle the close event of the frame """

        # close the pdf document
        self.viewer.pdfdoc.pdfdoc.close()
        self.Destroy()

class SimpleSimGPU_Reports_wx():
    """ List of Simple Simulations GPU """

    def __init__(self, dir_or_sims:list[SimpleSimulation | Path | str] | Path, show:bool=True, **kwargs):
        """ Initialize the Simple Simulations GPU Reports """

        pgbar = wx.ProgressDialog("Reporting simulations",
                                    "Creating report...",
                                    maximum=100,
                                    style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH)

        if isinstance(dir_or_sims, Path):
            # We assume it is a directory containing SimpleSimulation files
            if dir_or_sims.is_dir():
                sims = list(dir_or_sims.rglob('parameters.json'))
                self._sims = []
                for i, sim_dir in enumerate(sims):
                    pgbar.Update(int((i / len(sims)) * 100), f"Loading simulation {sim_dir.parent.name} ({i+1}/{len(sims)})")
                    self._sims.append(SimpleSimGPU_Report_wx(sim_dir.parent, **kwargs)) # Create a report for each simulation

                pgbar.Update(100, "All simulations loaded.")
                pgbar.Destroy()
                self._sims = [sim for sim in self._sims if sim._report._sim is not None]  # Filter out None values
            else:
                raise ValueError(f"The path {dir_or_sims} is not a directory.")
        elif isinstance(dir_or_sims, list):
            self._sims = []
            for sim in dir_or_sims:
                pgbar.Update(int((len(self._sims) / len(dir_or_sims)) * 100), f"Loading simulation {sim} ({len(self._sims) + 1}/{len(dir_or_sims)})")
                self._sims.append(SimpleSimGPU_Report_wx(sim, **kwargs))
            pgbar.Update(100, "All simulations loaded.")
            pgbar.Destroy()

            self._sims = [sim for sim in self._sims if sim._report._sim is not None]  # Filter out None values

        if show:
            for sim in self._sims:
                sim.Show()

class SimpleSimGPU_Report_Compare():
    """ Compare Multiple Simple Simulations GPU """

    _sims: list[SimpleSimulation]

    def __init__(self, sims:list[SimpleSimulation | Path | str] | Path, **kwargs):

        self._sims = []
        self._infos = []

        if isinstance(sims, Path):
            # We assume it is a a directory containing SimpleSimulation files

            if sims.is_dir():
                # Load all SimpleSimulation files in the directory
                for sim_file in sims.rglob('parameters.json'):
                    try:
                        self._sims.append(SimpleSimulation.load(sim_file.parent))
                    except Exception as e:
                        logging.error(f"Failed to load simulation from file {sim_file.parent}: {e}")
                        self._infos.append(f"Failed to load simulation from file {sim_file.parent}: {e}")
            else:
                logging.error(f"The path {sims} is not a directory.")
                self._infos.append(f"The path {sims} is not a directory.")
                return

        elif isinstance(sims, list):
            for sim in sims:
                if isinstance(sim, Path):
                    try:
                        self._sims.append(SimpleSimulation.load(sim))
                    except Exception as e:
                        logging.error(f"Failed to load simulation from path {sim}: {e}")
                        self._infos.append(f"Failed to load simulation from path {sim}: {e}")
                elif isinstance(sim, str):
                    try:
                        self._sims.append(SimpleSimulation.load(Path(sim)))
                    except Exception as e:
                        logging.error(f"Failed to load simulation from string {sim}: {e}")
                        self._infos.append(f"Failed to load simulation from string {sim}: {e}")
                elif not isinstance(sim, SimpleSimulation):
                    try:
                        self._sims.append(sim)
                    except Exception as e:
                        logging.error(f"Failed to append simulation {sim}: {e}")
                        self._infos.append(f"Failed to append simulation {sim}: {e}")
                else:
                    logging.error("Invalid type for simulation. Must be SimpleSimulation, Path, or str.")
                    self._infos.append("Invalid type for simulation. Must be SimpleSimulation, Path, or str.")
                    return
        else:
            logging.error("Invalid type for simulations. Must be Path, list of SimpleSimulation, Path or str.")
            self._infos.append("Invalid type for simulations. Must be Path, list of SimpleSimulation, Path or str.")
            return

        self._report = None

    def _summary_versions(self):
        """ Find the versions of the simulation, wolfhece and the wolfgpu package """

        group_title = "Versions"
        text = [f"Wolfhece : {wolfhece_version}",
                f"Wolfgpu : {wolfgpu_version}",
                f"Python : {sys.version.split()[0]}",
                f"Operating System: {os.name}"
                ]

        return group_title, text

    def _summary_array_shapes(self):
        """ Return the summary of the array shapes of the simulations """
        if not self._sims:
            logging.error("No simulations available to summarize.")
            return

        group_title = "Array Shapes"
        text = []

        sim_ref = self._sims[0]

        for idx, sim in enumerate(self._sims[1:]):
            try:
                text.append(f"{idx} - _bathymetry_: {sim_ref.bathymetry.shape == sim.bathymetry.shape}")
            except AttributeError:
                text.append(f"{idx} - _bathymetry_: error")
            try:
                text.append(f"{idx} - _manning_: {sim_ref.manning.shape == sim.manning.shape}")
            except AttributeError:
                text.append(f"{idx} - _manning_: error")
            try:
                text.append(f"{idx} - _infiltration_: {sim_ref.infiltration_zones.shape == sim.infiltration_zones.shape}")
            except AttributeError:
                text.append(f"{idx} - _infiltration_: error")
            try:
                text.append(f"{idx} - _h_: {sim_ref.h.shape == sim.h.shape}")
            except AttributeError:
                text.append(f"{idx} - _h_: error")
            try:
                text.append(f"{idx} - _qx_: {sim_ref.qx.shape == sim.qx.shape}")
            except AttributeError:
                text.append(f"{idx} - _qx_: error")
            try:
                text.append(f"{idx} - _qy_: {sim_ref.qy.shape == sim.qy.shape}")
            except AttributeError:
                text.append(f"{idx} - _qy_: error")
            try:
                text.append(f"{idx} - _nap_: {sim_ref.nap.shape == sim.nap.shape}")
            except AttributeError:
                text.append(f"{idx} - _nap_: error")

            if sim_ref.bridge_roof is not None and sim.bridge_roof is not None:
                try:
                    text.append(f"{idx} - _bridge roof_: {sim_ref.bridge_roof.shape == sim.bridge_roof.shape}")
                except AttributeError:
                    text.append(f"{idx} - _bridge roof_: error")

        return group_title, text

    def _summary_array_data(self):
        """ Return the summary of the array data of the simulations """
        if not self._sims:
            logging.error("No simulations available to summarize.")
            return

        group_title = "Array Data"
        text = []

        sim_ref = self._sims[0]

        for idx, sim in enumerate(self._sims[1:]):
            try:
                text.append(f"{idx} - _bathymetry_: {np.all(sim.bathymetry == sim.bathymetry)}")
            except AttributeError:
                text.append(f"{idx} - _bathymetry_: error")
            try:
                text.append(f"{idx} - _manning_: {np.all(sim_ref.manning == sim.manning)}")
            except AttributeError:
                text.append(f"{idx} - _manning_: error")
            try:
                text.append(f"{idx} - _infiltration_: {np.all(sim_ref.infiltration_zones == sim.infiltration_zones)}")
            except AttributeError:
                text.append(f"{idx} - _infiltration_: error")
            try:
                text.append(f"{idx} - _h_: {np.all(sim_ref.h == sim.h)}")
            except AttributeError:
                text.append(f"{idx} - _h_: error")
            try:
                text.append(f"{idx} - _qx_: {np.all(sim_ref.qx == sim.qx)}")
            except AttributeError:
                text.append(f"{idx} - _qx_: error")
            try:
                text.append(f"{idx} - _qy_: {np.all(sim_ref.qy == sim.qy)}")
            except AttributeError:
                text.append(f"{idx} - _qy_: error")
            try:
                text.append(f"{idx} - _nap_: {np.all(sim_ref.nap == sim.nap)}")
            except AttributeError:
                text.append(f"{idx} - _nap_: error")
            if sim_ref.bridge_roof is not None and sim.bridge_roof is not None:
                try:
                    text.append(f"{idx} - _bridge roof_: {np.all(sim_ref.bridge_roof == sim.bridge_roof)}")
                except AttributeError:
                    text.append(f"{idx} - _bridge roof_: error")

        return group_title, text

    def _summary_resolution(self):
        """ Return the summary of the resolution of the simulations """
        if not self._sims:
            logging.error("No simulations available to summarize.")
            return

        group_title = "Resolution"
        text = []

        sim_ref = self._sims[0]

        for idx, sim in enumerate(self._sims[1:]):
            try:
                text.append(f"{idx} - _base coord ll x_: {sim_ref.param_base_coord_ll_x == sim.param_base_coord_ll_x}")
            except AttributeError:
                text.append(f"{idx} - _base coord ll x_: error")
            try:
                text.append(f"{idx} - _base coord ll y_: {sim_ref.param_base_coord_ll_y == sim.param_base_coord_ll_y}")
            except AttributeError:
                text.append(f"{idx} - _base coord ll y_: error")
            try:
                text.append(f"{idx} - _dx_: {sim_ref.param_dx == sim.param_dx}")
            except AttributeError:
                text.append(f"{idx} - _dx_: error")
            try:
                text.append(f"{idx} - _dy_: {sim_ref.param_dy == sim.param_dy}")
            except AttributeError:
                text.append(f"{idx} - _dy_: error")
            try:
                text.append(f"{idx} - _nbx_: {sim_ref.param_nx == sim.param_nx}")
            except AttributeError:
                text.append(f"{idx} - _nbx_: error")
            try:
                text.append(f"{idx} - _nby_: {sim_ref.param_ny == sim.param_ny}")
            except AttributeError:
                text.append(f"{idx} - _nby_: error")

        return group_title, text

    def _summary_boundary_conditions(self):
        """ Return the summary of the boundary conditions of the simulations """
        if not self._sims:
            logging.error("No simulations available to summarize.")
            return

        group_title = "Boundary Conditions"
        text = []

        sim_ref = self._sims[0]

        for idx, sim in enumerate(self._sims[1:]):
            try:
                text.append(f"{idx} - _boundary conditions count_: {len(sim_ref.boundary_condition) == len(sim.boundary_condition)}")
            except AttributeError:
                text.append(f"{idx} - _boundary conditions count_: error")
            bc_set_ref = {bc.ntype: 0 for bc in sim_ref.boundary_condition}
            for bc in sim_ref.boundary_condition:
                bc_set_ref[bc.ntype] += 1

            bc_set = {bc.ntype: 0 for bc in sim.boundary_condition}
            for bc in sim.boundary_condition:
                bc_set[bc.ntype] += 1

            for bc_type, count in bc_set_ref.items():
                if count > 0:
                    try:
                        text.append(f"{idx} - _{count} {bc_type.name}_: {bc_set.get(bc_type, 0) == count}")
                    except AttributeError:
                        text.append(f"{idx} - _{count} {bc_type.name}_: error")

        return group_title, text

    def summary(self):
        """ Create a summary of the simulations """
        summary = {}
        summary['array_shapes'] = self._summary_array_shapes()
        summary['array_data'] = self._summary_array_data()
        summary['resolution'] = self._summary_resolution()
        summary['boundary_conditions'] = self._summary_boundary_conditions()

        return summary

    def _html_table_compare(self, key:str, text: list):
        """ Create an HTML table to compare the simulations

        One line for each parameter to compare.
        One column for each simulation.
        The first column is the parameter name.
        The first row is the simulation name.
        """

        html = "<table style='border-collapse: collapse; width: 100%;'>"
        html += "<tr><th>Parameter</th>"
        for sim in self._sims[1:]:
            html += f"<th>{sim.path.name}</th>"
        html += "</tr>"

        params = [current_text.split(': ', 1)[0].split(' - ')[-1] for current_text in text if '0 -' in current_text]

        for param in params:
            html += f"<tr><td>{param[1:-1]}</td>"

            # find the element in the text that contains the parameter name
            for current_text in text:
                if param in current_text:
                    value = current_text.split(': ', 1)[-1]
                    if value == 'True':
                        html += f'<td><span style="color: green; font-size: 14px;">\u2705</span></td>'
                    else:
                        html += f'<td><span style="color: red; font-size: 14px;">\u274C</span></td>'
            html += "</tr>"

        html += "</table>"

        # add basic css like border, padding, and font size, grid
        html = f"<div style='font-size: 8pt; font-family: Helvetica; border: 1px solid #ddd; padding: 5px; text-align: center'>{html}</div>"

        return html

    def _layout(self):
        """ Set the layout of the PDF report for the comparison."""

        summary = self.summary()

        LEFT_MARGIN = 1
        TOP_MARGIN = 0.5
        PADDING = 0.5

        WIDTH_TITLE = 16
        HEIGHT_TITLE = 1.5
        WIDTH_VERSIONS = 16
        HEIGHT_VERSIONS = 0.5
        X_LOGO = 18.5
        WIDTH_LOGO = 1.5
        HEIGHT_LOGO = 1.5

        WIDTH_SUMMARY = 19
        HEIGHT_SUMMARY = 5

        WIDTH_REFERENCE = 19
        HEIGHT_REFERENCE = 1.5

        layout = {}
        layout['title'] = rect_cm(LEFT_MARGIN, TOP_MARGIN, WIDTH_TITLE, HEIGHT_TITLE)
        layout['versions'] = rect_cm(LEFT_MARGIN, TOP_MARGIN + HEIGHT_TITLE + PADDING, WIDTH_VERSIONS, HEIGHT_VERSIONS)
        layout['reference'] = rect_cm(LEFT_MARGIN, TOP_MARGIN + HEIGHT_TITLE + HEIGHT_VERSIONS + 1.5*PADDING, WIDTH_REFERENCE, HEIGHT_REFERENCE)
        layout['logo'] = rect_cm(X_LOGO, TOP_MARGIN, WIDTH_LOGO, HEIGHT_LOGO)
        layout['footer'] = rect_cm(LEFT_MARGIN, 28, 19, 1.2)  # Footer at the bottom

        TOP_SUMMARY = TOP_MARGIN + HEIGHT_TITLE + HEIGHT_VERSIONS + HEIGHT_REFERENCE + 2 * PADDING  # 1.5 cm for title, 1 cm for versions, 0.5 cm padding
        y_summary = TOP_SUMMARY

        layout['resolution'] = rect_cm(LEFT_MARGIN, y_summary, WIDTH_SUMMARY, HEIGHT_SUMMARY *2/3)
        y_summary += HEIGHT_SUMMARY*2/3 + 2*PADDING

        layout['array_shapes'] = rect_cm(LEFT_MARGIN, y_summary, WIDTH_SUMMARY, HEIGHT_SUMMARY)
        y_summary += HEIGHT_SUMMARY + 2*PADDING

        layout['array_data'] = rect_cm(LEFT_MARGIN, y_summary, WIDTH_SUMMARY, HEIGHT_SUMMARY)
        y_summary += HEIGHT_SUMMARY + 2*PADDING

        layout['boundary_conditions'] = rect_cm(LEFT_MARGIN, y_summary, WIDTH_SUMMARY, HEIGHT_SUMMARY/2)
        y_summary += HEIGHT_SUMMARY/2 + 2*PADDING

        layout['informations'] = rect_cm(LEFT_MARGIN, y_summary, WIDTH_SUMMARY, HEIGHT_SUMMARY)
        y_summary += HEIGHT_SUMMARY + 2*PADDING

        return layout, summary

    def create_report(self):
        """ Create the PDF report for the comparison """
        if not self._sims:
            logging.error("No simulation data available to create report.")
            return

        # Create a new PDF document
        self._doc = pdf.Document()

        # Add a page
        page = self._doc.new_page()

        layout, summary = self._layout()

        page.insert_htmlbox(layout['title'], f"<h1>GPU - Parameters comparison report</h1>",
                                css='h1 {font-size:16pt; font-family:Helvetica; color:#333}')

        # versions
        group, summary_versions = self._summary_versions()
        rect = layout['versions']
        html, css = list_to_html_aligned(summary_versions, font_size="6pt", font_family="Helvetica")
        page.insert_htmlbox(rect, html, css=css, scale_low  = 0.1)

        # reference
        rect = layout['reference']
        if self._sims:
            ref_sim = self._sims[0]
            ref_text = [f"Reference Simulation: {ref_sim.path.name}",
                        f"Resolution (dx, dy): ({ref_sim.param_dx}, {ref_sim.param_dy})",
                        f"Number of Cells (nx, ny): ({ref_sim.param_nx}, {ref_sim.param_ny})",
                        # full path
                        f"Full Path: {ref_sim.path.resolve()}"]
            html, css = list_to_html_aligned(ref_text, font_size="8pt", font_family="Helvetica")
            page.insert_htmlbox(rect, html, css=css, scale_low  = 0.1)

        for key, text in summary.items():
            rect = layout[key]

            # Add a rectangle for the group
            page.draw_rect(rect, color=(0, 0, 0, .05), width=0.5)

            # Add the group title
            page.insert_text((rect.x0 + 1, rect.y0 - cm2pts(.2)), text[0],
                                fontsize=12, fontname="helv", fill=(0, 0, 0), fill_opacity=1.)

            # Create an HTML table for the comparison
            html = self._html_table_compare(text[0], text[1])
            spare_height, scale = page.insert_htmlbox(rect, html,
                                                        scale_low=0.1)

            if spare_height < 0.:
                logging.warning("Text overflow in summary box. Adjusting scale.")

        # logo
        rect = layout['logo']
        # Add the logo to the top-right corner
        logo_path = Path(__file__).parent.parent / 'apps' / 'WolfPython2.png'
        if logo_path.exists():
            page.insert_image(rect, filename=str(logo_path), keep_proportion=True,
                              overlay=True)
        # Footer
        # ------
        # Insert the date and time of the report generation, the user and the PC name
        footer_rect = layout['footer']
        footer_text = f"<p>Report generated on {dt.now()} by {os.getlogin()} on {platform.uname().node} - {platform.uname().machine} - {platform.uname().release} - {platform.uname().version}</br> \
        This report does not guarantee the quality of the simulation and in no way commits the software developers.</p>"
        page.insert_htmlbox(footer_rect, footer_text,
                            css='p {font-size:10pt; font-family:Helvetica; color:#BEBEBE; align-text:center}',)

        # Infos
        # -----

        rect = layout['informations']
        if self._infos:
            page.insert_text((rect.x0 + 1, rect.y0 + cm2pts(.05)), "Informations / Warnings / Errors",
                                fontsize=10, fontname="helv", fill=(0, 0, 0), fill_opacity=1.)
            html, css = list_to_html(self._infos, font_size="8pt", font_family="Helvetica")
            spare_height, scale = page.insert_htmlbox(rect, html, css=css,
                                                        scale_low=0.1)
            if spare_height < 0.:
                logging.warning("Text overflow in informations box. Adjusting scale.")


    def save_report(self, output_path: Path | str = None):
        """ Save the report to a PDF file """

        # Save the PDF to a file
        if output_path is None:
            output_path = Path("GPU_Comparison_Report.pdf")

        try:
            self._doc.subset_fonts()
            self._doc.save(output_path, garbage=3, deflate=True)
            self._pdf_path = output_path
        except Exception as e:
            logging.error(f"Failed to save the report to {output_path}: {e}")
            logging.error("Check if the file is already opened.")
            self._pdf_path = None
            return

    @property
    def pdf_path(self):
        """ Return the PDF document """
        return self._pdf_path

class SimpleSimGPU_Report_Compare_wx(PDFViewer):

    def __init__(self, sims:list[SimpleSimulation | Path | str], **kwargs):
        """ Initialize the Simple Simulation GPU Report Viewer for comparison """

        super(SimpleSimGPU_Report_Compare_wx, self).__init__(None, **kwargs)

        self._report = SimpleSimGPU_Report_Compare(sims, **kwargs)

        self._report.create_report()
        self._report.save_report()

        # Load the PDF into the viewer
        if self._report._pdf_path is None:
            logging.error("No report created. Cannot load PDF.")
            return

        self.load_pdf(self._report.pdf_path)
        self.viewer.SetZoom(-1)  # Fit to width

        # Set the title of the frame
        self.SetTitle("Simple Simulation GPU Comparison Report")

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        """ Handle the close event to clean up resources """
        self.viewer.pdfdoc.pdfdoc.close()
        self.Destroy()
