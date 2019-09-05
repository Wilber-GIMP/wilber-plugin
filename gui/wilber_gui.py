from os.path import basename,join
import logging
import gtk
import glib
from gtk.gdk import Pixbuf, pixbuf_new_from_stream, pixbuf_new_from_file_at_size

from wilber_common import Asset, ASSET_TYPE_TO_CATEGORY
from wilber_plugin import WilberPlugin
from wilber_gui_upload import WilberUploadDialog
from wilber_gui_config import WilberConfigDialog
from wilber_config import Config
from wilber_log import logger

logger = logging.getLogger('wilber.gui')

class WilberGui(object):
    def __init__(self, gimp_directory):
        self.settings = Config()
        self.gimp_directory = gimp_directory
        self.plugin = WilberPlugin(self.settings)
        Asset.plugin = self.plugin

        self.window = gtk.Window()
        self.window.set_title("Wilber Asset Manager")
        windowicon = self.window.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.window.set_icon(windowicon)

        self.image_size = self.settings.get_image_size()
        #self.image_size = 100#self.settings.get_image_size()


        self.create_widgets()



        self.window.connect("destroy", gtk.mainquit);

        self.connect_signals()

        self.window.show_all()
        self.hide_status()

        self.category_changed()
        gtk.main()


    def category_changed(self, *argss):
        self.plugin.current_asset_type = self.category_dropdown.get_active_text()
        self.load_assets(clear=True)

    def create_widgets(self):
        self.vbox = gtk.VBox(spacing=10)

        self.status_bar = gtk.Label("")
        self.vbox.pack_start(self.status_bar)

        self.category_dropdown = gtk.combo_box_new_text()
        for asset_type in ASSET_TYPE_TO_CATEGORY.keys():
            self.category_dropdown.append_text(asset_type)
        self.category_dropdown.set_active(0)
        self.category_dropdown.connect("changed", self.category_changed)



        self.hbox_1 = gtk.HBox(spacing=10)
        self.label = gtk.Label("Search:")
        self.hbox_1.pack_start(self.label, False)
        self.entry_search = gtk.Entry()
        self.hbox_1.pack_start(self.entry_search)

        self.button_config = gtk.Button("Login")
        self.hbox_1.pack_start(self.category_dropdown)

        self.hbox_2 = gtk.HButtonBox()
        self.button_exit = gtk.Button("Exit")
        self.button_upload = gtk.Button("Upload")
        self.button_more = gtk.Button("More")
        self.button_more.set_sensitive(False)

        self.hbox_2.pack_start(self.button_config)
        self.hbox_2.pack_start(self.button_upload)
        self.hbox_2.pack_start(self.button_more)
        self.hbox_2.pack_start(self.button_exit)


        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_size_request(480, 480)


        self.model_assets = gtk.ListStore(int, gtk.gdk.Pixbuf, str, bool)


        self.treeview = gtk.TreeView(model=self.model_assets)
        self.scrolled_window.add(self.treeview)

        cell1 = gtk.CellRendererPixbuf()
        cell2 = gtk.CellRendererText()
        cell3 = gtk.CellRendererToggle()
        #cell3.set_activatable(True)
        cell3.connect("toggled", self.toggle_asset)
        #cell3.set_property("activatable", True)

        col1 = gtk.TreeViewColumn('Image', cell1, pixbuf=1)
        col2 = gtk.TreeViewColumn('Name' , cell2, text=2)
        col2.set_expand(True)
        col3 = gtk.TreeViewColumn('Installed' , cell3, active=3)
        col3.set_clickable(True)

        self.treeview.append_column(col1)
        self.treeview.append_column(col2)
        self.treeview.append_column(col3)

        self.treeview.set_search_column(2)

        self.vbox.pack_start(self.hbox_1, False, False,)
        self.vbox.pack_start(self.scrolled_window, True, True)
        self.vbox.pack_start(self.hbox_2, False, False)

        self.window.add(self.vbox)


    def toggle_asset(self, cell, row):
        asset_id = self.model_assets[int(row)][0]
        is_installed = Asset.get(asset_id).is_installed()
        if is_installed:
            self.remove_asset(asset_id)
        else:
            self.install_asset(asset_id)

        self.model_assets[int(row)][3] = not is_installed

    def remove_asset(self, asset_id):
        asset = Asset.get(asset_id)
        self.set_status("Removing '%s' " % asset.name, timeout=None)
        self.plugin.remove_asset(Asset.get_asset(asset_id))

        self.set_status("Asset '%s' removed" % asset.name, timeout=5000)

    def install_asset(self, asset_id):
        asset = Asset.get(asset_id)

        self.set_status("Downloading '%s' " % asset.name, timeout=None)
        self.plugin.download_asset(asset.dic)
        self.hide_status()
        self.set_status("Asset '%s' downloaded" % asset.name, timeout=5000)


    def load_assets(self, query=None, clear=False, more=False):
        if more:
            assets, has_more = self.plugin.get_assets(more=more)
        elif query:
            assets, has_more = self.plugin.get_assets(query=query)
        else:
            assets, has_more = self.plugin.get_assets()
        if assets:
            if clear:
                self.model_assets.clear()
            self.update_asset_listing(assets)

            if has_more:
                self.button_more.set_sensitive(True)
            else:
                self.button_more.set_sensitive(False)


    def update_asset_listing(self, assets):
        for row, asset_dic in enumerate(assets):
            asset = Asset(asset_dic)
            try:
                pixbuf = pixbuf_new_from_file_at_size(asset.image_path, self.image_size, self.image_size)
            except Exception as e:
                print(e)
            is_installed = asset.is_installed()
            self.model_assets.append([asset.id, pixbuf, asset.name, is_installed])






    def connect_signals(self):
        self.button_exit.connect("clicked", self.callback_exit)
        self.button_upload.connect("clicked", self.callback_upload)
        self.button_config.connect("clicked", self.callback_show_config)
        self.entry_search.connect("activate", self.callback_search)

        self.button_more.connect("clicked", self.callback_load_more)

    def callback_search(self, widget, callback_data=None):
        query = self.entry_search.get_text()
        self.load_assets(query)

    def callback_load_more(self, widget):
        logger.info("Load More")
        self.load_assets(more=True)

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
        if response not in (gtk.RESPONSE_OK, gtk.RESPONSE_ACCEPT):
            self.set_status("Upload canceled", 3500)
            return
        #response_ok = self.plugin.sanitize_response(response_data)
        #if not response_ok:
        #    self.set_status("Incorrect or insuficient data to upload", 1500)
        #    return

        self.set_status("Uploading asset '%s' " % response_data["name"], timeout=None)

        upload_response = self.plugin.upload_asset(**response_data)

        #upload_response = self.plugin.api.put_asset(**response_data)
        self.hide_status()
        if upload_response.status_code < 399:
            self.set_status("Asset '%s' uploaded successfuly" % response_data["name"], 5000)
        else:
            self.set_status("Error in uploading asset - HTTP code: '%s'" % upload_response.status_code, 5000)

    def callback_exit(self, widget, callback_data=None):
        gtk.main_quit()

    def callback_show_config(self, widget, callback_data=None):
        dialog = WilberConfigDialog()
        response = dialog.run()

        if response==gtk.RESPONSE_ACCEPT:
            self.settings.set_username(self.entry_username.get_text())
            self.settings.set_password(self.entry_password.get_text())
            self.settings.save()





if __name__ == '__main__':

    from os.path import expanduser
    dialog = WilberGui(gimp_directory=expanduser('~/.config/GIMP/2.10'))
    #result = dialog.run()
