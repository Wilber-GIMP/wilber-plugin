import sys
from os.path import dirname, realpath, join

PLUGINS_PATH = dirname(realpath(__file__))
WILBER_LIBS_PATH = join(PLUGINS_PATH, 'libs')

sys.path.insert(0, WILBER_LIBS_PATH)

import requests
import requests_cache

from wilber_config import Config

class WilberAPIClient(object):
    URL = 'http://127.0.0.1:8000'
    def __init__(self):
        self.settings = Config()
        self.token = None

        if self.settings.get_use_cache():
            requests_cache.install_cache(self.settings.get_cache_folder())

    def headers(self):
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
            return self.token
        else:
            print('ERROR')
            print(response)
            return None


    #API GET ASSETS
    def get_assets(self, type=None):
        url = self.URL + '/api/asset/?format=json'
        if type:
            url += "&type=%s" % type
        json = self.request_get(url)
        return json['results']

    def put_asset(self, name, category, desc, image, file):
        url = self.URL + '/api/asset/'
        data = {'name':name,
            'description':desc,
            'category':category,
            }
        files = {
            'image':open(image, 'rb'),
            'file':open(file, 'rb'),
        }

        response = self.request_post(url, data=data, files=files, headers=self.headers(), json=False)
        return response
