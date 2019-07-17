# coding: utf-8
from __future__ import print_function, unicode_literals, division

from ConfigParser import SafeConfigParser, NoSectionError
from os.path import join
import ast

class Config(object):
    SETTINGS_FILE = 'settings.ini'
    #SETTINGS_PATH = join(WILBER_PATH, SETTINGS_FILE)

    def __init__(self, wilber_path):
        self.settings_path = join(wilber_path, self.SETTINGS_FILE)
        self.cache_folder = join(wilber_path, 'wilber_cache')
        self.parser = SafeConfigParser()
        self.parser.read(self.settings_path)

        self.get_values()

    def set(self, page, key, value):
        return self.parser.set(page, key, value)

    def get(self, page, key, default=None):
        if default is not None:
            try:
                result = self.parser.get(page, key)
            except:
                return default
            else:
                return result
        return self.parser.get(page, key)

    def get_values(self):
        try:
            self.username = self.parser.get('User', 'username')
            self.password = self.parser.get('User', 'password')
        except NoSectionError:
            self.username = ''
            self.password = ''

    def save(self):
        with open(self.settings_path, 'wt') as configfile:
            self.parser.write(configfile)
            print('Config File saved at',self.settings_path)

    def get_use_cache(self,default='False'):
        return ast.literal_eval(self.get('Settings', 'use_cache', default))

    def get_username(self):
        return self.get('User', 'username')

    def get_password(self):
        return self.get('User', 'password')

    def get_image_size(self):
        return int(self.get('Interface', 'thumb_image_size'))

    def get_cache_folder(self):
        return self.cache_folder

    def set_username(self, value):
        self.set('User', 'username', value)

    def set_password(self, value):
        self.set('User', 'password', value)
