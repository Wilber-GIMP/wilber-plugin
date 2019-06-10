#!/usr/bin/env python
import sys
import os
import errno
from os import path
import requests
#sys.stderr = open(path.expanduser('~/tmp/wilber_error.txt'), 'a')
#sys.stdout = open(path.expanduser('~/tmp/wilber_log.txt'), 'a')
import gtk
import gtk.gdk
from gtk.gdk import Pixbuf, pixbuf_new_from_stream, pixbuf_new_from_file_at_size

from gimpfu import *
import urllib2


THUMB_IMAGE_WIDTH = 100
THUMB_IMAGE_HEIGHT = 100



class WilberAPIClient(object):
    URL = 'http://127.0.0.1:8000'
    def __init__(self):
        self.token = None

    def headers(self):
        if self.token:
            return {'Authorization': 'Token %s' % self.token}
        return {}

    def request_get(self, uri):
        response = requests.get(uri, headers=self.headers())
        print(response)
        json = response.json()
        return json

    def request_post(self, url, data={}, headers={}):
        response = requests.post(url, data=data, headers=headers)
        print(response)
        return response.json()



    #API CREATE USER
    def create_user(self, username, password1, password2, email):
        url = self.URL + '/rest-auth/registration/'
        data = {'username': username,
            'password1': password1,
            'password2': password2,
            'email': email
            }
        response = self.request_post(url, data)
        print(response)
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
        return self.request_get(url)

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

        response = requests.post(url, data=data, files=files, headers=self.headers())
        return response




class WilberPlugin(object):
    def __init__(self):
        self.api = WilberAPIClient()
    
    def get_wilber_folder(self):
        return path.join(gimp.directory, 'tmp', 'wilber')
        
    def get_asset_folder(self, asset):
        folder = path.join(gimp.directory, asset['folder'])
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
        r = requests.get(url, allow_redirects=True)
        filename = self.get_filename_from_url(url)
        filedir = path.join(self.get_wilber_folder(), folder)
        self.mkdirs(filedir)
        filepath = path.join(filedir, filename)
        with open(filepath, 'wb') as f:
            f.write(r.content)
        return filepath
        
    def download_asset(self, asset):
        url = asset['file']
        folder = self.get_asset_folder(asset)
        filepath = self.download_file(url, folder)


    def download_assets_list(self, assets):
        for asset in assets:
            url = asset['image']
            filepath = self.download_file(url)
            asset['image_path'] = filepath
            
    def get_assets(self):
        assets = self.api.get_assets()
        
        self.download_assets_list(assets)
        return assets




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
    
    
    def download_asset(self, button, asset):
        self.plugin.download_asset(asset)
    
    def connect_signals(self):
        self.button_exit.connect("clicked", self.callback_exit)
    
    
    def callback_ok(self, widget, callback_data=None):
        name = self.entry.get_text()
        print name
    
    
    def callback_exit(self, widget, callback_data=None):
        gtk.main_quit()



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

main()
