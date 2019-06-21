#!/usr/bin/env python
import os
import sys
import urllib2
import sqlite3
import errno
import ast
from os import path
from os.path import dirname, realpath, join
from datetime import datetime
from configparser import SafeConfigParser


import gtk
import gtk.gdk
from gtk.gdk import Pixbuf, pixbuf_new_from_stream, pixbuf_new_from_file_at_size
from gimpfu import *

PLUGINS_PATH = dirname(realpath(__file__))
WILBER_PATH = join(PLUGINS_PATH, 'wilber')
WILBER_LIBS_PATH = join(WILBER_PATH, 'libs')
sys.path.insert(0, WILBER_LIBS_PATH)
#Wilber Libs:
import requests
import requests_cache





COMMIT_NUMBER=4
COMMIT_DATE='2019-06-11'

THUMB_IMAGE_WIDTH = 200
THUMB_IMAGE_HEIGHT = 200


def show_version():
    print("Started Wilber Plugin Version %s %d %s" % (COMMIT_DATE, COMMIT_NUMBER, datetime.now()))



class Config(object):
    SETTINGS_FILE = 'settings.ini'
    SETTINGS_PATH = join(WILBER_PATH, SETTINGS_FILE)

    def __init__(self):
        self.parser = SafeConfigParser()
        self.parser.read(self.SETTINGS_PATH)

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
        self.username = self.parser.get('User', 'username')
        self.password = self.parser.get('User', 'password')




    def save(self):
        with open(self.SETTINGS_PATH, 'w') as configfile:
            self.parser.write(configfile)
            print('Config File saved at',self.SETTINGS_PATH)

    def get_use_cache(self,default='False'):
        return ast.literal_eval(self.get('Settings', 'use_ache', default))

    def get_username(self):
        return self.get('User', 'username')

    def get_password(self):
        return self.get('User', 'password')

    def set_username(self, value):
        self.set('User', 'username', value)

    def set_password(self, value):
        self.set('User', 'password', value)


config = Config()
config.save()

if config.get_use_cache():
    requests_cache.install_cache(join(WILBER_PATH,'wilber_cache'))


class WilberAPIClient(object):
    URL = 'http://127.0.0.1:8000'
    def __init__(self):
        self.token = None
        #self.sess = requests.session()
        #self.cached_sess = CacheControl(self.sess)

    def headers(self):
        if self.token:
            return {'Authorization': 'Token %s' % self.token}
        return {}

    def request_get(self, uri, json=True, **kwargs):
        response = requests.get(uri, headers=self.headers(), **kwargs)
        #response = self.cached_sess.get(uri, headers=self.headers(), **kwargs)
        if json:
            return response.json()
        return response

    def request_post(self, url, data={}, headers={}, json=True):
        response = requests.post(url, data=data, headers=headers)
        if json:
            return response.json()
        return response



    #API CREATE USER
    def create_user(self, username, password1, password2, email):
        url = self.URL + '/rest-auth/registration/'
        data = {'username': username,
            'password1': password1,
            'password2': password2,
            'email': email
            }
        response = self.request_post(url, data)
        return response

    #API LOGIN
    def login(self, username, password):
        url = self.URL+'/rest-auth/login/?format=json'
        data = {'username':username, 'password':password}

        response = self.request_post(url, data)
        if 'key' in response:
            self.token = response['key']
            return self.token
        else:
            print(r)

    #API GET ASSETS
    def get_assets(self, type=None):
        url = self.URL + '/api/asset/?format=json'
        if type:
            url += "&type=%s" % type
        json = self.request_get(url)
        return json['results']

    def put_asset(self, name, type, desc, image, file):
        url = self.URL + '/api/asset/'
        data = {'name':name,
            'description':desc,
            'type':type,
            }
        files = {
            'image':open(image, 'rb'),
            'file':open(file, 'rb'),
        }

        response = self.request_post(url, data=data, files=files, headers=self.headers(), json=False)
        return response




class WilberPlugin(object):
    def __init__(self):
        self.api = WilberAPIClient()
        self.db = self.init_db()

    def init_db(self):
        db_path = os.path.join(self.get_wilber_folder(), 'wilber_db.sqlite')
        db = sqlite3.connect(db_path)
        return db

    def get_wilber_folder(self):
        wilber_folder = path.join(gimp.directory, 'plug-ins', 'wilber')
        self.mkdirs(wilber_folder)
        return wilber_folder

    def get_asset_folder(self, asset):
        folder = path.join(self.get_wilber_folder(), asset['folder'])
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


class WilberConfigDialog(gtk.Dialog):
    def __init__(self):
        dialog = gtk.Dialog("Wilber Config",
                   None,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        label_username = gtk.Label("Username:")
        entry_username = gtk.Entry()

        label_password = gtk.Label("Password:")
        entry_password = gtk.Entry()
        entry_password.set_visibility(False)

        entry_username.set_text(config.username)
        entry_password.set_text(config.password)

        dialog.vbox.pack_start(label_username)
        dialog.vbox.pack_start(entry_username)
        dialog.vbox.pack_start(label_password)
        dialog.vbox.pack_start(entry_password)
        #label.show()
        #entry.show()
        checkbox = gtk.CheckButton("Useless checkbox")
        #dialog.action_area.pack_end(checkbox)
        checkbox.show()
        dialog.show_all()

class WilberGui(object):
    def __init__(self):
        self.plugin = WilberPlugin()
        self.window = gtk.Window()
        self.window.set_title("Wilber Asset Manager")
        windowicon = self.window.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_LARGE_TOOLBAR)
        self.window.set_icon(windowicon)

        self.create_widgets()
        self.connect_signals()

        self.window.show_all()

        gtk.main()


    def create_widgets(self):
        self.vbox = gtk.VBox(spacing=10)

        self.hbox_1 = gtk.HBox(spacing=10)
        self.label = gtk.Label("Search:")
        self.hbox_1.pack_start(self.label, False)
        self.entry = gtk.Entry()
        self.hbox_1.pack_start(self.entry)

        self.button_config = gtk.Button("Config")
        self.hbox_1.pack_start(self.button_config)

        self.hbox_2 = gtk.HButtonBox()
        self.button_exit = gtk.Button("Exit")
        self.hbox_2.pack_start(self.button_exit)


        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_size_request(480, 480)
        view_port = gtk.Viewport()

        self.table = gtk.Table(rows=7, columns=3)

        for row, asset in enumerate(self.plugin.get_assets()):
            name = asset['name']

            image = gtk.Image()
            try:
                pixbuf = pixbuf_new_from_file_at_size(asset['image_path'], THUMB_IMAGE_WIDTH, THUMB_IMAGE_HEIGHT)
                image.set_from_pixbuf(pixbuf)
            except Exception as e:
                print(e)

            button = gtk.Button('Download')
            button.connect("clicked", self.download_asset, asset)

            self.table.attach(image, 0, 1, row, row+1, False, False)
            self.table.attach(gtk.Label(name), 1 , 2, row, row+1, False, False)
            self.table.attach(button, 2,3, row, row+1, False, False)

        view_port.add(self.table)
        scrolled_window.add(view_port)


        self.vbox.pack_start(self.hbox_1, False, False,)
        self.vbox.pack_start(scrolled_window, True, True)
        self.vbox.pack_start(self.hbox_2, False, False)

        self.window.add(self.vbox)


    def window_config(self):

        dialog = gtk.Dialog("Wilber Config",
                   None,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        label_username = gtk.Label("Username:")
        entry_username = gtk.Entry()

        label_password = gtk.Label("Password:")
        entry_password = gtk.Entry()
        entry_password.set_visibility(False)

        entry_username.set_text(config.get_username())
        entry_password.set_text(config.get_password())

        self.entry_username = entry_username
        self.entry_password = entry_password

        dialog.vbox.pack_start(label_username)
        dialog.vbox.pack_start(entry_username)
        dialog.vbox.pack_start(label_password)
        dialog.vbox.pack_start(entry_password)
        #label.show()
        #entry.show()
        checkbox = gtk.CheckButton("Useless checkbox")
        #dialog.action_area.pack_end(checkbox)
        checkbox.show()
        dialog.show_all()
        return dialog


    def download_asset(self, button, asset):
        self.plugin.download_asset(asset)

    def connect_signals(self):
        self.button_exit.connect("clicked", self.callback_exit)
        self.button_config.connect("clicked", self.callback_show_config)


    def callback_ok(self, widget, callback_data=None):
        name = self.entry.get_text()


    def callback_exit(self, widget, callback_data=None):
        print('trying to quit')
        gtk.main_quit()
        print('im still here')

    def callback_show_config(self, widget, callback_data=None):
        dialog = self.window_config()
        response = dialog.run()

        if response==gtk.RESPONSE_ACCEPT:
            config.set_username(self.entry_username.get_text())
            config.set_password(self.entry_password.get_text())
            config.save()

        dialog.destroy()



def python_wilber():
    wilber = WilberGui()

register_params = {
    'proc_name': 'wilber_asset_manager',
    'blurb': 'Manage Gimp Assets',
    'help': 'Manage Gimp Assets',
    'author': 'Joao, Robin, Darpan',
    'copyright': 'Joao, Robin, Darpan',
    'date': '2019',
    'label': 'Manage Gimp Assets',
    'imagetypes': '*',
    'params': [],
    'results': [],
    'function': python_wilber,
    'menu': '<Toolbox>/Tools',
    'domain': None,
    'on_query': None,
    'on_run': None,
}

register(**register_params)
#show_version()
main()
