"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

"""
Logging handler to redirect messages sent to the python logging module to wx if necessary

How tu use it :

 import logging
 from wolfhece.pylogging import create_wxlogwindow

 myapp = wx.App()
 create_wxlogwindow('My first wx log Window')

and use logging as usual

"""
import wx
import logging

class LoggingPythonWxBridgeHandler(logging.Handler):
    def __init__(self, winTitle: str = "Log", show=True):
        # assert wxParent is not None, "You must provide an initial parent frame"
        super().__init__()
        # This is a member variable so that the GC
        # doesn't kill the window too early.
        # When the WxApp closes, it will close this window
        # and that may invalidate the variable. So
        # use the variable with care.
        self._log_window = wx.LogWindow(None, winTitle)
        self._log_window.PassMessages(False) # évite que les messages ne soit affichés en popup en plus de la fenêtre de Logs

    def emit(self, record: logging.LogRecord):
        if record.levelno < logging.DEBUG:
            wx.LogVerbose(record.getMessage())
        elif record.levelno < logging.INFO:
            wx.LogDebug(record.getMessage())
        elif record.levelno < logging.WARNING:
            wx.LogMessage(record.getMessage())
        elif record.levelno < logging.ERROR:
            wx.LogWarning(record.getMessage())
        else:
            wx.LogError(record.getMessage())

def create_wxlogwindow(winTitle='Log') -> wx.LogWindow:

    log_bridge_handler=None

    if wx.App.Get() is not None:
        """
        test if a LoggingPythonWxBridgeHandler exists
        if it is the case, nothing to do
        otherwise, create it !
        """
        create=True
        for curhand in logging.getLogger().handlers:
            if isinstance(curhand, LoggingPythonWxBridgeHandler):
                create=False
        if create:
            log_bridge_handler = LoggingPythonWxBridgeHandler(winTitle)
            logging.getLogger().addHandler(log_bridge_handler)

            # Set some logging level, just to show up.
            logging.getLogger().setLevel(logging.INFO)
            log_bridge_handler.setLevel(logging.INFO)
            wx.Log.SetVerbose(True)

            return log_bridge_handler._log_window

    return None

class ADemonstrationFrame(wx.Frame):
    def __init__(self):
        TITLE = "wxPython Logging To A Control"
        wx.Frame.__init__(self, None, wx.ID_ANY, TITLE)

        panel = wx.Panel(self, wx.ID_ANY)
        self.log = wx.TextCtrl(panel, wx.ID_ANY, size=(300,100),
                          style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        btn = wx.Button(panel, wx.ID_ANY, 'Log something!')
        self.Bind(wx.EVT_BUTTON, self.onButton, btn)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.log, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(btn, 0, wx.ALL|wx.CENTER, 5)
        panel.SetSizer(sizer)

    def onButton(self, event):
        self.log.AppendText("Adding some logs")

        logging.debug("A debug log message")
        logging.info("A info log message")
        logging.warning("A warning log message")
        logging.error("An error log message")
        logging.critical("An critical log message")



if __name__ == "__main__":
    import sys
    app = wx.App()
    frame = ADemonstrationFrame()

    # Connect the python logging to the wx one.
    log_bridge_handler = LoggingPythonWxBridgeHandler()
    logging.getLogger().addHandler(log_bridge_handler)

    # Set some logging level, just to show up.
    logging.getLogger().setLevel(logging.DEBUG)
    log_bridge_handler.setLevel(logging.INFO)
    # Make sure debug-lvl messages show up in the log window eventhough
    # we discard the debug level later on
    wx.Log.SetVerbose(True)

    # Just for fun, add a "log to console" too...
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter( logging.Formatter('[%(levelname)s] %(asctime)s: %(message)s'))
    console_handler.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(console_handler)

    frame.Show()
    app.MainLoop()