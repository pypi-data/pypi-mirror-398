""" WX Frame displaying a PDF file """
import wx
import wx.lib.sized_controls as sc
from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel

from pathlib import Path

class PDFViewer(sc.SizedFrame):

    def __init__(self, parent, **kwargs):
        """ Initialize the PDF Viewer Frame """
        super(PDFViewer, self).__init__(parent, **kwargs)

        paneCont = self.GetContentsPane()
        self.buttonpanel = pdfButtonPanel(paneCont, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.buttonpanel.SetSizerProps(expand=True)

        self.viewer:pdfViewer
        self.viewer = pdfViewer(paneCont, wx.ID_ANY, wx.DefaultPosition,
                                wx.DefaultSize,
                                wx.HSCROLL|wx.VSCROLL|wx.SUNKEN_BORDER)

        self.viewer.SetSizerProps(expand=True, proportion=1)

        # introduce buttonpanel and viewer to each other
        self.buttonpanel.viewer = self.viewer
        self.viewer.buttonpanel = self.buttonpanel

        icon = wx.Icon()
        icon_path = Path(__file__).parent.parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)


    def load_pdf(self, pdf_path:str):
        """ Load a PDF file into the viewer """

        if not Path(pdf_path).exists():
            wx.MessageBox("PDF file does not exist.", "Error", wx.OK | wx.ICON_ERROR)
            return

        try:
            self.viewer.LoadFile(str(pdf_path))
        except Exception as e:
            wx.MessageBox("Failed to load PDF file.", "Error", wx.OK | wx.ICON_ERROR)

if __name__ == '__main__':
    import wx.lib.mixins.inspection as WIT
    app = WIT.InspectableApp(redirect=False)

    pdfV = PDFViewer(None)
    pdfV.load_pdf(Path(__file__).parent.parent.parent /'tests' / 'data' / 'pdf' / "dummy.pdf")  # Change to your PDF file path
    pdfV.Show()

    app.MainLoop()