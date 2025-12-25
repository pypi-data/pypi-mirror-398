"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
from ..PyTranslate import _

from ..hydrometry.kiwis_gui import hydrometry_gui

import ctypes
myappid = 'wolf_hece_uliege' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def main():

    app = wx.App()
    frame = hydrometry_gui()
    app.MainLoop()


if __name__=='__main__':
    main()