# coding: utf-8

from __future__ import print_function, unicode_literals


import requests
import requests_cache
#requests_cache.install_cache('/home/darpan/tmp/wilber-cache')



class WilberAPIClient(object):
    URL = 'http://127.0.0.1:8000'
    def __init__(self, settings):
        self.settings = settings
        self.token = None

        if settings.get_use_cache():
            requests_cache.install_cache(self.settings.get_cache_folder())
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
        url = self.URL + '/api/asset/'
        params = {"format": "json"}
        if type:
            params["type"] = type
        json = self.request_get(url, params=params)
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
