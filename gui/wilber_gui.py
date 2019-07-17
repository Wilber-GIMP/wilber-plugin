import gtk
import glib
from gtk.gdk import Pixbuf, pixbuf_new_from_stream, pixbuf_new_from_file_at_size

from wilber_common import ASSET_TYPE_TO_CATEGORY
from wilber_plugin import WilberPlugin
from wilber_gui_upload import WilberUploadDialog
from wilber_gui_config import WilberConfigDialog
from wilber_config import Config


assets_cache = {}


class WilberGui(object):
    def __init__(self, gimp_directory):
        self.settings = Config()
        self.gimp_directory = gimp_directory
        self.plugin = WilberPlugin(self.settings)
        self.window = gtk.Window()
        self.window.set_title("Wilber Asset Manager")
        windowicon = self.window.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.window.set_icon(windowicon)

        #self.image_size = self.settings.get_image_size()
        self.image_size = 100#self.settings.get_image_size()


        self.create_widgets()
        self.update_asset_listing()

        self.window.connect("destroy", gtk.mainquit);

        self.connect_signals()

        self.window.show_all()
        self.hide_status()

        gtk.main()


    def category_changed(self, *argss):
        self.plugin.current_asset_type = self.category_dropdown.get_active_text()
        self.update_asset_listing()

    def create_widgets(self):
        self.vbox = gtk.VBox(spacing=10)

        self.status_bar = gtk.Label("")
        self.vbox.pack_start(self.status_bar)

        self.category_dropdown = gtk.combo_box_new_text()
        for asset_type in ASSET_TYPE_TO_CATEGORY.keys():
            self.category_dropdown.append_text(asset_type)

        self.category_dropdown.connect("changed", self.category_changed)
        self.vbox.pack_start(self.category_dropdown)


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


        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_size_request(480, 480)



        #self.view_port = view_port = gtk.Viewport()
        #self.scrolled_window.add(view_port)


        self.model_assets = gtk.ListStore(int, gtk.gdk.Pixbuf, str, bool)


        self.treeview = gtk.TreeView(model=self.model_assets)
        self.scrolled_window.add(self.treeview)

        cell1 = gtk.CellRendererPixbuf()
        cell2 = gtk.CellRendererText()
        cell3 = gtk.CellRendererToggle()
        #cell3.set_activatable(True)
        cell3.connect("toggled", self.install_asset)
        #cell3.set_property("activatable", True)

        col1 = gtk.TreeViewColumn('Image', cell1, pixbuf=1)
        col2 = gtk.TreeViewColumn('Name' , cell2, text=2)
        col2.set_expand(True)
        col3 = gtk.TreeViewColumn('Installed' , cell3, active=3)
        col3.set_clickable(True)

        self.treeview.append_column(col1)
        self.treeview.append_column(col2)
        self.treeview.append_column(col3)


        self.vbox.pack_start(self.hbox_1, False, False,)
        self.vbox.pack_start(self.scrolled_window, True, True)
        self.vbox.pack_start(self.hbox_2, False, False)

        self.window.add(self.vbox)

    def install_asset(self, cell, row):


        asset_id = self.model_assets[int(row)][0]
        self.download_asset(assets_cache[asset_id])


        #v = self.model_assets[int(row)][3]
        self.model_assets[int(row)][3] = True

    def update_asset_listing(self):


        assets = self.plugin.get_assets()
        print(assets[0])
        self.model_assets.clear()

        for row, asset in enumerate(assets):
            assets_cache[asset['id']] = asset
            name = asset['name']
            id = asset['id']

            try:
                pixbuf = pixbuf_new_from_file_at_size(asset['image_path'], self.image_size, self.image_size)

            except Exception as e:
                print(e)

            self.model_assets.append([id, pixbuf, name, False])



    def download_asset(self, asset):
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
        dialog = WilberUploadDialog(self.gimp_directory)

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





if __name__ == '__main__':

    class Settings(object):
        pass

    settings = Settings()
    settings.get_username = lambda:'x'
    settings.get_password = lambda:'x'
    dialog = WilberGui(settings)
    result = dialog.run()
