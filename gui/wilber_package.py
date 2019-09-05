import json
import os
import shutil
import tempfile
from collections import OrderedDict
from os import path
import logging
from wilber_log import logger

logger = logging.getLogger('wilber.package')


#shutil.make_archive('test','zip','/home/darpan/Dropbox/projects/wilber/','wilber-plugin/gui')


class WilberPackage(object):
    def __init__(self, name, description, category, image, filenames):
        self.name = name
        self.description = description
        self.category = category
        self.image = image
        self.file_list = filenames

        self.package_path = None
        self.temp_path = None

    def __call__(self):
        return self.make()

    def make(self):
        result, message = AssetValidator(self.category)(self.file_list)
        if result:
            self.package_path = self.create_temp_package(self.category, self.file_list)

            import subprocess
            subprocess.call(["xdg-open", path.dirname(self.package_path)])

        else:
            logger.error(message)
        return self.package_path

    def create_manifest(self, file_list):
        data = OrderedDict([
            ('name', self.name),
            ('description', self.description),
            ('software', 'GIMP'),
            ('category', self.category),
            ('wilber_package_version', '1.0'),
            ('file_list', file_list)]
        )
        return json.dumps(data, indent=4)

    def get_file_list(self, folder, base_path=None):
        file_list = []
        if base_path is None:
            base_path = folder

        for root, dirs, files in os.walk(folder):
            for name in files:
                filepath = os.path.join(root, name)
                file_list.append(os.path.relpath(filepath, start=base_path))

        return sorted(file_list)

    def create_temp_package(self, category, file_list):
        temp_path = tempfile.mkdtemp('', 'Wilber-Package-',)
        self.temp_path = temp_path

        package_name = 'package_file'
        package_path = path.join(temp_path, package_name)

        package_folder_name = 'GIMP'
        package_folder_path = path.join(temp_path, package_folder_name)
        asset_folder = path.join(package_folder_path, category)
        os.makedirs(asset_folder)

        #Copy assets
        for file in file_list:
            shutil.copy(file, asset_folder)

        #Copy image
        image_name, ext = path.splitext(self.image)
        new_image_path = path.join(package_folder_path, 'image'+ext)
        shutil.copy(self.image, new_image_path)
        self.image = new_image_path

        #Create manifest
        with open(path.join(package_folder_path, 'manifest.txt'), 'w') as f:
            file_list = self.get_file_list(package_folder_path)
            f.write(self.create_manifest(file_list))

        zipped_package_path = shutil.make_archive(package_path, 'zip', temp_path, package_folder_name)

        return zipped_package_path

    def clean(self):
        if self.temp_path:
            shutil.rmtree(self.temp_path)
            logger.info("Temporary path deleted: " + self.temp_path)
        else:
            logger.warning("Temporary folder not created")


class FileValidator(object):
    extension_message = "Extension '%(extension)s' of file '%(filename)s' not allowed. Allowed extensions are: '%(allowed_extensions)s.'"
    not_exists_message = "File '%(filename)s' not exists"
    min_size_message = "'%(filename)s' file has %(size)s, which is too small. The minumum file size is %(allowed_size)s."
    max_size_message = "'%(filename)s' file has %(size)s, which is too large. The maximum file size is %(allowed_size)s."

    def __init__(self, *args, **kwargs):
        self.allowed_extensions = kwargs.pop('allowed_extensions', None)
        self.min_size = kwargs.pop('min_size', 1)
        self.max_size = kwargs.pop('max_size', 20 * 10 ** 20)  # 20 MiB

    def __call__(self, filepath):
        #Check existence
        if not path.exists(filepath):
            message = self.not_exists_message % {
                'filename': filepath,
            }
            return False, message


        # Check the extension
        self.filename = path.basename(filepath)
        self.ext = path.splitext(filepath)[1].lower()

        if self.allowed_extensions and self.ext not in self.allowed_extensions:
            message = self.extension_message % {
                'filename': self.filename,
                'extension': self.ext,
                'allowed_extensions': ', '.join(self.allowed_extensions)
            }
            return False, message

        filesize = path.getsize(filepath)
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

        return True, 'Ok'

    def filesizeformat(self, num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)


class AssetValidator(object):
    asset_extensions = {
        "brushes": ['.gbr', '.vbr', '.gih'],
        "patterns": ['.pat'],
        "gradients": ['.ggr'],
        "plug-ins": ['.py', '.zip'],
        "palettes": ['.gpl'],
        "tool-presets": ['.gtp'],
    }

    guess_category_map = {ext: asset_type for asset_type, extensions in asset_extensions.items() for ext in extensions}

    def __init__(self, category):
        self.category = category

    def __call__(self, filenames):
        if isinstance(filenames, list) or isinstance(filenames, tuple):
            return self.validate_list(filenames)
        if isinstance(filenames, str):
            return self.validate(filenames)

    def guess_category(self, filepath):
        ext = path.splitext(filepath)[1].lower()
        return self.guess_category_map.get(ext, None)

    def validate(self, filename):
        if self.category:
            validator = FileValidator(allowed_extensions=self.asset_extensions[self.category])
            return validator(filename)

        return False, None


    def validate_list(self, filenames):
        validations = [self.validate(filename) for filename in filenames]
        result = all([i[0] for i in validations])
        message = "\n".join([i[1] for i in validations])
        return result, message


if __name__ == '__main__':
    name = 'Night Sky'
    description = 'Night Sky Brushes'
    category = 'brushes'
    image = path.expanduser('~/Downloads/GIMP/brushes/Night 2 GIMP BRUSHES -fullview/d20k1hj-fc0840fe-476e-4aac-a392-1db20bf094dc.jpg')
    file_list = [
        path.expanduser('~/.config/GIMP/2.10/brushes/nightsky_MyLastBlkRose_2_dFhPFBN.gbr'),
        path.expanduser('~/.config/GIMP/2.10/brushes/nightsky_MyLastBlkRose_5_DE7E2x4.gbr'),
        path.expanduser('~/Downloads/GIMP/brushes/Contact Lenses for GIMP/contact_lenses_for_gimp_by_thethiirdshift_d4szg0w/Contacttry2/contact1.gbr'),
    ]


    package = WilberPackage(name, description, category, image, file_list)
    package_path = package.make()
    print(package_path)
    #package.clean()