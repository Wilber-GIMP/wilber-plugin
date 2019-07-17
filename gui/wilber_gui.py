# coding: utf-8
from __future__ import print_function, unicode_literals, division

import glib
import gtk
# from gtk.gdk import Pixbuf, pixbuf_new_from_stream
from gtk.gdk import pixbuf_new_from_file_at_size


from wilber_plugin import WilberPlugin
from wilber_gui_upload import WilberUploadDialog


try:
    import gimp
except ImportError:
    # Only used when debugging the UI
    class gimp(object):
        directory = "."


class WilberConfigDialog(gtk.Dialog):
    def __init__(self, settings):
        dialog = gtk.Dialog(
            "Wilber Config",
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        )

        label_username = gtk.Label("Username:")
        entry_username = gtk.Entry()

        label_password = gtk.Label("Password:")
        entry_password = gtk.Entry()
        entry_password.set_visibility(False)
        entry_password.set_invisible_char("*")

        entry_username.set_text(settings.username)
        entry_password.set_text(settings.password)

        dialog.vbox.pack_start(label_username)
        dialog.vbox.pack_start(entry_username)
        dialog.vbox.pack_start(label_password)
        dialog.vbox.pack_start(entry_password)
        #label.show()
        #entry.show()
        checkbox = gtk.CheckButton("Useless checkbox")
        #dialog.action_area.pack_end(checkbox)
        checkbox.show()
        dialog.show_all()


class WilberGui(object):
    def __init__(self, settings):
        self.settings = settings
        self.plugin = WilberPlugin(settings)
        self.window = gtk.Window()
        self.window.set_title("Wilber Asset Manager")
        windowicon = self.window.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.window.set_icon(windowicon)

        self.image_size = self.settings.get_image_size()
        self.create_widgets()
        self.window.connect("destroy", gtk.mainquit);

        self.connect_signals()

        self.window.show_all()
        self.hide_status()

        gtk.main()


    def create_widgets(self):
        self.vbox = gtk.VBox(spacing=10)

        self.status_bar = gtk.Label("")
        self.vbox.pack_start(self.status_bar)

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

            self.table.attach(image, 0, 1, row, row+1, False, False, xpadding=6)
            self.table.attach(gtk.Label(name), 1 , 2, row, row+1, False, False, xpadding=6)
            self.table.attach(button, 2,3, row, row+1, False, False, xpadding=6)

        view_port.add(self.table)
        scrolled_window.add(view_port)


        self.vbox.pack_start(self.hbox_1, False, False,)
        self.vbox.pack_start(scrolled_window, True, True)
        self.vbox.pack_start(self.hbox_2, False, False)

        self.window.add(self.vbox)


    def window_config(self):

        dialog = gtk.Dialog("Wilber Config",
                   self.window,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        label_username = gtk.Label("Username:")
        entry_username = gtk.Entry()

        label_password = gtk.Label("Password:")
        entry_password = gtk.Entry()
        entry_password.set_visibility(False)

        entry_username.set_text(self.settings.get_username())
        entry_password.set_text(self.settings.get_password())

        self.entry_username = entry_username
        self.entry_password = entry_password

        dialog.vbox.pack_start(label_username)
        dialog.vbox.pack_start(entry_username)
        dialog.vbox.pack_start(label_password)
        dialog.vbox.pack_start(entry_password)
        #label.show()
        #entry.show()
        checkbox = gtk.CheckButton("Useless checkbox")
        #dialog.action_area.pack_end(checkbox)
        checkbox.show()
        dialog.show_all()
        return dialog


    def download_asset(self, button, asset):
        self.set_status("Downloading '%s' " % asset["name"], timeout=None)
        self.plugin.download_asset(asset)
        self.hide_status()
        self.set_status("Asset '%s' downloaded" % asset["name"], timeout=5000)

    def connect_signals(self):
        self.button_exit.connect("clicked", self.callback_exit)
        self.button_upload.connect("clicked", self.callback_upload)
        self.button_config.connect("clicked", self.callback_show_config)


    def callback_ok(self, widget, callback_data=None):
        name = self.entry.get_text()
        print(name)

    def set_status(self, message, timeout=3000):
        self.status_bar.set_text(message)
        self.status_bar.show()
        if timeout:
            glib.timeout_add(timeout, self.hide_status, None)

    def hide_status(self, *args):
        self.status_bar.hide()

    def callback_upload(self, widget, callback_data=None):
        dialog = WilberUploadDialog(gimp.directory)
        # embed()
        #dialog = gtk_file_chooser_dialog_new('Upload', self.window)
        response, response_data = dialog.run()
        if  response not in (gtk.RESPONSE_OK, gtk.RESPONSE_ACCEPT):
            self.set_status("Upload canceled", 1500)
        response_ok = self.plugin.sanitize_response(response_data)
        if not response_ok:
            self.set_status("Incorrect or insuficient data to upload", 1500)
            return

        self.set_status("Uploading asset '%s' " % response_data["name"], timeout=None)
        upload_response = self.plugin.api.put_asset(**response_data)
        self.hide_status()
        if upload_response.status_code < 399:
            self.set_status("Asset '%s' uploaded successfuly" % response_data["name"], 5000)
        else:
            self.set_status("Error in uploading asset - HTTP code: '%s'" % upload_response.status_code, 5000)

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
