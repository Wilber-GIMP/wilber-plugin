import gtk
from os.path import dirname, join, realpath

from wilber_config import Config
from wilber_api import WilberAPIClient

class WilberConfigDialog(object):
    def __init__(self):
        self.dialog = gtk.Dialog(
            "Wilber Config",
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_OK)
        )
        self.config = Config()
        self.create_widgets()
        self.load_fields()

    def create_widgets(self):
        label_username = gtk.Label("Username:")
        label_password = gtk.Label("Password:")

        self.entry_username = gtk.Entry()
        self.entry_password = gtk.Entry()
        self.entry_password.set_visibility(False)

        table = gtk.Table()
        table.attach(label_username, 0, 1, 0, 1, False, False, 5, 5)
        table.attach(label_password, 0, 1, 1, 2, False, False, 5, 5)

        table.attach(self.entry_username, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, False, 5, 5)
        table.attach(self.entry_password, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, False, 5, 5)


        self.dialog.vbox.pack_start(table)


    def load_fields(self):
        self.entry_username.set_text(self.config.username)
        self.entry_password.set_text(self.config.password)

    def save_fields(self):
        self.username = self.entry_username.get_text()
        self.password = self.entry_password.get_text()

        self.config.set_username(self.username)

        self.config.set_password(self.password)

        token = self.login()
        if token:
            self.config.set_token(token)

        self.config.save()

    def login(self):
        api = WilberAPIClient()
        token = api.login(self.username, self.password)
        return token

    def run(self):
        self.dialog.show_all()
        response = self.dialog.run()

        if response == gtk.RESPONSE_OK:
            self.save_fields()

        self.dialog.destroy()

if __name__ == '__main__':
    dialog = WilberConfigDialog()
    result = dialog.run()
