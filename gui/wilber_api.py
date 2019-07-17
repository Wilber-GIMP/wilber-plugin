# coding: utf-8

from __future__ import print_function, unicode_literals, division


import requests
import requests_cache
#requests_cache.install_cache('/home/darpan/tmp/wilber-cache')


from wilber_common import ASSET_TYPE_TO_CATEGORY

class WilberAPIClient(object):
    URL = 'http://127.0.0.1:8000'
    def __init__(self, settings):
        self.settings = settings
        self.URL = settings.get_server_url()
        self.token = None

        if settings.get_use_cache():
            requests_cache.install_cache(self.settings.get_cache_folder())
        #self.sess = requests.session()
        #self.cached_sess = CacheControl(self.sess)

    def headers(self):
        if not self.token:
            self.login(self.settings.username, self.settings.password)
        if self.token:
            return {'Authorization': 'Token %s' % self.token}
        return {}

    def request_get(self, uri, json=True, **kwargs):
        response = requests.get(uri, headers=self.headers(), **kwargs)
        #response = self.cached_sess.get(uri, headers=self.headers(), **kwargs)
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

    #API LOGIN
    def login(self, username, password):
        url = self.URL+'/rest-auth/login/?format=json'
        data = {'username':username, 'password':password}

        response = self.request_post(url, data)
        if 'key' in response:
            self.token = response['key']
            print("logged in succesfully into Wilber Social")
            return self.token
        else:
            print("Failed to login in Wilber Social")

    #API GET ASSETS
    def get_assets(self, type_=None):
        url = self.URL + '/api/asset/'
        params = {"format": "json"}
        if type_:
            params["category"] = ASSET_TYPE_TO_CATEGORY[type_]
        json_data = self.request_get(url, params=params)
        return json_data['results']

    def put_asset(self, name, type, description, image, file):
        url = self.URL + '/api/asset/'
        data = {
            'name': name,
            'description': description,
            'category': type,
        }
        files = {
            'file': open(file, 'rb'),
        }
        if image:
            files["image"] = open(image, "rb")

        response = self.request_post(url, data=data, files=files, headers=self.headers(), json=False)
        return response
