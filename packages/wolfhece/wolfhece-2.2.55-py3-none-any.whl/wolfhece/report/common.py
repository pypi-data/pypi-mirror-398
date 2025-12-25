import sys
import wx
import os
import platform

import pandas as pd
import pymupdf as pdf
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from functools import cached_property
from PIL import Image

import matplotlib.pyplot as plt
import numpy as np
import logging
from pathlib import Path
from datetime import datetime as dt

from .. import __version__ as wolfhece_version
try:
    from wolfgpu.version import __version__ as wolfgpu_version
except ImportError:
    wolfgpu_version = "not installed"

from ..PyVertexvectors import vector, zone, Zones, wolfvertex as wv
from ..PyTranslate import _

def pts2cm(pts):
    """ Convert points to centimeters for PyMuPDF.

    One point equals 1/72 inches.
    """
    return pts / 28.346456692913385  # 1 point = 1/28.346456692913385 cm = 2.54/72

def pt2inches(pts):
    """ Convert points to inches for PyMuPDF.

    One point equals 1/72 inches.
    """
    return pts / 72.0  # 1 point = 1/72 inches

def inches2cm(inches):
    """ Convert inches to centimeters.

    One inch equals 2.54 centimeters.
    """
    return inches * 2.54  # 1 inch = 2.54 cm

def cm2pts(cm):
    """ Convert centimeters to points for PyMuPDF.

    One point equals 1/72 inches.
    """
    return cm * 28.346456692913385  # 1 cm = 28.346456692913385 points = 72/2.54

def cm2inches(cm):
    """ Convert centimeters to inches.

    One inch equals 2.54 centimeters.
    """
    return cm / 2.54  # 1 cm = 1/2.54 inches

def A4_rect():
    """ Return the A4 rectangle in PyMuPDF units.

    (0, 0) is the top-left corner in PyMuPDF coordinates.
    """
    return pdf.Rect(0, 0, cm2pts(21), cm2pts(29.7))  # A4 size in points (PDF units)

def rect_cm(x, y, width, height):
    """ Create a rectangle in PyMuPDF units from centimeters.

    (0, 0) is the top-left corner in PyMuPDF coordinates.
    """
    return pdf.Rect(cm2pts(x), cm2pts(y), cm2pts(x) + cm2pts(width), cm2pts(y) + cm2pts(height))

def get_rect_from_text(text, width, fontsize=10, padding=5):
    """ Get a rectangle that fits the text in PyMuPDF units.

    :param text: The text to fit in the rectangle.
    :param width: The width of the rectangle in centimeters.
    :param fontsize: The font size in points.
    :param padding: Padding around the text in points.
    :return: A PyMuPDF rectangle that fits the text.
    """
    # Create a temporary PDF document to measure the text size
    with NamedTemporaryFile(delete=True, suffix='.pdf') as temp_pdf:
        doc = pdf.Document()
        page = doc.new_page(A4_rect())
        text_rect = page.insert_text((0, 0), text, fontsize=fontsize, width=cm2pts(width))
        doc.save(temp_pdf.name)

        # Get the size of the text rectangle
        text_width = text_rect.width + padding * 2
        text_height = text_rect.height + padding * 2
        # Create a rectangle with the specified width and height
        rect = pdf.Rect(0, 0, cm2pts(width), text_height)
        # Adjust the rectangle to fit the text
        rect.x0 -= padding
        rect.y0 -= padding
        rect.x1 += padding
        rect.y1 += padding
        return rect

def single_line_to_html(text, font_size="10pt", font_family="Helvetica"):
    # Génère le CSS
    css = f"""
p {{font-size:{font_size};
    font-family:{font_family};
    color:#000000;
    align-text:center}}
    """
    # Génère le HTML
    html = f"<p>{text}</p>"

    return html, css

def list_to_html(list_items, font_size="10pt", font_family="Helvetica"):
    # Génère le CSS
    css = f"""
p {{font-size:{font_size};
    font-family:{font_family};
    color:#BEBEBE;
    align-text:center}}

ul.list {{
    font-size: {font_size};
    font-family: {font_family};
    color: #2C3E50;
    padding-left: 20px;
    }}
li {{
    margin-bottom: 5px;
    }}
    """

    # Génère le HTML
    html = "<ul class='list'>"
    for item in list_items:
        html += f"  <li>{item}</li>\n"
    html += "</ul>"

    css = css.replace('\n', ' ')  # Remove newlines in CSS for better readability

    return html, css


def list_to_html_aligned(list_items, font_size="10pt", font_family="Helvetica"):
    # Génère le CSS
    css = f"""
p {{font-size:{font_size};
    font-family:{font_family};
    color:#BEBEBE;
    align-text:left}}

div.list {{
    font-size: {font_size};
    font-family: {font_family};
    color: #2C3E50;
    padding-left: 8px;
    align-text:left
}}
li {{
    margin-bottom: 5px;
}}
"""

    # Génère le HTML
    html = "<div class='list'>"
    html += " - ".join(list_items)  # Join the items with a hyphen
    html += "</div>"

    css = css.replace('\n', ' ')  # Remove newlines in CSS for better readability

    return html, css


def dict_to_html(data_dict:dict, font_size="10pt", font_family="Helvetica"):
    """ Convert a dictionary to an HTML table with dataframe_image """

    df = pd.DataFrame.from_dict(data_dict)

    # Convert the DataFrame to an HTML table
    html = df.to_html(index=False, border=0, justify='left')

    # Generate the CSS
    css = f"""
    table {{
        font-size: {font_size};
        font-family: {font_family};
        color: #2C3E50;
        border-collapse: collapse;
    }}
    th, td {{
        padding: 8px 12px;
        border: 1px solid #BDC3C7;
    }}
    """

    return html, css

def dataframe_to_html(data:pd.DataFrame, font_size="10pt", font_family="Helvetica"):
    """ Convert a DataFrame to an HTML table with dataframe_image """

    # Convert the DataFrame to an HTML table
    html = data.to_html(index=False, border=0, justify='left')

    # Generate the CSS
    css = f"""
    table {{
        font-size: {font_size};
        font-family: {font_family};
        color: #2C3E50;
        border-collapse: collapse;
    }}
    th, td {{
        padding: 8px 12px;
        border: 1px solid #BDC3C7;
    }}
    """

    return html, css

def convert_report_to_images(pdf_path: str | Path, dpi=150) -> list[Image.Image]:
    """ Convert the PDF report to a list of images (one per page).

    :param dpi: Dots per inch for the output images.
    :return: List of Images, one per page.
    """

    if pdf_path is None:
        raise ValueError("PDF report has not been saved yet. Please save the report before converting to images.")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF report not found at {pdf_path}. Please check the path.")

    doc = pdf.open(pdf_path)
    images = []

    zoom = dpi / 72  # 72 dpi is the default resolution
    mat = pdf.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    return images

# A4 format
PAGE_WIDTH = 21  # cm
PAGE_HEIGHT = 29.7  # cm

# Default Powerpoint 16:9 slide dimensions
SLIDE_HEIGHT = inches2cm(7.5)  # cm
SLIDE_WIDTH = inches2cm(13.3333)  # cm

class DefaultLayoutA4(Zones):
    """
    Global layout for A4 report.

    This class inherits from Zones and defines a standard layout for A4 reports.
    It includes predefined areas for the title, versions, logo, and footer.
    """

    def __init__(self, title:str, filename = '', ox = 0, oy = 0, tx = 0, ty = 0, parent=None, is2D=True, idx = '', plotted = True, mapviewer=None, need_for_wx = False, bbox = None, find_minmax = True, shared = False, colors = None):
        super().__init__(filename, ox, oy, tx, ty, parent, is2D, idx, plotted, mapviewer, need_for_wx, bbox, find_minmax, shared, colors)

        self.title = title

        self.left_right_margin = 1  # cm
        self.top_bottom_margin = 0.5  # cm
        self.padding = 0.5  # cm

        WIDTH_TITLE = 16  # cm
        HEIGHT_TITLE = 1.5  # cm

        WIDTH_VERSIONS = 16  # cm
        HEIGHT_VERSIONS = .5 # cm

        X_LOGO = 18.5  # Logo starts after the title and versions
        WIDTH_LOGO = 1.5  # cm
        HEIGHT_LOGO = 1.5  # cm

        HEIGHT_FOOTER = 1.2  # cm

        page = zone(name='Page')
        elts = zone(name='Elements')

        self.add_zone(page, forceparent= True)
        self.add_zone(elts, forceparent= True)

        vec_page = vector(name=_("Page"))
        vec_page.add_vertex(wv(0, 0))
        vec_page.add_vertex(wv(PAGE_WIDTH, 0))
        vec_page.add_vertex(wv(PAGE_WIDTH, PAGE_HEIGHT))
        vec_page.add_vertex(wv(0, PAGE_HEIGHT))
        vec_page.force_to_close()
        page.add_vector(vec_page, forceparent=True)

        vec_title = vector(name=_("Title"))
        y_from_top = PAGE_HEIGHT - self.top_bottom_margin
        vec_title.add_vertex(wv(self.left_right_margin, y_from_top))
        vec_title.add_vertex(wv(self.left_right_margin + WIDTH_TITLE, y_from_top))
        vec_title.add_vertex(wv(self.left_right_margin + WIDTH_TITLE, y_from_top - HEIGHT_TITLE))
        vec_title.add_vertex(wv(self.left_right_margin, y_from_top - HEIGHT_TITLE))
        vec_title.force_to_close()
        vec_title.set_legend_text(_("Title of the report"))
        vec_title.set_legend_position_to_centroid()
        vec_title.myprop.legendvisible = True
        vec_title.find_minmax()
        elts.add_vector(vec_title, forceparent=True)

        vec_versions = vector(name=_("Versions"))
        y_from_top = PAGE_HEIGHT - self.top_bottom_margin - HEIGHT_TITLE - self.padding
        vec_versions.add_vertex(wv(self.left_right_margin, y_from_top))
        vec_versions.add_vertex(wv(self.left_right_margin + WIDTH_VERSIONS, y_from_top))
        vec_versions.add_vertex(wv(self.left_right_margin + WIDTH_VERSIONS, y_from_top - HEIGHT_VERSIONS))
        vec_versions.add_vertex(wv(self.left_right_margin, y_from_top - HEIGHT_VERSIONS))
        vec_versions.force_to_close()
        vec_versions.set_legend_text(_("Versions of the software"))
        vec_versions.set_legend_position_to_centroid()
        vec_versions.myprop.legendvisible = True
        vec_versions.find_minmax()
        elts.add_vector(vec_versions, forceparent=True)

        vec_logo = vector(name=_("Logo"))
        # Logo is placed at the top right corner, after the title and versions
        # Adjust the position based on the logo size
        y_from_top = PAGE_HEIGHT - self.top_bottom_margin
        vec_logo.add_vertex(wv(X_LOGO, y_from_top))
        vec_logo.add_vertex(wv(X_LOGO + WIDTH_LOGO, y_from_top))
        vec_logo.add_vertex(wv(X_LOGO + WIDTH_LOGO, y_from_top - HEIGHT_LOGO))
        vec_logo.add_vertex(wv(X_LOGO, y_from_top - HEIGHT_LOGO))
        vec_logo.force_to_close()
        vec_logo.set_legend_text(_("Logo"))
        vec_logo.set_legend_position_to_centroid()
        vec_logo.myprop.legendvisible = True
        vec_logo.find_minmax()
        elts.add_vector(vec_logo, forceparent=True)

        vec_footer = vector(name=_("Footer"))
        vec_footer.add_vertex(wv(self.left_right_margin, self.top_bottom_margin))
        vec_footer.add_vertex(wv(PAGE_WIDTH - self.left_right_margin, self.top_bottom_margin))
        vec_footer.add_vertex(wv(PAGE_WIDTH - self.left_right_margin, self.top_bottom_margin + HEIGHT_FOOTER))
        vec_footer.add_vertex(wv(self.left_right_margin, self.top_bottom_margin + HEIGHT_FOOTER))
        vec_footer.force_to_close()
        vec_footer.set_legend_text(_("Footer of the report"))
        vec_footer.set_legend_position_to_centroid()
        vec_footer.myprop.legendvisible = True
        vec_footer.find_minmax()
        elts.add_vector(vec_footer, forceparent=True)

        self._doc = None # Placeholder for the PDF document
        self._pdf_path = None  # Placeholder for the PDF file path

    def add_element(self, name:str, width:float, height:float, x:float = 0, y:float = 0) -> vector:
        """
        Add a single element to the page.

        :param name: Name of the element.
        :param width: Width of the element in cm.
        :param height: Height of the element in cm.
        :param x: X coordinate of the bottom-left corner in cm.
        :param y: Y coordinate of the bottom-left corner in cm.
        :return: The created vector representing the element.
        """

        vec = vector(name=name)
        vec.add_vertex(wv(x, y))
        vec.add_vertex(wv(x + width, y))
        vec.add_vertex(wv(x + width, y + height))
        vec.add_vertex(wv(x, y + height))
        vec.force_to_close()
        vec.find_minmax()
        vec.set_legend_text(name)
        vec.set_legend_position_to_centroid()
        vec.myprop.legendvisible = True

        self['Elements'].add_vector(vec, forceparent=True)

        return vec

    def add_element_repeated(self, name:str, width:float, height:float,
                             first_x:float = 0, first_y:float = 0,
                             count_x:int = 1, count_y:int = 1,
                             padding:float = None) -> zone:
        """
        Add multiple elements to the page in a grid.

        :param name: Base name for the elements.
        :param width: Width of each element in cm.
        :param height: Height of each element in cm.
        :param first_x: X coordinate of the first element in cm.
        :param first_y: Y coordinate of the first element in cm.
        :param count_x: Number of elements in the X direction (positive for right, negative for left).
        :param count_y: Number of elements in the Y direction (positive for up, negative for down).
        :param padding: Padding between elements in cm. If None, use self.padding.
        :return: A zone containing the added elements.
        """

        if padding is None:
            padding = self.padding

        delta_x = width + padding if count_x > 0 else -(padding + width)
        delta_y = height + padding if count_y > 0 else -(padding + height)

        count_x = abs(count_x)
        count_y = abs(count_y)

        x = first_x
        y = first_y if delta_y > 0 else first_y - height

        elements = zone(name=name + '_elements')
        for j in range(count_y):
            for i in range(count_x):
                elements.add_vector(self.add_element(name + f"_{i}-{j}", width, height, x, y), forceparent=False)
                x += delta_x
            x = first_x
            y += delta_y

        elements.find_minmax()

        return elements


    def check_if_overlap(self, vec:vector) -> bool:
        """
        Check if the vector overlaps with any existing vector in the page layout.

        :param vec: The vector to check.
        :return: True if there is an overlap, False otherwise.
        """
        for existing_vec in self['Elements'].myvectors:
            if vec.linestring.overlaps(existing_vec.linestring):
                return True
        return False

    @property
    def useful_part(self) -> vector:
        """
        Get the useful part of the page, excluding margins.
        """

        vec = self[('Page', _('Page'))]
        vec.find_minmax()

        version = self[('Elements', _('Versions'))]
        version.find_minmax()

        footer = self[('Elements', _('Footer'))]
        footer.find_minmax()

        useful_part = vector(name=_("Useful part of the page"))
        useful_part.add_vertex(wv(vec.xmin + self.left_right_margin, version.ymin - self.padding))
        useful_part.add_vertex(wv(vec.xmax - self.left_right_margin, version.ymin - self.padding))
        useful_part.add_vertex(wv(vec.xmax - self.left_right_margin, footer.ymax + self.padding))
        useful_part.add_vertex(wv(vec.xmin + self.left_right_margin, footer.ymax + self.padding))
        useful_part.force_to_close()

        useful_part.find_minmax()
        useful_part.set_legend_text(_("Useful part of the page"))
        useful_part.set_legend_position_to_centroid()
        useful_part.myprop.legendvisible = True

        return useful_part

    @property
    def page_dimension(self) -> tuple[float, float]:
        """
        Get the dimensions of the page in centimeters.
        """

        vec = self[('Page', _('Page'))]
        vec.find_minmax()
        width = vec.xmax - vec.xmin
        height = vec.ymax - vec.ymin
        return width, height

    @property
    def keys(self) -> list[str]:
        """
        Get the keys of the page layout.
        """

        return [vec.myname for vec in self['Elements'].myvectors]

    @cached_property
    def layout(self) -> dict:
        """
        Get the layout as a dictionary.
        """

        return self._to_dict()

    def get_item_in_layout(self, name:str):
        """ Override the indexing to access layout elements by name. """
        if isinstance(name, str):
            if name not in self.layout:
                raise KeyError(f"Element '{name}' not found in layout.")

        return self.layout[name]

    def _to_dict(self):
        """
        Convert the layout Zones to a dictionary.
        """

        layout = {}

        for vec in self['Elements'].myvectors:
            vec.find_minmax()
            layout[vec.myname] = rect_cm(vec.xmin, PAGE_HEIGHT - vec.ymax, vec.xmax - vec.xmin, vec.ymax - vec.ymin)

        return layout

    def plot(self, scale=1.):
        """
        Plot the page layout using matplotlib.

        :param scale: Scale factor for the plot.
        """

        fig, ax = plt.subplots(figsize=(cm2inches(PAGE_WIDTH) * scale, cm2inches(PAGE_HEIGHT)*scale))

        self['Elements'].plot_matplotlib(ax = ax)
        ax.set_aspect('equal')

        ax.set_xlim(0, PAGE_WIDTH)
        ax.set_ylim(0, PAGE_HEIGHT)

        ax.set_yticks(list(np.arange(0, PAGE_HEIGHT, 1))+[PAGE_HEIGHT])
        ax.set_xticks(list(np.arange(0, PAGE_WIDTH + 1, 1)))

        plt.title(_("Layout of the report"))
        plt.xlabel(_("Width (cm)"))
        plt.ylabel(_("Height (cm)"))
        # plt.grid(True)

        return fig, ax

    def _summary_versions(self):
        """ Find the versions of the simulation, wolfhece and the wolfgpu package """
        import json

        group_title = "Versions"
        text = [f"Wolfhece : {wolfhece_version}",
                f"Wolfgpu : {wolfgpu_version}",
                f"Python : {sys.version.split()[0]}",
                f"Operating System: {os.name}"
                ]

        return group_title, text

    def _insert_to_page(self, page: pdf.Page):
        """ Insert the layout into the PDF page. """

        page.insert_htmlbox(self.layout['Title'], f"<h1>{self.title}</h1>",
                                css='h1 {font-size:16pt; font-family:Helvetica; color:#333}')

        # versions box
        try:
            text = self._summary_versions()
            html, css = list_to_html_aligned(text[1], font_size="10pt", font_family="Helvetica")
            spare_height, scale = page.insert_htmlbox(self.layout['Versions'], html, css=css, scale_low=0.1)

            if spare_height < 0.:
                logging.warning("Text overflow in versions box. Adjusting scale.")
        except:
            logging.error("Failed to insert versions text. Using fallback method.")

        rect = self.layout['Logo']
        # Add the logo to the top-right corner
        logo_path = Path(__file__).parent / 'wolf_report.png'
        if logo_path.exists():
            page.insert_image(rect, filename=str(logo_path),
                              keep_proportion=True,
                              overlay=True)

        # Footer
        # ------
        # Insert the date and time of the report generation, the user and the PC name
        footer_rect = self.layout['Footer']
        footer_text = f"<p>Report generated on {dt.now()} by {os.getlogin()} on {platform.uname().node} - {platform.uname().machine} - {platform.uname().release} - {platform.uname().version}</br> \
        This report does not guarantee the quality of the model and in no way commits the software developers.</p>"
        page.insert_htmlbox(footer_rect, footer_text,
                            css='p {font-size:10pt; font-family:Helvetica; color:#BEBEBE; align-text:center}',)

    def create_report(self) -> pdf.Document:
        """ Create the PDF report for the default LayoutA4. """

        # Create a new PDF document
        self._doc = pdf.Document()

        # Add a page
        self._page = self._doc.new_page()

        # Insert the layout into the page
        self._insert_to_page(self._page)

        return self._doc

    def save_report(self, output_path: Path | str):
        """ Save the report to a PDF file """

        if self._doc is None:
            self.create_report()

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
