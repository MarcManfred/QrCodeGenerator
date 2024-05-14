"""
    This script generates QR codes from URLs and an optional image.
    The QR codes are displayed in a wxPython GUI.
    
"""

import wx
from io import BytesIO
from code_generator import QrCodeGenerator
import threading

class QrCodeApp(wx.App):
    def OnInit(self):
        self.frame = wx.Frame(None, title='QR Code Generator')
        self.panel = wx.Panel(self.frame)

        self.url_label = wx.StaticText(self.panel, label='URLs:')
        self.url_text_ctrl = wx.TextCtrl(self.panel)

        self.qr_color_label = wx.StaticText(self.panel, label='QR Color:')
        self.qr_color_picker = wx.ColourPickerCtrl(self.panel)

        self.image_button = wx.Button(self.panel, label='Select Image')
        self.image_button.Bind(wx.EVT_BUTTON, self.on_select_image)

        self.generate_button = wx.Button(self.panel, label='Generate')
        self.generate_button.Bind(wx.EVT_BUTTON, self.on_generate)

        self.save_button = wx.Button(self.panel, label='Save')
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)
        self.save_button.Disable()

        self.qr_bitmaps = []
        self.qr_images = []
        self.qr_sizer_items = []

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.url_label, 0, wx.LEFT, 5)
        self.sizer.Add(self.url_text_ctrl, 0, wx.LEFT | wx.RIGHT, 5)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.qr_color_label, 0, wx.LEFT, 5)
        self.sizer.Add(self.qr_color_picker, 0, wx.LEFT | wx.RIGHT, 5)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.image_button, 0, wx.LEFT | wx.RIGHT, 5)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.generate_button, 0, wx.LEFT | wx.RIGHT, 5)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.save_button, 0, wx.LEFT | wx.RIGHT, 5)
        self.sizer.AddSpacer(10)

        self.selected_image_path = None

        self.panel.SetSizerAndFit(self.sizer)
        self.frame.Show()
        return True

    def on_generate(self, event):
        urls = self.url_text_ctrl.GetValue().split(';')
        qr_color = self.qr_color_picker.GetColour().GetAsString(wx.C2S_HTML_SYNTAX)

        self.qr_bitmaps = []
        self.qr_images = []

        for url in urls:
            threading.Thread(target=self.generate_qr_code, args=(url, qr_color)).start()

    def generate_qr_code(self, url, qr_color):
        generator = QrCodeGenerator(url, self.selected_image_path, qr_color)
        qr_image = generator.generate_code()

        image_stream = BytesIO()
        qr_image.save(image_stream, format='PNG')
        image_stream.seek(0)
        wx_image = wx.Image(image_stream)

        wx_image = wx_image.Scale(200, 200, wx.IMAGE_QUALITY_HIGH)
        wx.CallAfter(self.display_qr_code, wx.Bitmap(wx_image), qr_image)

    def display_qr_code(self, qr_bitmap, qr_image):
        self.qr_bitmaps.append(wx.StaticBitmap(self.panel, bitmap=qr_bitmap))
        self.qr_images.append(qr_image)
        self.qr_sizer_items.append(self.sizer.Add(self.qr_bitmaps[-1]))
        self.panel.SetSizerAndFit(self.sizer)
        self.save_button.Enable()

    def on_save(self, event):
        for qr_image in self.qr_images:
            with wx.FileDialog(self.frame, "Save QR code as PNG", wildcard="PNG files (*.png)|*.png",
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                pathname = fileDialog.GetPath()
                try:
                    qr_image.save(pathname)
                except IOError:
                    wx.LogError("Cannot save current data in file '%s'." % pathname)

    def on_select_image(self, event):
        with wx.FileDialog(self.frame, "Select an image file", wildcard="Image files (*.jpg;*.png)|*.jpg;*.png",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.selected_image_path = fileDialog.GetPath()

if __name__ == '__main__':
    app = QrCodeApp()
    app.MainLoop()
