"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
import logging

class Times_Selection(wx.Dialog):
    """
    Boîte de dialogue permettant de sélectionner un temps parmi une liste de temps donnée.

    Plueisurs listes de temps sont affichées, et l'utilisateur doit en sélectionner un dans chaque liste.

    """

    def __init__(self, parent, id, title, size=(300, 200), times:list[list[float]] = None, callback = None):
        """ Initialisation de la boîte de dialogue """

        wx.Dialog.__init__(self, parent.parent, id, title, size=size)

        self.parent = parent

        self.times = times

        self.InitUI()

        self._callback = callback # fonction à appeler lorsque l'utilisateur a sélectionné deux temps

        self.Centre()
        self.Show()

    def InitUI(self):
        """
        Initialisation de l'interface graphique

        Plusieurs listboxes sont affichées côte-à-côte, chacune contenant une liste de temps.
        Deux boutons sont affichés en bas de la boîte de dialogue.

        """

        panel = wx.Panel(self)

        # Sizer de placement vertical
        sizer = wx.BoxSizer(wx.VERTICAL)

        # sizer de placement horizontal pour les listes de temps
        sizerlist = wx.BoxSizer(wx.HORIZONTAL)

        # listes de temps
        self.lb = []
        for cur in self.times:

            sizer_t = wx.BoxSizer(wx.VERTICAL)

            self.lb.append((wx.CheckBox(panel, -1, "Fix"), wx.ListBox(panel, -1, choices = [str(curtime) for curtime in cur], style = wx.LB_SINGLE)))

            sizer_t.Add(self.lb[-1][0], 1, wx.EXPAND)
            sizer_t.Add(self.lb[-1][1], 10, wx.EXPAND)

            sizerlist.Add(sizer_t, 1, wx.EXPAND)

        sizer.Add(sizerlist, 1, wx.EXPAND)

        # boutons
        button4 = wx.Button(panel, label="Previous", size=(90, 10))
        button1 = wx.Button(panel, label="Apply", size=(90, 10))
        button3 = wx.Button(panel, label="Next", size=(90, 10))
        button2 = wx.Button(panel, label="Last", size=(90, 10))

        # sizer de placement horizontal pour les boutons
        sizerbut = wx.BoxSizer(wx.HORIZONTAL)

        sizerbut.Add(button4, 1, wx.EXPAND)
        sizerbut.Add(button1, 1, wx.EXPAND)
        sizerbut.Add(button3, 1, wx.EXPAND)
        sizerbut.Add(button2, 1, wx.EXPAND)

        sizer.Add(sizerbut, 1, wx.EXPAND)

        panel.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_BUTTON, self.OnLast, id=button2.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnApply, id=button1.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnNext, id=button3.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnPrevious, id=button4.GetId())

    def callback(self):

        idx = [curlb[1].GetSelection() for curlb in self.lb]

        self._callback(idx)

    def OnNext(self, e):
        """
        Appelée lorsque l'utilisateur clique sur le bouton "Next".

        """
        logging.debug("Times_Selection.OnNext")

        for curlb in self.lb:
            if not curlb[0].IsChecked():
                curlb[1].Select(min(curlb[1].GetCount()-1, curlb[1].GetSelection()+1))

        self.callback()

    def OnPrevious(self, e):
        """
        Appelée lorsque l'utilisateur clique sur le bouton "Previous".

        """
        logging.debug("Times_Selection.OnPrevious")

        for curlb in self.lb:
            if not curlb[0].IsChecked():
                curlb[1].Select(max(0, curlb[1].GetSelection()-1))

        self.callback()

    def OnApply(self, e):
        """
        Appelée lorsque l'utilisateur clique sur le bouton "Apply".

        Appelle la fonction de callback avec les deux temps sélectionnés.

        """
        logging.debug("Times_Selection.OnApply")
        self.callback()

    def OnLast(self, e):
        """
        Appelée lorsque l'utilisateur clique sur le bouton "Last".

        Ferme la boîte de dialogue.

        """
        logging.debug("Times_Selection.OnLast")
        self.callback([-1]*len(self.times))

    def update_times(self, times:list[list[float]]):
        """
        Met à jour les listes de temps affichées dans la boîte de dialogue.

        """
        assert len(times) == len(self.times), "Times_Selection.update_times: len(times) != len(self.times)"

        self.times = times
        for cur, curlb in zip(self.times, self.lb):
            curlb[1].Set([str(curtime) for curtime in cur])

    def get_times_idx(self):
        """
        Retourne les index des temps sélectionnés dans les listes de temps.

        """
        return [curlb[1].GetSelection() for curlb in self.lb]