import gtk
from gtk.gdk import Pixbuf, pixbuf_new_from_stream, pixbuf_new_from_file_at_size


from wilber_plugin import WilberPlugin
from wilber_gui_upload import WilberUploadDialog
from wilber_gui_config import WilberConfigDialog



class WilberGui(object):
    def __init__(self, settings):
        self.settings = settings
        self.plugin = WilberPlugin(settings)
        self.window = gtk.Window()
        self.window.set_title("Wilber Asset Manager")
        windowicon = self.window.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.window.set_icon(windowicon)

        #self.image_size = self.settings.get_image_size()
        self.image_size = 100#self.settings.get_image_size()


        self.create_widgets()
        self.window.connect("destroy", gtk.mainquit);

        self.connect_signals()

        self.window.show_all()


        gtk.main()


    def create_widgets(self):
        self.vbox = gtk.VBox(spacing=10)

        self.hbox_1 = gtk.HBox(spacing=10)
        self.label = gtk.Label("Search:")
        self.hbox_1.pack_start(self.label, False)
        self.entry = gtk.Entry()
        self.hbox_1.pack_start(self.entry)

        self.button_config = gtk.Button("Config")
        self.hbox_1.pack_start(self.button_config)

        self.hbox_2 = gtk.HButtonBox()
        self.button_exit = gtk.Button("Exit")
        self.button_upload = gtk.Button("Upload")

        self.hbox_2.pack_start(self.button_upload)
        self.hbox_2.pack_start(self.button_exit)


        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_size_request(480, 480)
        view_port = gtk.Viewport()

        self.table = gtk.Table(rows=7, columns=3)

        for row, asset in enumerate(self.plugin.get_assets()):
            name = asset['name']

            image = gtk.Image()
            try:
                pixbuf = pixbuf_new_from_file_at_size(asset['image_path'], self.image_size, self.image_size)
                image.set_from_pixbuf(pixbuf)
            except Exception as e:
                print(e)

            button = gtk.Button('Download')
            button.connect("clicked", self.download_asset, asset)

            self.table.attach(image, 0, 1, row, row+1, False, False)
            self.table.attach(gtk.Label(name), 1 , 2, row, row+1, False, False)
            self.table.attach(button, 2,3, row, row+1, False, False)

        view_port.add(self.table)
        scrolled_window.add(view_port)


        self.vbox.pack_start(self.hbox_1, False, False,)
        self.vbox.pack_start(scrolled_window, True, True)
        self.vbox.pack_start(self.hbox_2, False, False)

        self.window.add(self.vbox)

    def window_upload(self):
        print("show")
        #self.dialog_upload = gtk_dialog_new_with_buttons('Upload', self.window)

        #self.dialog_upload.show()

        WilberUploadDialog()

    def window_config(self):
        config_dialog = WilberConfigDialog()
        return config_dialog


    def download_asset(self, button, asset):
        self.plugin.download_asset(asset)

    def connect_signals(self):
        self.button_exit.connect("clicked", self.callback_exit)
        self.button_upload.connect("clicked", self.callback_upload)
        self.button_config.connect("clicked", self.callback_show_config)


    def callback_ok(self, widget, callback_data=None):
        name = self.entry.get_text()

    def callback_upload(self, widget, callback_data=None):
        dialog = WilberUploadDialog(self.plugin.get_gimp_folder())
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            print("Do UPLOAD")
            filename = dialog.get_filename()
            self.plugin.put_asset(name="Xuxu", file=filename, image=filename, desc="YES", category='brushes')

        dialog.destroy()
        print("RESPONSE=",response)

    def callback_exit(self, widget, callback_data=None):
        gtk.main_quit()

    def callback_show_config(self, widget, callback_data=None):
        dialog = self.window_config()
        response = dialog.run()

        if response==gtk.RESPONSE_ACCEPT:
            self.settings.set_username(self.entry_username.get_text())
            self.settings.set_password(self.entry_password.get_text())
            self.settings.save()

        dialog.destroy()





if __name__ == '__main__':

    class Settings(object):
        pass

    settings = Settings()
    settings.get_username = lambda:'x'
    settings.get_password = lambda:'x'
    dialog = WilberGui(settings)
    result = dialog.run()
