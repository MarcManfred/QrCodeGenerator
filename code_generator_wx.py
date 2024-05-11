import wx
import os
import math
from PIL import Image
from code_generator import QrCodeGenerator
import wx.lib.scrolledpanel as scroller
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import time

FRAME_WIDTH = 1024
FRAME_HEIGHT = 800

BUTTON_WIDTH = 150
BUTTON_HEIGHT = 45

BUTTON_TEXT_WIDTH = 100
BUTTON_TEXT_HEIGHT = 30

LIST_BOX_URL_WIDTH = 275
LIST_BOX_URL_HEIGHT = 150

SCROLL_PANEL_WIDTH = 600
SCROLL_PANEL_HEIGHT = 400

TEXT_WIDTH = 300
TEXT_HEIGHT = 30

GAUGE_WIDTH = 600
GAUGE_HEIGHT = 25

IMG_WIDTH = 200
IMG_HEIGHT = 200


class QrWindow(wx.Frame):

    def __init__(self):
        super(QrWindow, self).__init__(None, title='QrWindow',
                                        size=(FRAME_WIDTH, FRAME_HEIGHT))
        
        self.panel = wx.Panel(self)
        self.timer = wx.Timer(self)

        self.dirname = ''
        self.url = ''
        self.path = None
        self.qr_code_color = '#000000'
        self.input_array = []
        self.url_index_array = []

        # Event to communicate with thread, cancel operation
        self.event = Event()

        # scroll_cnt for virtual size of scrolled panel
        self.scroll_cnt = 0
        
        self.CreateStatusBar()

        self.__create_menu()
        self.__create_scrollpanels()
        self.__create_buttons()
        self.__create_gauge()

        self.executor = ThreadPoolExecutor()
        
        self.Show(True)
        

    def __create_menu(self):
        # Setting up the menu
        filemenu = wx.Menu()

        menu_about = filemenu.Append(wx.ID_ABOUT, " About the game")
        menu_about.SetItemLabel("&About")
        filemenu.AppendSeparator()
        menu_exit = filemenu.Append(wx.ID_EXIT, "&Exit", " Exit the game")

        # Creating Menu Bar
        menu_bar = wx.MenuBar()
        menu_bar.Append(filemenu, "&Menu")
        self.SetMenuBar(menu_bar)

        # Set events
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)


    def __create_scrollpanels(self):
        text_pos_x = int(FRAME_WIDTH/2 - TEXT_WIDTH/2)
        button_pos_x = int(FRAME_WIDTH/2 + TEXT_WIDTH/2 + 10)
        list_box_x = int(FRAME_WIDTH/2 - 275/2)
        scroll_panel_x = int(FRAME_WIDTH/2 - 600/2)

        self.button_add = wx.Button(self.panel, -1, 'Add URL', pos=(button_pos_x, 0), size=(BUTTON_TEXT_WIDTH, BUTTON_TEXT_HEIGHT))
        self.button_add.Bind(wx.EVT_BUTTON, self.on_url_input)

        self.url_input = wx.TextCtrl(self.panel, -1, style = wx.TE_PROCESS_ENTER, pos=(text_pos_x, 0), size=(TEXT_WIDTH, TEXT_HEIGHT))
        self.url_input.Bind(wx.EVT_TEXT_ENTER, self.on_url_input)

        self.list_box_url = wx.ListBox(self.panel, -1, pos=(list_box_x, 50), size=(LIST_BOX_URL_WIDTH, LIST_BOX_URL_HEIGHT), style=wx.LB_MULTIPLE)
        self.list_box_url.Bind(wx.EVT_LISTBOX, self.on_url_select)

        self.scroll_panel = scroller.ScrolledPanel(self.panel, -1, pos=(scroll_panel_x, 300), size=(SCROLL_PANEL_WIDTH, SCROLL_PANEL_HEIGHT), style=wx.SIMPLE_BORDER)
        self.scroll_panel.SetupScrolling(scroll_x=False)
        self.scroll_panel.SetBackgroundColour('#FFFFFF')


    def __create_buttons(self):
        button_pos_x = int(FRAME_WIDTH/2 - BUTTON_WIDTH/2)

        self.button_image = wx.Button(self.panel, -1, 'Select image..', pos=(button_pos_x - 275, 225), size=(BUTTON_WIDTH, BUTTON_HEIGHT))
        self.button_image.Bind(wx.EVT_BUTTON, self.on_image)

        self.button_color = wx.Button(self.panel, -1, 'Choose color', pos=(button_pos_x - 100, 225), size=(BUTTON_WIDTH, BUTTON_HEIGHT))
        self.button_color.Bind(wx.EVT_BUTTON, self.on_color)
        
        self.button_qr = wx.Button(self.panel, -1, 'Create QR-Code', pos=(button_pos_x + 100, 225), size=(BUTTON_WIDTH, BUTTON_HEIGHT))
        self.button_qr.Bind(wx.EVT_BUTTON, self.on_qr)

        self.button_save = wx.Button(self.panel, -1, 'Save..', pos=(button_pos_x + 275, 225), size=(BUTTON_WIDTH, BUTTON_HEIGHT))
        self.button_save.Bind(wx.EVT_BUTTON, self.on_save)

    
    def __create_gauge(self):
        gauge_pos_x = int(FRAME_WIDTH/2 - GAUGE_WIDTH/2)
        self.gauge_label = wx.StaticText(self.panel, -1 , label ='Waiting for URL to process...', pos =(gauge_pos_x, 710), size=(300, 50))
        self.gauge_label.SetFont(wx.Font(15, wx.DEFAULT, wx.DEFAULT, wx.NORMAL))
        self.gauge = wx.Gauge(self.panel, -1, pos=(gauge_pos_x, 720), size=(GAUGE_WIDTH, GAUGE_HEIGHT), style=wx.GA_SMOOTH)
        self.button_cancel = wx.Button(self.panel, -1, 'Cancel', pos=(gauge_pos_x + 500, 705), size=(BUTTON_TEXT_WIDTH, BUTTON_TEXT_HEIGHT))
        self.button_cancel.Enable(False)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)

    
    def on_timer(self, e):
        self.gauge.SetValue(self.scroll_cnt)
        if self.scroll_cnt == len(self.url_index_array):
            self.timer.Stop()
            self.gauge_label.SetLabel('Finished !')
            # reenable button
            self.button_qr.Enable(True)
            self.button_cancel.Enable(False)

    def on_cancel(self, e):
        self.event.set()
        self.button_cancel.Enable(False)
        self.gauge_label.SetLabel('Cancelling Process...')


    def on_about(self, e):
        dlg = wx.MessageDialog(self, "A small text editor", "About Sample Editor", wx.OK)
        
        dlg.ShowModal()
        dlg.Destroy()
        

    def on_exit(self, e):
        self.Close(True)
        

    def on_url_input(self, e):
        self.url = self.url_input.GetValue()

        if self.url != '':
            self.list_box_url.Append(self.url)
            self.input_array.append(self.url)
            self.url_input.SetValue('')
            print(self.input_array)
        else:
            self.url_input.SetHint('Please enter an url.')
        

    def on_url_select(self, e):
        self.url_index_array = self.list_box_url.GetSelections()


    def on_image(self, e):
        """
        Open a file
        """
        dlg = wx.FileDialog(self, "Choose an image", self.dirname, "", "*.*", wx.FD_OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            
            self.path = os.path.join(self.dirname, self.filename)
            print(self.path)
            
        dlg.Destroy()


    def on_color(self, e):
        dlg = wx.ColourDialog(self)

        # SetChooseFull for extended windows visualization
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            self.qr_code_color = dlg.GetColourData().GetColour().GetAsString(wx.C2S_HTML_SYNTAX)

        print(self.qr_code_color)
        print(type(self.qr_code_color))


    def on_qr(self, e):
        bitmaps = self.scroll_panel.GetChildren()
        
        # deleting bitmaps on redraw
        for bitmap in bitmaps:
            bitmap.Destroy()

        if len(self.url_index_array) != 0:
            self.scroll_cnt = 0
            self.gauge.SetRange(len(self.url_index_array))
            self.Bind(wx.EVT_TIMER, self.on_timer)
            # Restarts timer every 100 milliseconds
            self.timer.Start(100)
            self.gauge_label.SetLabel('Processing...')

            # disabling qr button --> no new threads
            self.button_qr.Enable(False)

            self.button_cancel.Enable(True)
            
            self.future = self.executor.submit(self.generate_qr, self.event)
        else:
            wx.MessageBox('Please select one or more urls.', 'Hint', wx.OK|wx.ICON_INFORMATION)


    def generate_qr(self, event):
        x_cnt = 0
        y_cnt = 0

        scroll_cnt = 0

        for index in self.url_index_array:
            if event.is_set():
                event.clear()
                self.timer.Stop()
                self.gauge_label.SetLabel('Cancelled Process...')
                self.button_qr.Enable(True)

                return
                

            code_generator = QrCodeGenerator(url=self.input_array[index],
                                            image_path=self.path if self.path is not None else None,
                                            qr_color=self.qr_code_color if self.qr_code_color is not None else None)

            qr_code = code_generator.generate_code()
                
            # Convert PIL image to wxPython Image
            qr_image = wx.Image(qr_code.size[0], qr_code.size[1])
            qr_image.SetData(qr_code.convert("RGB").tobytes())

            # Scale the image and convert it to a bitmap
            scaled_image = qr_image.Scale(IMG_WIDTH, IMG_HEIGHT, wx.IMAGE_QUALITY_HIGH)
            scaled_bitmap = wx.Bitmap(scaled_image)

            # Display the wxPython image
            wx.StaticBitmap(self.scroll_panel, bitmap=scaled_bitmap, pos=(IMG_WIDTH * x_cnt, IMG_HEIGHT * y_cnt))

            x_cnt += 1
            self.scroll_cnt += 1

            if x_cnt % 3 == 0:
                y_cnt += 1
                x_cnt = 0
        
            
            print(f'Done Generating...{index}')

        # Setting the height of scroll panel
        self.scroll_panel.SetVirtualSize((IMG_WIDTH, (IMG_HEIGHT * math.ceil(self.scroll_cnt / 3))))
    

    def on_save(self, e):
        bitmaps = self.scroll_panel.GetChildren()
        img_list = []

        for bitmap in bitmaps:
            img_list.append(bitmap.GetBitmap())


        with wx.FileDialog(self, "Save Images",
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:

            if dlg.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            pathname = dlg.GetPath()
            filename = dlg.GetFilename()
            i = 0

             # save the current contents in the file
            try:
                if len(img_list) > 1:
                    os.makedirs(pathname)
                    os.chdir(pathname)
                    for img in img_list:
                        img.SaveFile(self.input_array[i] + '_' + str(i) + '.png', wx.BITMAP_TYPE_PNG)
                        i += 1
                else:
                    img_list[0].SaveFile(filename + '.png', wx.BITMAP_TYPE_PNG)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    

if __name__ == '__main__':
    app = wx.App()
    frame = QrWindow()
    app.MainLoop()
