import wx
import wx.grid
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class DictGrid(wx.Dialog):

    def __init__(self, parent, id, data: dict[dict]):

        super().__init__(parent, title=f"Edit: {id}", size=(600, 400))

        self.data = data

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Create the grid
        self.grid = wx.grid.Grid(self)

        first_elem = next(iter(data.values()))
        self.grid.CreateGrid(len(data)+1, len(list(first_elem.keys()))+1)

        # Set column labels
        for col, colname in enumerate(first_elem.keys()):
            self.grid.SetColLabelValue(col+1, str(colname))

        # Fill grid and make cells read-only
        for row, vals in data.items():
            for col, colname in enumerate(first_elem.keys()):
                val = str(vals[colname])
                self.grid.SetCellValue(row+1, col+1, val)
                # self.grid.SetReadOnly(row, col, True)

        vbox.Add(self.grid, 1, wx.EXPAND | wx.ALL, 10)

        # Add a button to show histogram
        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self._ok_button = wx.Button(self, label="OK")
        self._cancel_button = wx.Button(self, label="Cancel")
        sizer_buttons.Add(self._ok_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        sizer_buttons.Add(self._cancel_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self._ok_button.Bind(wx.EVT_BUTTON, self.OnOk)
        self._cancel_button.Bind(wx.EVT_BUTTON, self.Close)

        vbox.Add(sizer_buttons, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        self.SetSizer(vbox)

    def get_dict(self):
        """ Return the data as a dictionary. """
        new_data = {}
        for row in range(1, self.grid.GetNumberRows()):
            new_data[row] = {}
            for col in range(1, self.grid.GetNumberCols()):
                colname = self.grid.GetColLabelValue(col)
                new_data[row][colname] = self.grid.GetCellValue(row, col)
        return new_data

    def OnOk(self, event):
        """ Handle the OK button click. """
        # Here you can implement logic to save changes if needed
        # For now, we just close the dialog
        self.Hide()

    def Close(self, event=None):
        """ Close the dialog. """
        self.Destroy()
class PandasGrid(wx.Dialog):

    def __init__(self, parent, id, df: pd.DataFrame):
        super().__init__(parent, title=f"DataFrame characteristics: {id}", size=(600, 400))

        self.df = df

        vbox = wx.BoxSizer(wx.VERTICAL)

        # Create the grid
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(df.shape[0], df.shape[1])

        # Set column labels
        for col, colname in enumerate(df.columns):
            self.grid.SetColLabelValue(col, str(colname))

        # Fill grid and make cells read-only
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                val = str(df.iloc[row, col])
                self.grid.SetCellValue(row, col, val)
                self.grid.SetReadOnly(row, col, True)

        vbox.Add(self.grid, 1, wx.EXPAND | wx.ALL, 10)

        # Add a button to show histogram
        self.hist_button = wx.Button(self, label="Histogram")
        self.hist_button.Bind(wx.EVT_BUTTON, self.OnShowHistogram)
        vbox.Add(self.hist_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.SetSizer(vbox)

    def OnShowHistogram(self, event):
        selected_cols = self.grid.GetSelectedCols()
        if not selected_cols:
            wx.MessageBox("Please select a column to plot.", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        col_idx = selected_cols[0]
        colname = self.df.columns[col_idx]
        data = pd.to_numeric(self.df[colname], errors='coerce').dropna()

        if data.empty:
            wx.MessageBox(f"No numeric data in column '{colname}'", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        # Calcul de l'histogramme sans affichage
        counts, bins = np.histogram(data, bins=20)
        probabilities = counts / counts.sum()*100  # Normalisation

        # Plot manuel
        plt.figure(figsize=(6, 4))
        plt.bar(bins[:-1], probabilities, width=np.diff(bins), align='edge',
                color='skyblue', edgecolor='black')
        plt.title(f"Histogram of {colname}")
        plt.xlabel(colname)
        plt.ylabel("Probability [%]")
        plt.grid(visible=True)
        plt.tight_layout()
        plt.show()