# coding: utf-8
from __future__ import unicode_literals, print_function, division
from os.path import basename, join
from collections import OrderedDict

ASSET_TYPE_TO_CATEGORY = OrderedDict([
    ("Brush", "brushes"),
    ("Pattern", "patterns"),
    ("Gradient", "gradients"),
    ("Plug-in", "plug-ins"),
    ("Palette", "palettes"),
    ("Preset", "tool-presets"),
])


class Asset(object):
    __cache__ = {}
    __installed__ = {}
    gimp_directory = '.'

    def __init__(self, dic):
        self.__dict__.update(dic)
        self.id = dic['id']
        self.dic = dic


        if id not in Asset.__cache__:
            Asset.__cache__[self.id] = self

    @classmethod
    def get(self, id):
        return Asset.__cache__.get(id, None)

    @classmethod
    def get_asset(self, id):
        asset = Asset.get(id)
        if asset:
            return asset.dic

    def is_installed(self):
        return self.plugin.asset_is_installed(self.dic)
        filename = basename(self.file)
        folder = self.folder

        return filename in self.__installed__[folder]

    def local_folder(self):
        filename = basename(self.file)
        folder = self.folder
        return join(self.gimp_directory, folder, filename)