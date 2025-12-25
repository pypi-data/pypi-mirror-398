from enum import Enum
from PIL import Image
import numpy as np
from typing import Literal
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, ListedColormap, BoundaryNorm


from .PyTranslate import _
from .PyWMS import getLifeWatch
from .wolf_array import WolfArray, header_wolf, WOLF_ARRAY_FULL_INTEGER8, WOLF_ARRAY_FULL_INTEGER, wolfpalette


YEARS = [2006, 2010, 2015, 2018, 2019, 2020, 2021, 2022]
PIXEL_SIZE = 2 # in meters
MAP_LW = 'LW_ecotopes_lc_hr_raster'
MAX_PIXELS = 2048 # Maximum number of pixels in one direction (x or y)
class LifeWatch_Legend(Enum):
    """
    https://www.mdpi.com/2306-5729/8/1/13

    Map Class	Map Code	Related EAGLE Code	Percentage of Land Area [%] Based on 2018 Product
    Water	10	LCC-3	0.73
    Natural Material Surfaces with less than 10% vegetation	15	LCC-1_2	0.32
    Artificially sealed ground surface	20	LCC-1_1_1_3	5.75
    Building, specific structures and facilities	21	LCC-1_1_1_1 ||     LCC-1_1_1_2	1.99
    Herbaceous in rotation during the year (e.g., crops)	30	LCC-2_2	23.94
    Grassland with intensive management	35	LCC-2_2	27.57
    Grassland and scrub of biological interest	40	LCC-2_2	1.82
    Inundated grassland and scrub of biological interest	45	LCC-2_2 &     LCH-4_4_2	0.22
    Vegetation of recently disturbed area (e.g., clear cut)	48	LCC-2_2 &     LCH-3_8	2.64
    Coniferous trees (≥3 m)	50	LCC-2_1_1 &     LCH-3_1_1	11.24
    Small coniferous trees (<3 m)	51	LCC-2_1_2 &    LCH-3_1_1	0.40
    Broadleaved trees (≥3 m)	55	LCC-2_1_1 &    LCH-3_1_2	21.63
    Small broadleaved trees (<3 m) and shrubs	56	LCC-2_1_2 &    LCH-3_1_2	1.75

    Color Table (RGB with 256 entries) from tiff file
    10: 10,10,210
    15: 210,210,210
    20: 20,20,20
    21: 210,0,0
    30: 230,230,130
    35: 235,170,0
    40: 240,40,240
    45: 145,245,245
    48: 148,118,0
    50: 50,150,50
    51: 0,151,151
    55: 55,255,0
    56: 156,255,156

    46: 246,146,246,255
    11: 254,254,254,255
    """
    NODATA_WHITE = (0, (255, 255, 255), 'Nodata', '') # Outside Belgium/Wallonia

    WATER = (10, (10, 10, 210), _("Water"), 'LCC-3')
    NATURAL_MATERIAL_SURFACES = (15, (210, 210, 210), _("Natural Material Surfaces with less than 10% vegetation"), 'LCC-1_2')
    ARTIFICIALLY_SEALED_GROUND_SURFACE = (20, (20, 20, 20), _("Artificially sealed ground surface"), 'LCC-1_1_1_3')
    BUILDING = (21, (210, 0, 0), _("Building, specific structures and facilities"), 'LCC-1_1_1_1 || LCC-1_1_1_2')
    HERBACEOUS_ROTATION = (30, (230, 230, 130), _("Herbaceous in rotation during the year (e.g., crops)"), 'LCC-2_2')
    GRASSLAND_INTENSIVE_MANAGEMENT = (35, (235, 170, 0), _("Grassland with intensive management"), 'LCC-2_2')
    GRASSLAND_SCRUB_BIOLOGICAL_INTEREST = (40, (240, 40, 240), _("Grassland and scrub of biological interest"), 'LCC-2_2')
    INUNDATED_GRASSLAND_SCRUB_BIOLOGICAL_INTEREST = (45, (145, 245, 245), _("Inundated grassland and scrub of biological interest"), 'LCC-2_2 & LCH-4_4_2')
    VEGETATION_RECENTLY_DISTURBED_AREA = (48, (148, 118, 0), _("Vegetation of recently disturbed area (e.g., clear cut)"), 'LCC-2_2 & LCH-3_8')
    CONIFEROUS_TREES = (50, (50, 150, 50), _("Coniferous trees (≥3 m)"), 'LCC-2_1_1 & LCH-3_1_1')
    SMALL_CONIFEROUS_TREES = (51, (0, 151, 151), _("Small coniferous trees (<3 m)"), 'LCC-2_1_2 & LCH-3_1_1')
    BROADLEAVED_TREES = (55, (55, 255, 0), _("Broadleaved trees (≥3 m)"), 'LCC-2_1_1 & LCH-3_1_2')
    SMALL_BROADLEAVED_TREES_SHRUBS = (56, (156, 255, 156), _("Small broadleaved trees (<3 m) and shrubs"), 'LCC-2_1_2 & LCH-3_1_2')

    # NODATA11 = (11, (254,254,254,255)) # Not used
    # NODATA46 = (46, (246,146,246,255)) # Not used
    NODATA_BLACK = (100, (0, 0, 0), 'Nodata', '') # Outside Belgium/Wallonia

    @property
    def code(self) -> int:
        return self.value[0]

    @classmethod
    def reference(cls) -> str:
        """
        Return the reference
        """
        return 'https://www.mdpi.com/2306-5729/8/1/13'

    @classmethod
    def colors(cls, rgba:bool = False) -> list[tuple[int, int, int] | tuple[int, int, int, int]]:
        """
        Return the color of the class as a tuple (R, G, B)
        """
        if rgba:
            return [leg.value[1] + (255,) for leg in cls]
        else:
            return [leg.value[1] for leg in cls]

    @classmethod
    def codes(cls):
        """
        Return the code of the class as integer
        """
        return [leg.value[0] for leg in cls]

    @classmethod
    def plot_legend(cls, figax = None):
        """
        Return the color of the class as a tuple (R, G, B)
        """

        colors = cls.colors()
        codes = cls.codes()
        texts = cls.texts()

        if figax is None:
            fig, ax = plt.subplots(figsize=(1, 6))
        else:
            fig, ax = figax

        for i, color in enumerate(colors):
            ax.fill([0,1,1,0,0],[i,i,i+1,i+1,i], color=np.array(color)/255.0)
            ax.text(1.05, i + 0.5, f"{codes[i]}: {texts[i]}", va='center', fontsize=12)
            ax.axis('off')

        return fig, ax

    @classmethod
    def cmap(cls) -> plt.cm:
        """
        Return the colormap of the class
        """
        colors = np.asarray(cls.colors()).astype(float)/255.
        codes = np.asarray(cls.codes()).astype(float)

        normval = codes/100.

        normval[0] = 0.
        normval[-1] = 1.
        segmentdata = {"red": np.column_stack([normval, colors[:, 0], colors[:, 0]]),
                    "green": np.column_stack([normval, colors[:, 1], colors[:, 1]]),
                    "blue": np.column_stack([normval, colors[:, 2], colors[:, 2]]),
                    "alpha": np.column_stack([normval, np.ones(len(colors)) * 255., np.ones(len(colors)) * 255.])}

        return LinearSegmentedColormap('LifeWatch', segmentdata, 256)

    @classmethod
    def norm(cls) -> BoundaryNorm:
        """
        Return the norm of the class
        """
        return Normalize(0, 100)

    @classmethod
    def texts(cls):
        """
        Return the text of the class as a string
        """
        return [leg.value[2] for leg in cls]

    @classmethod
    def EAGLE_codes(cls):
        """
        Return the EAGLE code of the class as string
        """
        return [leg.value[3] for leg in cls]

    @classmethod
    def colors2codes(cls, array: np.ndarray | Image.Image,
                     aswolf:bool = True) -> np.ndarray:
        """
        Convert the color of the class to the code of the class
        :param array: numpy array or PIL image
        """

        if isinstance(array, Image.Image):
            mode = array.mode
            if mode == 'RGB':
                array = np.array(array)
            elif mode == 'RGBA':
                array = np.array(array)[:, :, :3]
            elif mode == 'P':
                array = np.array(array.convert('RGB'))
            else:
                raise ValueError(f"Unsupported image mode: {mode}")

        elif isinstance(array, np.ndarray):
            if array.ndim == 3 and array.shape[2] == 4:
                array = array[:, :, :3]
            elif array.ndim == 2:
                pass
            else:
                raise ValueError(f"Unsupported array shape: {array.shape}")

        unique_colors = np.unique(array.reshape(-1, array.shape[2]), axis=0)

        # check if the colors are in the legend
        for color in unique_colors:
            if not any(np.array_equal(color, leg.value[1]) for leg in cls):
                raise ValueError(f"Color {color} not found in legend")

        # convert the color to the code
        color_to_code = {leg.value[1]: leg.value[0] for leg in cls}
        code_array = np.zeros(array.shape[:2], dtype=np.uint8)
        for color, code in color_to_code.items():
            mask = np.all(array == color, axis=-1)
            code_array[mask] = code

        if aswolf:
            return np.asfortranarray(np.fliplr(code_array.T))
        else:
            return code_array

    @classmethod
    def codes2colors(cls, array: np.ndarray, asimage:bool = False) -> np.ndarray | Image.Image:
        """
        Convert the code of the class to the color of the class
        :param array: numpy array or PIL image
        """

        if isinstance(array, np.ndarray):
            if  array.ndim == 2:
                pass
            else:
                raise ValueError(f"Unsupported array shape: {array.shape}")
        else:
            raise ValueError(f"Unsupported array type: {type(array)}")

        # check if the codes are in the legend
        for code in np.unique(array):
            if code not in cls.codes():
                raise ValueError(f"Code {code} not found in legend")

        # convert the code to the color
        code_to_color = {leg.value[0]: leg.value[1] for leg in cls}
        color_array = np.zeros((*array.shape, 3), dtype=np.uint8)
        for code, color in code_to_color.items():
            mask = (array == code)
            color_array[mask] = color

        if asimage:
            color_array = Image.fromarray(color_array, mode='RGB')
            color_array = color_array.convert('RGBA')
            color_array.putalpha(255)
            return color_array
        else:
            return color_array

        return color_array

    @classmethod
    def getwolfpalette(cls) -> wolfpalette:
        """
        Get the wolf palette for the class
        """
        palette = wolfpalette()

        palette.set_values_colors(cls.codes(), cls.colors())
        palette.automatic = False
        palette.interval_cst = True

        return palette

def get_LifeWatch_bounds(year:int,
                         xmin:float,
                         ymin:float,
                         xmax:float,
                         ymax:float,
                         format:Literal['WolfArray',
                                        'NUMPY',
                                        'RGB',
                                        'RGBA',
                                        'Palette'] = 'WolfArray',
                         force_size:bool= True,
                                        ) -> tuple[WolfArray | np.ndarray | Image.Image, tuple[float, float, float, float]]:


    if year not in YEARS:
        raise ValueError(f"Year {year} not found in LifeWatch years")

    dx = xmax - xmin
    dy = ymax - ymin

    if force_size:
        w = dx / PIXEL_SIZE
        h = dy / PIXEL_SIZE

        if w > MAX_PIXELS or h > MAX_PIXELS:
            raise ValueError(f"Map size is too large: {w}x{h} pixels (max. {MAX_PIXELS}x{MAX_PIXELS})")
    else:

        if dx > dy:
            w = MAX_PIXELS
            h = int(dy * w / dx)
        else:
            h = MAX_PIXELS
            w = int(dx * h / dy)

    # Get the map from the WMS server
    mybytes = getLifeWatch(f'{MAP_LW}_{year}',
                        xmin, ymin,     # Lower left corner
                        xmax, ymax,     # Upper right corner
                        # Previous version was w=MAX_SIZE, h=None
                        # but that ignores the computation of w,h above.
                        # Moreover it makes it hard to get a specific size/resolution.
                        w, h, # Width and height of the image [pixels]
                        tofile=False,   # Must be False to get bytes --> save the image to ".\Lifewatch.png" if True
                        format='image/png; mode=8bit')

    # Check if the map is empty
    if mybytes is None:
        raise ValueError(f"Error getting LifeWatch map for year {year} -- Check you internet connection or the resolution of the map (max. 2048x2048 pixels or 2mx2m)")

    image = Image.open(mybytes) # Convert bytes to Image

    if format in ['RGB', 'RGBA', 'Palette']:
        if format == 'RGB':
            image = image.convert('RGB')
        elif format == 'RGBA':
            image = image.convert('RGBA')
        elif format == 'Palette':
            image = image.convert('P')
        else:
            raise ValueError(f"Unsupported format: {format}")

        return image, (xmin, ymin, xmax, ymax)

    elif format == 'NUMPY':
        return LifeWatch_Legend.colors2codes(image, aswolf=False), (xmin, ymin, xmax, ymax)

    elif format in ['WolfArray', 'WOLF']:
        h = header_wolf()
        h.set_origin(xmin, ymin)
        h.shape = image.size[0], image.size[1]
        h.set_resolution((xmax-xmin)/h.nbx, (ymax-ymin)/h.nby)
        wolf = WolfArray(srcheader=h, whichtype=WOLF_ARRAY_FULL_INTEGER)
        wolf.array[:,:] = LifeWatch_Legend.colors2codes(image, aswolf=True).astype(int)
        wolf.mask_data(0)
        wolf.mypal = LifeWatch_Legend.getwolfpalette()

        return wolf, (xmin, ymin, xmax, ymax)
    else:
        raise ValueError(f"Unsupported format: {format}")

def get_LifeWatch_Wallonia(year: int,
                           format:Literal['WolfArray',
                                          'NUMPY',
                                          'RGB',
                                          'RGBA',
                                          'Palette'] = 'WolfArray') -> WolfArray | np.ndarray | Image.Image:
    """
    Get the Wallonia LifeWatch map for the given year
    :param year: year of the map
    :param asimage: if True, return the image as PIL image, else return numpy array
    :return: numpy array or PIL image
    """

    # Whole Wallonia
    xmin = 40_000
    xmax = 300_000
    ymin = 10_000
    ymax = 175_000

    return get_LifeWatch_bounds(year, xmin, ymin, xmax, ymax, format, force_size=False)

def get_LifeWatch_center_width_height(year: int,
                            x: float,
                            y: float,
                            width: float = 2000,
                            height: float = 2000,
                            format:Literal['WolfArray',
                                           'NUMPY',
                                           'RGB',
                                           'RGBA',
                                           'Palette'] = 'WolfArray') -> tuple[WolfArray | np.ndarray | Image.Image, tuple[float, float, float, float]]:
    """
    Get the LifeWatch map for the given year and center
    :param year: year of the map
    :param x: x coordinate of the center
    :param y: y coordinate of the center
    :param asimage: if True, return the image as PIL image, else return numpy array
    :return: numpy array or PIL image
    """

    # compute bounds
    xmin = x - width / 2
    xmax = x + width / 2
    ymin = y - height / 2
    ymax = y + height / 2

    return get_LifeWatch_bounds(year, xmin, ymin, xmax, ymax, format)

def count_pixels(array:np.ndarray | WolfArray) -> dict[int, int]:
    """
    Count the number of pixels for each code in the array
    :param array: numpy array or WolfArray
    :return: dictionary with the code as key and the number of pixels as value
    """
    if isinstance(array, WolfArray):
        array = array.array[~array.array.mask]
    elif isinstance(array, np.ndarray):
        pass
    else:
        raise ValueError(f"Unsupported array type: {type(array)}")

    unique_codes, counts = np.unique(array, return_counts=True)

    for code in unique_codes:
        if code not in LifeWatch_Legend.codes():
            raise ValueError(f"Code {code} not found in legend")

    return {int(code): int(count) for code, count in zip(unique_codes, counts)}

def get_areas(array:np.ndarray | WolfArray) -> dict[int, float]:
    """
    Get the areas of each code in the array
    :param array: numpy array or WolfArray
    :return: dictionary with the code as key and the area in m² as value
    """
    if isinstance(array, WolfArray):
        array = array.array[~array.array.mask]
    elif isinstance(array, np.ndarray):
        pass
    else:
        raise ValueError(f"Unsupported array type: {type(array)}")

    unique_codes, counts = np.unique(array, return_counts=True)

    for code in unique_codes:
        if code not in LifeWatch_Legend.codes():
            raise ValueError(f"Code {code} not found in legend")

    return {int(code): float(count) * PIXEL_SIZE**2 for code, count in zip(unique_codes, counts)}