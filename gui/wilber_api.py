# coding: utf-8
from __future__ import print_function, unicode_literals, division

import sys
import logging
from os.path import dirname, realpath, join

from wilber_config import Config
from wilber_common import ASSET_TYPE_TO_CATEGORY
from wilber_log import logger

PLUGINS_PATH = dirname(realpath(__file__))
WILBER_LIBS_PATH = join(PLUGINS_PATH, 'libs')
sys.path.insert(0, WILBER_LIBS_PATH)

import requests


logger = logging.getLogger('wilber.api')


class WilberAPIClient(object):
    def __init__(self):
        self.settings = Config()
        self.URL = self.settings.get_server_url()
        self.token = None

        self.next_url = None

    def headers(self):
        if not self.token:
            if self.settings.token:
                self.token = self.settings.token
            else:
                self.login(self.settings.username, self.settings.password)
        if self.token:
            return {'Authorization': 'Token %s' % self.token}
        return {}

    def request_get(self, uri, json=True, headers=True, **kwargs):
        try:
            if headers:
                response = requests.get(uri, headers=self.headers(), **kwargs)
            else:
                response = requests.get(uri, **kwargs)

        except requests.exceptions.ConnectionError as e:
            logger.error(e)
        else:
            if json:
                self.check_response(response)
                return response.json()
            return response

    def request_post(self, url, data={}, headers={}, files={}, json=True):
        response = requests.post(url, data=data, headers=headers, files=files)
        if response.status_code > 399:
            logger.warning(response.content)
        if json:
            return response.json()
        return response

    def check_response(self, response):
        j = response.json()
        if 'detail' in j:
            if j['detail'] == 'Invalid token.':
                logger.error('Invalid token')

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
        return token

    def login(self, username, password):
        url = self.URL + '/api-token-auth/'
        data = {'username': username, 'password': password}

        response = self.request_post(url, data)

        token_key = 'token'

        if token_key in response:
            self.token = response[token_key]
            logger.info("logged in succesfully into Wilber Social")
            return self.token
        else:
            logger.error("Failed to login in Wilber Social")

    def get_assets(self, type_=None, query=None, more=False):
        if more and self.next_url:
            url = self.next_url
        else:
            url = self.URL + '/api/asset/'
        logger.info('Connecting to %s' % url)

        params = {"format": "json"}
        if type_:
            params["category"] = ASSET_TYPE_TO_CATEGORY[type_]
        if query:
            params["search"] = query

        json_data = self.request_get(url, params=params, headers=False)
        if json_data and 'results' in json_data:
            self.next_url = json_data['next']
            return json_data['results'], json_data['next']

        return None, None

    def put_asset(self, name, category, description, image, file):
        url = self.URL + '/api/asset/'
        data = {'name': name,
                'description': description,
                'category': category,
                }
        files = {'file': open(file, 'rb'), }
        if image:
            files["image"] = open(image, "rb")

        response = self.request_post(url, data=data, files=files, headers=self.headers(), json=False)
        return response
