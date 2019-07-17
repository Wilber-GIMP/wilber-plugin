import gtk

from wilber_api import WilberAPIClient


class WilberUploadDialog(object):
    def __init__(self, folder):


        self.dialog = gtk.Dialog(
            "Wilber Upload",
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_OK))

        self.create_widgets()

        self.image_filename = None


        self.api = WilberAPIClient()
        self.connect_signals()
        self.dialog.connect("destroy", self.destroy)
        self.dialog.show_all()

    def create_widgets(self):


        label_1 = gtk.Label("Name:")
        label_2 = gtk.Label("Description:")
        self.button_select_image = gtk.Button("Select Image")
        self.button_add_file = gtk.Button("Add File")
        self.button_remove_file = gtk.Button("Remove Selected")
        self.entry_name = gtk.Entry()
        self.entry_description = gtk.TextView()

        self.image_widget = gtk.Image()


        self.files_model = gtk.ListStore(str)

        scrollable_view = gtk.ScrolledWindow()

        view_files = gtk.TreeView(model=self.files_model)
        scrollable_view.add(view_files)
        self.selection = view_files.get_selection()

        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn('Filename', cell, text=0)
        view_files.append_column(col)

        table = gtk.Table(rows=2, columns=2)
        self.dialog.vbox.pack_start(table)
        table.attach(label_1, 0, 1, 0, 1, False, False, 5, 5)
        table.attach(label_2, 0, 1, 1, 2, False, False, 5, 5)
        table.attach(self.button_select_image, 0, 1, 2, 3, False, False, 5, 5)
        table.attach(self.button_add_file, 0, 1, 3, 4, False, False, 5, 5)
        table.attach(self.button_remove_file, 1, 2, 4, 5, False, False, 5, 5)

        table.attach(self.entry_name,             1, 2, 0, 1, gtk.EXPAND|gtk.FILL, False, 5, 5)
        table.attach(self.entry_description,             1, 2, 1, 2, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL, 5 ,5)
        table.attach(self.image_widget,        1, 2, 2, 3, gtk.EXPAND|gtk.FILL, gtk.FILL, 5 ,5)
        table.attach(scrollable_view,         1, 2, 3, 4, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL, 5 ,5)


    def connect_signals(self):
        self.button_select_image.connect("clicked", self.select_image)
        self.button_add_file.connect("clicked", self.add_file)
        self.button_remove_file.connect("clicked", self.remove_file)


    def select_image(self, widget):
        dialog=gtk.FileChooserDialog(title="Select Image", action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/gif")
        dialog.add_filter(filter)

        response = dialog.run()
        filename = None
        if response == gtk.RESPONSE_OK:
            self.image_filename = dialog.get_filename()
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.image_filename, 200, 200)
            self.image_widget.set_from_pixbuf(pixbuf)


        dialog.destroy()
        return filename


    def add_file(self, widget):
        dialog = gtk.FileChooserDialog(title="Add File", action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_select_multiple(True)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filenames = dialog.get_filenames()
            for filename in filenames:
                self.files_model.append([filename])
        dialog.destroy()

    def remove_file(self, widget):
        if len(self.files_model) != 0:
            (model, iter) = self.selection.get_selected()
            if iter is not None:
                model.remove(iter)


    def get_name(self):
        return self.entry_name.get_text()

    def get_description(self):
        buffer = self.entry_description.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        text = buffer.get_text(start_iter, end_iter, True)
        return text

    def get_image(self):
        return self.image_filename

    def get_filenames(self):
        return [row[0] for row in self.files_model]

    def run(self):

        response = self.dialog.run()

        if response == gtk.RESPONSE_OK:

            result = {}
            result['name'] = self.get_name()
            result['description'] = self.get_description()
            result['image'] = self.get_image()
            result['filenames'] = self.get_filenames()

            self.do_upload(result)


        self.dialog.destroy()

        return


    def do_upload(self, data):
        print('upload')

        name = data['name']
        description = data['description']
        image = data['image']
        filename = data['filenames'][0]
        category = 'brushes'

        self.api.put_asset(name, category, description, image, filename)


    def get_filename(self):
        return self.dialog.get_filename()

    def destroy(self, widget, data=None):
        print("destroy")
        #gtk.main_quit()


if __name__ == '__main__':
    dialog = WilberUploadDialog('')
    result = dialog.run()
