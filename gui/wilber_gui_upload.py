# coding: utf-8
from __future__ import unicode_literals, print_function, division
from wilber_common import ASSET_TYPE_TO_CATEGORY
from os.path import splitext, basename, getsize
import os
import logging
import gtk


DEBUG = False

logger = logging.getLogger('wilber.gui.upload')


class FileValidator(object):
    extension_message = "Extension '%(extension)s' of file '%(filename)s' not allowed. Allowed extensions are: '%(allowed_extensions)s.'"
    min_size_message = "'%(filename)s' file has %(size)s, which is too small. The minumum file size is %(allowed_size)s."
    max_size_message = "'%(filename)s' file has %(size)s, which is too large. The maximum file size is %(allowed_size)s."

    def __init__(self, *args, **kwargs):
        self.allowed_extensions = kwargs.pop('allowed_extensions', None)
        self.min_size = kwargs.pop('min_size', 1)
        self.max_size = kwargs.pop('max_size', 20 * 10**20)  # 20 MiB

    def __call__(self, filepath):
        # Check the extension
        self.filename = basename(filepath)
        self.ext = splitext(filepath)[1].lower()

        if self.allowed_extensions and self.ext not in self.allowed_extensions:
            message = self.extension_message % {
                'filename': self.filename,
                'extension': self.ext,
                'allowed_extensions': ', '.join(self.allowed_extensions)
            }
            return False, message

        filesize = getsize(filepath)
        if self.max_size and filesize > self.max_size:
            message = self.max_size_message % {
                'filename': self.filename,
                'size': self.filesizeformat(filesize),
                'allowed_size': self.filesizeformat(self.max_size)
            }
            return False, message

        elif filesize < self.min_size:
            message = self.min_size_message % {
                'filename': self.filename,
                'size': self.filesizeformat(filesize),
                'allowed_size': self.filesizeformat(self.min_size)
            }
            return False, message

        return True, ''

    def filesizeformat(self, num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)


class Folder(object):
    def __init__(self, folder):
        self.folder = folder

    def __enter__(self):
        self.previous_dir = os.getcwd()
        os.chdir(self.folder)
        return self.folder

    def __exit__(self, exc_type, exc_value, tb):
        os.chdir(self.previous_dir)


class WilberUploadDialog(object):
    def __init__(self, folder='.'):
        self.dialog = gtk.Dialog(
            "Wilber Upload",
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        )

        self.image_filename = None
        self.base_folder = folder

        self.create_widgets()
        self.connect_signals()
        self.dialog.connect("destroy", self.destroy)
        self.dialog.show_all()

        self.validate_data()

    def create_widgets(self):
        label_name = gtk.Label("Name:")
        label_description = gtk.Label("Description:")
        label_category = gtk.Label("Category:")
        self.status_message = gtk.Label("Message Message Message")
        self.status_message.set_line_wrap(True)

        self.button_select_image = gtk.Button("Select Thumbnail")
        self.button_add_file = gtk.Button("Add File")
        self.button_remove_file = gtk.Button("Remove Selected")
        self.entry_name = gtk.Entry()
        self.entry_description = gtk.TextView()
        self.entry_description.set_size_request(200, 100)
        self.category_dropdown = gtk.combo_box_new_text()
        for asset_type in ASSET_TYPE_TO_CATEGORY.keys():
            self.category_dropdown.append_text(asset_type)

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

        table.attach(label_name,                0, 1, 0, 1, False, False, 5, 5)
        table.attach(label_description,         0, 1, 1, 2, False, False, 5, 5)
        table.attach(self.button_select_image,  0, 1, 2, 3, False, False, 5, 5)
        table.attach(label_category,            0, 1, 3, 4, False, False, 5, 5)
        table.attach(self.button_add_file,      0, 1, 4, 5, False, False, 5, 5)
        table.attach(self.button_remove_file,   0, 1, 5, 6, False, False, 5, 5)

        table.attach(self.entry_name,           1, 2, 0, 1, gtk.EXPAND | gtk.FILL, False, 5, 5)
        table.attach(self.entry_description,    1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 5, 5)
        table.attach(self.image_widget,         1, 2, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL, 5, 5)
        table.attach(self.category_dropdown,    1, 2, 3, 4, gtk.EXPAND | gtk.FILL, False, 5, 5)
        table.attach(scrollable_view,           1, 2, 4, 6, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 5, 5)

        table.attach(self.status_message,       0, 2, 6, 7, False, False, 5, 5)

    def set_message(self, message):
        self.status_message.set_text(message)

    def connect_signals(self):
        self.button_select_image.connect("clicked", self.select_image)
        self.button_add_file.connect("clicked", self.add_file)
        self.button_remove_file.connect("clicked", self.remove_file)

        self.entry_name.connect("focus-out-event", self.validate_data)
        self.entry_description.connect("focus-out-event", self.validate_data)
        self.category_dropdown.connect("changed", self.validate_data)

    def select_image(self, widget):
        dialog = gtk.FileChooserDialog(title="Select Image", action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        file_filter = gtk.FileFilter()
        file_filter.set_name("Images")
        file_filter.add_mime_type("image/jpeg")
        file_filter.add_mime_type("image/png")
        file_filter.add_mime_type("image/gif")
        dialog.add_filter(file_filter)

        response = dialog.run()
        filename = None
        if response in (gtk.RESPONSE_OK, gtk.RESPONSE_ACCEPT):
            self.image_filename = dialog.get_filename()
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.image_filename, 200, 200)
            self.image_widget.set_from_pixbuf(pixbuf)

        dialog.destroy()
        self.validate_data()
        return filename

    def add_file(self, widget):
        with Folder(self.base_folder) as folder:
            dialog = gtk.FileChooserDialog(
                title="Add File",

                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
            )
            dialog.set_select_multiple(True)
            dialog.set_current_folder(folder)
            response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filenames = dialog.get_filenames()
            for filename in filenames:
                self.files_model.append([filename])
        dialog.destroy()
        self.validate_data()

    def remove_file(self, widget):
        if len(self.files_model) != 0:
            (model, i) = self.selection.get_selected()
            if i is not None:
                model.remove(i)
        self.validate_data()

    def get_name(self):
        return self.entry_name.get_text()

    def get_description(self):
        entry_buffer = self.entry_description.get_buffer()
        start_iter = entry_buffer.get_start_iter()
        end_iter = entry_buffer.get_end_iter()
        text = entry_buffer.get_text(start_iter, end_iter, True)
        return text

    def get_category(self):
        label = self.category_dropdown.get_active_text()
        if label:
            category = ASSET_TYPE_TO_CATEGORY[label]
            return category

    def get_image(self):
        return self.image_filename

    def get_filenames(self):
        return [row[0] for row in self.files_model]

    def grab_data(self):
        return {
            'name': self.get_name(),
            'description': self.get_description(),
            'category': self.get_category(),
            'image': self.get_image(),
            'filenames': self.get_filenames(),
        }

    def run(self):
        response = self.dialog.run()
        data = self.grab_data()
        self.dialog.destroy()
        return response, data

    def validate_files(self, category, filenames):
        validators = {
            "brushes": FileValidator(allowed_extensions=['.gbr', '.vbr', '.gih']),
            "patterns": FileValidator(allowed_extensions=['.pat']),
            "gradients": FileValidator(allowed_extensions=['.ggr']),
            "plug-ins": FileValidator(allowed_extensions=['.py', '.zip']),
            "palettes": FileValidator(allowed_extensions=['.gpl']),
            "tool-presets": FileValidator(allowed_extensions=['.gtp']),
        }

        validator = validators[category]
        validations = [validator(filename) for filename in filenames]
        result = all([i[0] for i in validations])
        message = ' '.join([i[1] for i in validations])
        return result, message

    def validate_data(self, widget=None, event=None):
        data = self.grab_data()
        if not all(data.values()):
            self.dialog.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
            void_fields = [k for k, v in data.items() if not v]
            logger.info('Invalid Data: ' + ', '.join(void_fields))
            self.set_message("Please fill the fields: " + ', '.join(void_fields))
            return False
        else:
            valid, message = self.validate_files(data['category'], data['filenames'])
            if not valid:
                self.set_message(message)
                self.dialog.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
                return False

        self.set_message("")
        self.dialog.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
        logger.info('Data is valid')
        return True

    def destroy(self, widget, data=None):
        if DEBUG:
            gtk.main_quit()


if __name__ == '__main__':
    DEBUG = True
    dialog = WilberUploadDialog()
    result = dialog.run()
