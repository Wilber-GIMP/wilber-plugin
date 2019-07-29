# coding: utf-8
from __future__ import print_function, unicode_literals, division

import sys
from os.path import dirname, realpath, join

PLUGINS_PATH = dirname(realpath(__file__))
WILBER_LIBS_PATH = join(PLUGINS_PATH, 'libs')
sys.path.insert(0, WILBER_LIBS_PATH)

import requests
#import requests_cache

from wilber_config import Config
from wilber_common import ASSET_TYPE_TO_CATEGORY

class WilberAPIClient(object):

    def __init__(self):
        self.settings = Config()
        self.URL = self.settings.get_server_url()
        self.token = None

        #if self.settings.get_use_cache():
        #    requests_cache.install_cache(self.settings.get_cache_folder())

    def headers(self):
        if not self.token:
            if self.settings.token:
                self.token = self.settings.token
            else:
                self.login(self.settings.username, self.settings.password)
        if self.token:
            return {'Authorization': 'Token %s' % self.token}
        return {}

    def request_get(self, uri, json=True, **kwargs):
        response = requests.get(uri, headers=self.headers(), **kwargs)
        if json:
            return response.json()
        return response

    def request_post(self, url, data={}, headers={}, files={}, json=True):
        response = requests.post(url, data=data, headers=headers, files=files)
        print(response.status_code)
        if response.status_code > 399:
            print(response.content)
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


    def get_token(self):
        token = self.config.get_token()

    #API LOGIN
    def login(self, username, password):
        url = self.URL+'/api-token-auth/'
        data = {'username':username, 'password':password}

        response = self.request_post(url, data)

        token_key = 'token'

        if token_key in response:
            self.token = response[token_key]
            print("logged in succesfully into Wilber Social")
            return self.token
        else:
            print("Failed to login in Wilber Social")

    #API GET ASSETS
    def get_assets(self, type_=None):
        url = self.URL + '/api/asset/'
        print('\n\nConnecting to ', url)

        params = {"format": "json"}
        if type_:
            params["category"] = ASSET_TYPE_TO_CATEGORY[type_]
        json_data = self.request_get(url, params=params)
        print(json_data)
        return json_data['results']

    def put_asset(self, name, category, description, image, file):
        url = self.URL + '/api/asset/'
        data = {'name':name,
            'description':description,
            'category':category,
            }
        files = {
            'file': open(file, 'rb'),
        }
        if image:
            files["image"] = open(image, "rb")

        response = self.request_post(url, data=data, files=files, headers=self.headers(), json=False)
        return response
