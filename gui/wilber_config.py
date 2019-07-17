# coding: utf-8
from __future__ import print_function, unicode_literals, division
import ConfigParser
from ConfigParser import SafeConfigParser

from os.path import dirname, join, realpath
import ast



class Config(object):
    GUI_PATH = dirname(realpath(__file__))
    WILBER_PATH = join(dirname(GUI_PATH), 'wilber')
    CACHE_PATH = join(WILBER_PATH, 'wilber_cache')

    SETTINGS_FILE = 'settings.ini'
    SETTINGS_FILEPATH = join(WILBER_PATH, SETTINGS_FILE)


    def __init__(self):
        self.settings_path = Config.SETTINGS_FILEPATH
        self.cache_folder = Config.CACHE_PATH
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

    def get_token(self):
        return self.get('User', 'token')

    def get_image_size(self):
        return int(self.get('Interface', 'thumb_image_size'))

    def get_cache_folder(self):
        return self.cache_folder

    def set_username(self, value):
        self.set('User', 'username', value)

    def set_password(self, value):
        self.set('User', 'password', value)

    def set_token(self, value):
        self.set('User', 'token', value)

    def get_server_url(self):
        return self.get('Server', 'server_url')
