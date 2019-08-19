# coding: utf-8
from __future__ import print_function, unicode_literals, division

#Python imports
import errno
import os
import sqlite3
import shutil
import logging
from os import path
from os.path import join, basename


try:
    from gimpfu import gimp
    GIMP_DIRECTORY = gimp.directory
except:
    GIMP_DIRECTORY = path.expanduser('~/.config/GIMP/2.10')


# Wilber imports
from wilber_api import WilberAPIClient
from wilber_common import Asset, ASSET_TYPE_TO_CATEGORY
from wilber_log import logger


logger = logging.getLogger('wilber.plugin')

GIMP_FOLDERS = [
    'brushes',
    'gradients',
    'palettes',
    'patterns',
    'plug-ins',
    'scripts',
    'tool-options',
    'tool-presets',
]


class WilberPlugin(object):
    def __init__(self, settings):
        self.settings = settings
        self.gimp_directory = GIMP_DIRECTORY
        Asset.gimp_directory = GIMP_DIRECTORY
        self.api = WilberAPIClient()
        self.db = self.init_db()
        self.current_asset_type = "brush"
        self.installed = {}
        self.update_installed()

    def init_db(self):
        db_path = os.path.join(self.get_wilber_folder(), 'wilber_db.sqlite')
        db = sqlite3.connect(db_path)
        return db

    def get_wilber_folder(self):
        wilber_folder = path.join(self.gimp_directory, 'plug-ins', 'wilber')
        if not os.path.exists(wilber_folder):
            self.mkdirs(wilber_folder)
        return wilber_folder

    def get_asset_folder(self, asset):
        folder = os.path.join(self.get_wilber_folder(), asset['folder'])
        return folder

    def mkdirs(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path, 0o700)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

    def get_filename_from_url(self, url):
        if '/' in url:
            return url.rsplit('/', 1)[1]

    def download_file(self, url, folder='thumbs'):
        logger.info('Downloading %s' % url)
        response = self.api.request_get(url, allow_redirects=True, json=False)
        filename = self.get_filename_from_url(url)
        filedir = path.join(self.get_wilber_folder(), folder)
        self.mkdirs(filedir)
        filepath = path.join(filedir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath

    def download_asset(self, asset):
        url = asset['file']
        folder = self.get_asset_folder(asset)
        filepath = self.download_file(url, folder)

        destination_folder = self.get_gimp_folder(asset)
        if not destination_folder:
            print("Asset downloaded to '%s'" % filepath)
            return
        shutil.move(filepath, destination_folder)
        final_path = os.path.join(destination_folder, os.path.basename(filepath))

        category = asset["category"]
        self.update_gimp(category)

        print("Asset downloaded and moved to '%s'" % final_path)
        self.update_installed()

    def update_gimp(self, category):
        try:
            from gimpfu import pdb
            if category in "brushes gradients palettes dynamics fonts palette patterns":
                procedure = getattr(pdb, "gimp_%s_refresh" % category)
                procedure()
        except Exception as e:
            print(e)

    def remove_asset(self, asset):
        local = Asset(asset).local_folder()
        print('Removing ', local)
        os.remove(local)
        self.update_installed()

    def get_gimp_folder(self, asset):
        folder = os.path.join(self.gimp_directory, asset.get("category", "NONEXISTENT"))
        if not os.path.exists(folder):
            return None
        return folder

    def get_assets(self, query=None, more=False):
        assets, has_more = self.api.get_assets(type_=self.current_asset_type, query=query, more=more)
        if assets:
            for asset in assets:
                url = asset['image_thumbnail']
                filepath = self.download_file(url)
                asset['image_path'] = filepath
            return assets, has_more
        return None

    def sanitize_response(self, response):
        from gimpfu import pdb
        try:
            filename = response.pop("filenames")[0]
        except (KeyError, IndexError):
            return False
        if not os.path.exists(filename):
            return False
        thumbnail_path = response["image"] or ""
        name = response.pop("name", os.path.basename(filename))

        if not os.path.exists(thumbnail_path):
            try:
                thumbnail_img = pdb.gimp_file_load(filename, filename)
            except RuntimeError:
                pass
        else:
            thumbnail_img = pdb.gimp_file_load(thumbnail_path, thumbnail_path)

        thumbnail_new_path = None
        if thumbnail_img:
            import tempfile
            self.constrain_thumbnail_size(thumbnail_img, self.settings.get_image_size())
            thumbnail_new_path = os.path.join(tempfile.gettempdir(), slugify(name) + ".png")
            if len(thumbnail_img.layers) > 1:
                pdb.gimp_image_merge_down(thumbnail_img, thumbnail_img.layers[0], gimpfu.CLIP_TO_IMAGE)
            pdb.gimp_file_save(thumbnail_img, thumbnail_img.layers[0], thumbnail_new_path, thumbnail_new_path)
            pdb.gimp_image_delete(thumbnail_img)
        description = response["description"]
        response.clear()
        response["name"] = name
        response["category"] = ASSET_TYPE_TO_CATEGORY[self.current_asset_type]
        response["description"] = description  # self.ensure_tags_in_descritpion(response["description"])
        response["image"] = thumbnail_new_path
        response["file"] = filename
        return True

    def constrain_thumbnail_size(self, img, requested_size):
        from gimpfu import pdb
        if img.width < requested_size or img.width > 3 * requested_size:
            # Do not allow too little images that would not work as thumbnails:
            new_width = requested_size
            new_height = img.height * (new_width / img.width)
            if new_height / new_width > 1.5:
                # Weird vertical aspect ratio - limit image by height rather than width:
                new_height = requested_size
                new_width = img.width * (new_height / img.height)
            pdb.gimp_image_scale(img, new_width, new_height)
        return

    def update_installed(self):
        for folder in GIMP_FOLDERS:
            self.installed[folder] = os.listdir(join(self.gimp_directory, folder))

    def asset_is_installed(self, asset):
        filename = basename(asset['file'])
        folder = asset['folder']
        if folder in self.installed:
            return filename in self.installed[folder]
        return False


def slugify(name):
    import unicodedata
    if not isinstance(name, unicode):
        name = name.decode("utf-8")
    name = name.lower()
    name = name.encode("ASCII", errors="replace").decode("ASCII")
    new_name = ""
    for char in name:
        if unicodedata.category(char) not in ("Ll", "Nd"):
            new_name += "_" if name and name[-1] != "_" else ""
        else:
            new_name += char
    return new_name
