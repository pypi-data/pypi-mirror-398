"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import ctypes
myappid = 'wolf_hece_uliege' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

import wx

from ..PyTranslate import _

def main():
    ex = wx.App()

    from .splashscreen import WolfLauncher
    first_launch = WolfLauncher(play_sound=False)

    from ..PyParams import Wolf_Param

    frame = Wolf_Param(None,"Params")
    ex.MainLoop()

if __name__=="__main__":
    main()