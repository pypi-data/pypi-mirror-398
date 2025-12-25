"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from PIL import Image, ImageFont, ImageOps
from PIL.PngImagePlugin import PngInfo

try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
except:
    msg=_('Error importing OpenGL library')
    msg+=_('   Python version : ' + sys.version)
    msg+=_('   Please check your version of opengl32.dll -- conflict may exist between different files present on your desktop')
    raise Exception(msg)

from os.path import exists
from io import BytesIO
import math
import numpy as np

from .PyTranslate import _
from .PyWMS import getIGNFrance, getWalonmap, getVlaanderen, getLifeWatch, getNGI, getCartoweb, getOrthoPostFlood2021, getAlaro
from .textpillow import Font_Priority, Text_Image,Text_Infos
from .drawing_obj import Element_To_Draw

class genericImagetexture(Element_To_Draw):
    """
    Affichage d'une image en OpenGL via une texture
    """
    name: str
    idtexture: int

    width: int
    height: int

    which: str

    myImage: Image

    def __init__(self,
                 which: str,
                 label: str,
                 mapviewer,
                 xmin:float, xmax:float, ymin:float, ymax:float,
                 imageFile:str = "",
                 imageObj = None,
                 transparent_color = None,
                 tolerance:int = 3,
                 replace_color = None,
                 drawing_scale:float = 1.0,
                 offset:list[float, float] = [0.,0.]) -> None:

        """ Initialize the image texture

        :param which: Type of image (e.g., 'satellite', 'map', etc.)
        :param label: Label for the texture
        :param mapviewer: The map viewer object to which this texture belongs
        :param xmin: Minimum X coordinate for the texture
        :param xmax: Maximum X coordinate for the texture
        :param ymin: Minimum Y coordinate for the texture
        :param ymax: Maximum Y coordinate for the texture
        :param imageFile: Optional file path to load the image from
        :param imageObj: Optional PIL Image object to use instead of loading from file
        :param transparent_color: Color to treat as transparent in the image
        :param tolerance: Tolerance for color matching when replacing transparent color
        :param replace_color: Color to replace the transparent color with
        :param drawing_scale: Scale factor for the image
        :param offset: Offset to apply to the texture position
        """

        super().__init__(label, True, mapviewer, False)

        try:
            self.mapviewer.canvas.SetCurrent(mapviewer.context)
        except:
            logging.error(_('Opengl setcurrent -- Do you have a active canvas ?'))
            return

        self.time = None
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.idtexture = (GLuint * 1)()
        self.idx = 'texture_{}'.format(self.idtexture)

        try:
            glGenTextures(1, self.idtexture)
        except:
            raise NameError(
                'Opengl glGenTextures -- maybe a conflict with an existing opengl32.dll file - please rename the opengl32.dll in the libs directory and retry')

        self.which = which.lower()
        self.idx  = label
        self.name = label
        self.imageFile = imageFile
        self.myImage = imageObj

        self.drawing_scale = drawing_scale
        self.offset = offset

        if imageFile != "":
            if exists(imageFile):
                try:
                    self.myImage = Image.open(imageFile).convert('RGBA')
                except Exception as e:
                    logging.warning(_('Error opening image file : ') + str(imageFile))
                    logging.info(_('Trying to open image file with increased limit of pixels'))
                    Image.MAX_IMAGE_PIXELS = 10000000000
                    self.myImage = Image.open(imageFile).convert('RGBA')

        if self.myImage is not None:
            self.width = self.myImage.width
            self.height = self.myImage.height

            if transparent_color is not None:
                # replace the transparent color by a fully transparent pixel
                colors = np.asarray(self.myImage).copy()

                if tolerance == 0:
                    ij = np.where(colors[:,:,:3] == transparent_color)
                else:
                    ij = np.where(np.isclose(colors[:,:,:3], np.full((colors.shape[0],colors.shape[1],3), transparent_color), atol=tolerance))

                # set the alpha channel to 0 for the pixels that are close to the transparent color
                colors[ij[0],ij[1],3] = 0

                # colorize the pixels that are not transparent
                if replace_color is not None:
                    ij = np.where(colors[:,:,3] > 0)
                    colors[ij[0],ij[1],:] = replace_color

                # create a new image from the modified array
                self.myImage = Image.fromarray(colors)

        else:
            self.width = -99999
            self.height = -99999

        self.update_minmax()

        self.oldview = [self.xmin, self.xmax, self.ymin, self.ymax, self.width, self.height, self.time]

        self.load()

    def __del__(self):
        """ Destructor to unload the texture from memory """
        self.unload()

    def unload(self):
        """ Unload the texture from memory """

        self.mapviewer.canvas.SetCurrent(self.mapviewer.context)

        if self.idtexture is not None:
            glDeleteTextures(1, self.idtexture)

        if self.myImage is not None:
            del self.myImage

    def load(self, imageFile=""):
        """ Load the image texture into OpenGL

        :param imageFile: Optional file path to load the image from
        """

        if self.width == -99999 or self.height == -99999:
            return

        if self.mapviewer.canvas.SetCurrent(self.mapviewer.context):
            mybytes: BytesIO

            if imageFile != "":
                if not exists(imageFile):
                    return
                self.myImage = Image.open(imageFile).convert('RGBA')
            elif self.myImage is None:
                return

            glBindTexture(GL_TEXTURE_2D, self.idtexture[0])
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.myImage.width, self.myImage.height, 0, GL_RGBA,
                         GL_UNSIGNED_BYTE, self.myImage.tobytes())

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glGenerateMipmap(GL_TEXTURE_2D)
        else:
            raise NameError(
                'Opengl setcurrent -- maybe a conflict with an existing opengl32.dll file - please rename the opengl32.dll in the libs directory and retry')

    def update_minmax(self):
        """ Update the spatial extent of the texture based on its size """

        if self.myImage is None:
            return

        dx = self.xmax - self.xmin
        dy = self.ymax - self.ymin

        scale=dy/dx

        if int(scale*4) != int(float(self.height)/float(self.width)*4):
            scale = float(self.height)/float(self.width)

            self.ymax = self.ymin + dx *scale

    def reload(self, xmin=-99999, xmax=-99999, ymin=-99999, ymax=-99999):

        if xmin !=-99999:
            self.xmin = xmin
        if xmax !=-99999:
            self.xmax = xmax
        if ymin !=-99999:
            self.ymin = ymin
        if ymax !=-99999:
            self.ymax = ymax

        self.update_minmax()

        self.newview = [self.xmin, self.xmax, self.ymin, self.ymax, self.width, self.height, self.time]
        if self.newview != self.oldview:
            self.load()
            self.oldview = self.newview

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """ alias for paint"""
        self.paint()

    def find_minmax(self,update=False):
        """
        Generic function to find min and max spatial extent in data
        """
        # Nothing to do, set during initialization phase
        pass

    def uv(self, x: float, y: float) -> tuple[float, float]:
        """ Convert coordinates to texture coordinates taking into account the texture's spatial extent,
        the scaleing factor, and the offset.

        :param x: X coordinate in pixels
        :param y: Y coordinate in pixels
        :return: Tuple of (u, v) texture coordinates
        """
        if self.width == -99999 or self.height == -99999:
            return 0.0, 0.0

        u = (x - self.offset[0] - self.xmin) / ((self.xmax - self.xmin) * self.drawing_scale)
        v = 1.0 - (y - self.offset[1] - self.ymin) / ((self.ymax - self.ymin) * self.drawing_scale)

        # Ensure u and v are within the range [0, 1]
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))

        return u, v

    def paint(self):
        """ Paint the image texture on the OpenGL canvas """

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glColor4f(1., 1., 1., 1.)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindTexture(GL_TEXTURE_2D, self.idtexture[0])

        glBegin(GL_QUADS)

        # Draw a quad with texture coordinates
        xy = [[self.xmin, self.ymax],
              [self.xmax, self.ymax],
              [self.xmax, self.ymin],
              [self.xmin, self.ymin]]
        uv = [self.uv(x,y) for x,y in xy]

        glTexCoord2f(uv[0][0], uv[0][1])
        glVertex2f(xy[0][0], xy[0][1])
        glTexCoord2f(uv[1][0], uv[1][1])
        glVertex2f(xy[1][0], xy[1][1])
        glTexCoord2f(uv[2][0], uv[2][1])
        glVertex2f(xy[2][0], xy[2][1])
        glTexCoord2f(uv[3][0], uv[3][1])
        glVertex2f(xy[3][0], xy[3][1])

        # glTexCoord2f(0.0, 0.0)
        # glVertex2f(self.xmin, self.ymax)
        # glTexCoord2f(1.0, 0.0)
        # glVertex2f(self.xmax, self.ymax)
        # glTexCoord2f(1.0, 1.0)
        # glVertex2f(self.xmax, self.ymin)
        # glTexCoord2f(0.0, 1.0)
        # glVertex2f(self.xmin, self.ymin)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)


class imagetexture(Element_To_Draw):
    """
    Affichage d'une image, obtenue depuis un Web service, en OpenGL via une texture
    """

    name: str
    idtexture: int

    width: int
    height: int

    which: str
    category: str
    subcategory: str

    France: bool
    epsg: str

    def __init__(self, which: str, label: str, cat: str, subc: str, mapviewer,
                 xmin:float, xmax:float, ymin:float, ymax:float,
                 width:int = 1000, height:int = 1000,
                 France:bool = False, epsg='31370', Vlaanderen:bool = False,
                 LifeWatch:bool = False, IGN_Belgium:bool = False,
                 IGN_Cartoweb:bool = False, postFlood2021:bool = False,
                 Alaro:bool = False) -> None:

        super().__init__(label+cat+subc, plotted=False, mapviewer=mapviewer, need_for_wx=False)

        try:
            mapviewer.canvas.SetCurrent(mapviewer.context)
        except:
            logging.error(_('Opengl setcurrent -- Do you have a active canvas ?'))

        self.France = France
        self.Vlaanderen = Vlaanderen
        self.LifeWatch = LifeWatch
        self.IGN_Belgium = IGN_Belgium
        self.IGN_Cartoweb = IGN_Cartoweb
        self.postFlood2021 = postFlood2021
        self.Alaro = Alaro

        self.epsg = epsg

        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.idtexture = (GLuint * 1)()
        self.idx = 'texture_{}'.format(self.idtexture)

        self.time = None
        self.alpha = 1.0
        self.force_alpha = False

        try:
            glGenTextures(1, self.idtexture)
        except:
            raise NameError(
                'Opengl glGenTextures -- maybe a conflict with an existing opengl32.dll file - '
                'please rename the opengl32.dll in the libs directory and retry')
        self.width = width
        self.height = height
        self.which = which.lower()
        self.category = cat  # .upper()
        self.name = label
        self.subcategory = subc  # .upper()
        self.oldview = [self.xmin, self.xmax, self.ymin, self.ymax, self.width, self.height, self.time]

        self.load()

    def load(self):
        if self.width == -99999 or self.height == -99999:
            return

        if self.mapviewer.canvas.SetCurrent(self.mapviewer.context):
            mybytes: BytesIO

            if self.France:
                mybytes = getIGNFrance(self.category, self.epsg,
                                       self.xmin, self.ymin, self.xmax, self.ymax,
                                       self.width, self.height, False)

            elif self.Vlaanderen:
                mybytes = getVlaanderen(self.category,
                                       self.xmin, self.ymin, self.xmax, self.ymax,
                                       self.width, self.height, False)

            elif self.LifeWatch:
                mybytes = getLifeWatch(self.category + '_' + self.subcategory,
                                       self.xmin, self.ymin, self.xmax, self.ymax,
                                       self.width, self.height, False)
            elif self.IGN_Belgium:
                mybytes = getNGI(self.subcategory,
                                       self.xmin, self.ymin, self.xmax, self.ymax,
                                       self.width, self.height, False)

            elif self.IGN_Cartoweb:
                mybytes = getCartoweb(self.subcategory,
                                       self.xmin, self.ymin, self.xmax, self.ymax,
                                       self.width, self.height, False)

            elif self.postFlood2021:
                mybytes = getOrthoPostFlood2021(self.subcategory,
                                       self.xmin, self.ymin, self.xmax, self.ymax,
                                       self.width, self.height, False)

            elif self.Alaro:
                mybytes = getAlaro(self.subcategory,
                                       self.xmin, self.ymin, self.xmax, self.ymax,
                                       self.width, self.height, False, time= self.time)

            else:
                mybytes = getWalonmap(self.category + '/' + self.subcategory,
                                      self.xmin, self.ymin, self.xmax, self.ymax,
                                      self.width, self.height, False)

            if mybytes is None:
                logging.warning(_('Error opening image file : ') + str(self.category + '/' + self.subcategory))
                return

            try:
                if isinstance(mybytes, bytes | BytesIO):
                    image = Image.open(mybytes)

                    if image.mode != 'RGBA':
                        image = image.convert('RGBA')

                    if self.force_alpha:
                        if self.alpha < 0.0:
                            self.alpha = 0.0
                        if self.alpha > 1.0:
                            self.alpha = 1.0

                        alpha = Image.new('L', image.size, int(self.alpha * 255))

                        image.putalpha(alpha)

                elif isinstance(mybytes, str):
                    image = Image.open(mybytes).convert('RGB')

                    if image.width != self.width or image.height != self.height:
                        image = image.resize((self.width, self.height), Image.ANTIALIAS)

                    image_memory = BytesIO()
                    image.save(image_memory, format='PNG')
                    image = Image.open(image_memory)

                elif isinstance(mybytes, Image.Image):
                    image = mybytes
                else:
                    logging.error(_('Unknown type of image file : ') + str(type(mybytes)))
                    return

            except Exception as e:
                logging.warning(_('Error opening image file : ') + str(self.category + '/' + self.subcategory))
                return

            glBindTexture(GL_TEXTURE_2D, self.idtexture[0])
            if self.subcategory[:5] == 'ORTHO':
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                             image.tobytes())
            elif image.mode == 'RGB':
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.width, image.height, 0, GL_RGB, GL_UNSIGNED_BYTE,
                             image.tobytes())
            else:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                             image.tobytes())
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glGenerateMipmap(GL_TEXTURE_2D)
        else:
            raise NameError(
                'Opengl setcurrent -- maybe a conflict with an existing opengl32.dll file - '
                'please rename the opengl32.dll in the libs directory and retry')

    def reload(self):
        dx = self.mapviewer.xmax - self.mapviewer.xmin
        dy = self.mapviewer.ymax - self.mapviewer.ymin
        cx = self.mapviewer.mousex
        cy = self.mapviewer.mousey

        coeff = .5
        self.xmin = cx - dx * coeff
        self.xmax = cx + dx * coeff
        self.ymin = cy - dy * coeff
        self.ymax = cy + dy * coeff
        self.width = int(self.mapviewer.canvaswidth * 2 * coeff)
        self.height = int(self.mapviewer.canvasheight * 2 * coeff)

        self.newview = [self.xmin, self.xmax, self.ymin, self.ymax, self.width, self.height, self.time]
        if self.newview != self.oldview:
            self.load()
            self.oldview = self.newview

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """ alias for paint"""
        self.paint()

    def find_minmax(self,update=False):
        """
        Generic function to find min and max spatial extent in data
        """
        # Nothing to do, set during initialization phase
        pass

    def paint(self):

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glColor4f(1., 1., 1., 1.)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindTexture(GL_TEXTURE_2D, self.idtexture[0])

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(self.xmin, self.ymax)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(self.xmax, self.ymax)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(self.xmax, self.ymin)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(self.xmin, self.ymin)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def check_plot(self):
        self.plotted = True

    def uncheck_plot(self, unload=True):
        self.plotted = False


class Text_Image_Texture(genericImagetexture):

    def __init__(self, text: str, mapviewer, proptext:Text_Infos, vector, x:float, y:float) -> None:
        """Gestion d'un texte sous forme de texture OpenGL

        Args:
            text (str): texte à afficher
            mapviewer (wolf_mapviewer): objet parent sur lequel dessiner
            proptext (Text_Infos): infos sur la mise en forme
            vector (vector): vecteur associé au texte
            x (float): point d'accroche X
            y (float): point d'accroche Y
        """
        self.x = x
        self.y = y

        self.vector = vector
        self.proptext = proptext

        self.mapviewer = mapviewer

        self.findscale()

        self.proptext.findsize(text)
        xmin, xmax, ymin, ymax = proptext.getminmax(self.x,self.y)

        super().__init__('other', text, mapviewer, xmin, xmax, ymin, ymax)

        if self.myImage is not None:
            self.width = self.myImage.width
            self.height = self.myImage.height

        self.oldview = [self.xmin, self.xmax, self.ymin, self.ymax, self.width, self.height, self.time]

    def findscale(self):

        self.proptext.setscale(self.mapviewer.sx, self.mapviewer.sy)

    def load(self, imageFile=""):


        if self.mapviewer.canvas.SetCurrent(self.mapviewer.context):

            if imageFile != "":
                if not exists(imageFile):
                    return
                self.myImage = Image.open(imageFile).convert('RGBA')
            else:
                self.myImage = Text_Image(self.name, self.proptext).image

            if self.myImage is None:
                return

            glEnable(GL_TEXTURE_2D)

            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glBindTexture(GL_TEXTURE_2D, self.idtexture[0])
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.myImage.width, self.myImage.height, 0, GL_RGBA,
                         GL_UNSIGNED_BYTE, self.myImage.transpose(Image.FLIP_TOP_BOTTOM).tobytes())

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glGenerateMipmap(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, 0)

            glDisable(GL_TEXTURE_2D)
        else:
            raise NameError(
                'Opengl setcurrent -- maybe a conflict with an existing opengl32.dll file - please rename the opengl32.dll in the libs directory and retry')

    def paint(self):

        self.findscale()
        self.proptext.setsize_real()

        if self.proptext.adapt_fontsize(self.name):
            self.update_image()
        x,y = self.proptext.getcorners(self.x,self.y)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glColor4f(1., 1., 1., 1.)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)

        glBindTexture(GL_TEXTURE_2D, self.idtexture[0])

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(x[0], y[0])
        glTexCoord2f(1.0, 0.0)
        glVertex2f(x[1], y[1])
        glTexCoord2f(1.0, 1.0)
        glVertex2f(x[2], y[2])
        glTexCoord2f(0.0, 1.0)
        glVertex2f(x[3], y[3])
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)

        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def update_image(self, newtext:str="", proptext:Text_Infos=None):

        if newtext !="":
            self.name = newtext

        if proptext is not None:
            self.proptext = proptext

        self.load()