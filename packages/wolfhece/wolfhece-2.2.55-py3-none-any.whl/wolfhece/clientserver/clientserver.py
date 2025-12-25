"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
import numpy as np
import socket

class Server(wx.Frame):

    def __init__(self, parent, title):
        super(Server, self).__init__(parent, title=title, size=(300, 200))
        self.panel = wx.Panel(self)
        self.text_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE)
        self.button = wx.Button(self.panel, label="Send Matrix")
        self.button.Bind(wx.EVT_BUTTON, self.on_send_matrix)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND)
        self.sizer.Add(self.button, proportion=0, flag=wx.EXPAND)
        self.panel.SetSizer(self.sizer)
        self.Show()

    def on_send_matrix(self, event):
        matrix = np.random.rand(3, 3)  # Example of a random matrix
        self.text_ctrl.SetValue(str(matrix))

        # Send matrix to client
        host = '192.168.0.100'  # Replace with the IP address of the client PC
        port = 12345  # Choose a suitable port number
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(str(matrix).encode())

class Client(wx.Frame):
    def __init__(self, parent, title):
        super(Client, self).__init__(parent, title=title, size=(300, 200))
        self.panel = wx.Panel(self)
        self.text_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE)
        self.button = wx.Button(self.panel, label="Receive Matrix")
        self.button.Bind(wx.EVT_BUTTON, self.on_receive_matrix)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND)
        self.sizer.Add(self.button, proportion=0, flag=wx.EXPAND)
        self.panel.SetSizer(self.sizer)
        self.Show()

    def on_receive_matrix(self, event):
        host = '192.168.0.100'  # Replace with the IP address of the server PC
        port = 12345  # Choose the same port number used by the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            matrix_str = s.recv(1024).decode()
            try:
                matrix = np.array(eval(matrix_str))
                self.text_ctrl.SetValue(str(matrix))
            except:
                self.text_ctrl.SetValue("Invalid matrix format")

def main():
    app = wx.App()
    Server(None, "Server")
    Client(None, "Client")
    app.MainLoop()

if __name__ == '__main__':
    main()
