# coding: utf-8
from __future__ import print_function, unicode_literals

#Python imports
import os
import sqlite3
from os import path

#GIMP imports

from gimpfu import gimp

#Wilber imports
from wilber_api import WilberAPIClient

class WilberPlugin(object):
    def __init__(self, settings):
        self.settings = settings
        self.api = WilberAPIClient(settings)
        self.db = self.init_db()

    def init_db(self):
        db_path = os.path.join(self.get_wilber_folder(), 'wilber_db.sqlite')
        db = sqlite3.connect(db_path)
        return db

    def get_wilber_folder(self):
        wilber_folder = path.join(gimp.directory, 'plug-ins', 'wilber')
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
        print('Downloading', url)
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

    def get_assets(self):
        assets = self.api.get_assets()

        for asset in assets:
            url = asset['image']
            filepath = self.download_file(url)
            asset['image_path'] = filepath
        return assets
