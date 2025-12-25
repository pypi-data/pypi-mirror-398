"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx

from .PyTranslate import _
from .PyParams import Wolf_Param

def main():
    ex = wx.App()
    frame = Wolf_Param(None,"Params",to_read=False)
    ex.MainLoop()

if __name__=="__main__":
    main()