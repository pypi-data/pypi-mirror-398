"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

"""
This is a minimal wxPython SplashScreen
"""
try:
    from osgeo import gdal
except ImportError as e:
    print(f"Import Error: {e} - GDAL")
    print("Please install GDAL for your Python version.")

from os.path import dirname, join, exists
import wx
import time
from   wx.adv import SplashScreen as SplashScreen,SPLASH_CENTRE_ON_SCREEN,SPLASH_TIMEOUT,Sound

try:
    from wolf_libs import wolfogl
except ImportError:
    print("** WolfOGL not found **")
    print("Without WolfOGL, the application will not work !")
    print("Please reinstall 'wolfhece' package -- pip install wolfhece --force-reinstall")

class WolfLauncher(SplashScreen):
    """
    Wolf Splashcreen
    """

    done = False

    def __init__(self, parent=None, play_sound=True):

        if self.done:
            return

        # try:
        #     wolfogl.init()
        # except ImportError:
        #     print("Error initializing WolfOGL -- We must stop here !")
        #     print("Please reinstall 'wolfhece' package -- pip install wolfhece")
        #     exit()

        mydir=dirname(__file__)
        mybitmap = wx.Bitmap(name=join(mydir,".\\WolfPython2.png"), type=wx.BITMAP_TYPE_PNG)

        mask = wx.Mask(mybitmap, wx.Colour(255,0,204))
        mybitmap.SetMask(mask)
        splash = SPLASH_CENTRE_ON_SCREEN | SPLASH_TIMEOUT
        duration = 1000 # milliseconds

        # Call the constructor with the above arguments
        # in exactly the following order.
        super(WolfLauncher, self).__init__(bitmap=mybitmap,
                                            splashStyle=splash,
                                            milliseconds=duration,
                                            parent=None,
                                            id=-1,
                                            pos=wx.DefaultPosition,
                                            size=wx.DefaultSize,
                                            style=wx.STAY_ON_TOP |
                                                    wx.BORDER_NONE)

        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.CenterOnScreen(wx.BOTH)
        self.Show()

        if play_sound:
            soundfile=['son6.wav']
            if exists(join(mydir,'../sounds/'+soundfile[0])):
                time.sleep(1)
                mysound = Sound(join(mydir,'../sounds/'+soundfile[0]))
                mysound.Play()

        self.done = True

    def OnExit(self, event):
        # These two comments comes from :
        # https://wiki.wxpython.org/How%20to%20create%20a%20splash%20screen%20%28Phoenix%29

        # The program will freeze without this line.
        event.Skip()  # Make sure the default handler runs too...
        self.Hide()
