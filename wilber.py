#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals, print_function
import sys
from os.path import dirname, realpath, join
from datetime import datetime


PLUGINS_PATH = dirname(realpath(__file__))
WILBER_PATH = join(PLUGINS_PATH, 'wilber')
WILBER_LIBS_PATH = join(WILBER_PATH, 'libs')

sys.path.insert(0, WILBER_LIBS_PATH)

from gimpfu import register, main

from gui.wilber_gui import WilberGui
from gui.wilber_config import Config


COMMIT_NUMBER = 7
COMMIT_DATE = '2019-07-15'

def show_version():
    print("Started Wilber Plugin Version %s %d %s" % (COMMIT_DATE, COMMIT_NUMBER, datetime.now()))


settings = Config(WILBER_PATH)
settings.save()

#if settings.get_use_cache():
#    requests_cache.install_cache(join(WILBER_PATH,'wilber_cache'))


def python_wilber():
    wilber = WilberGui(settings)

register_params = {
    'proc_name': 'wilber_asset_manager',
    'blurb': 'Manage GIMP Assets',
    'help': 'Manage GIMP Assets',
    'author': 'Joao, Robin, Darpan',
    'copyright': 'João, Robin, Darpan',
    'date': '2019',
    'label': 'Manage GIMP Assets',
    'imagetypes': None,
    'params': [],
    'results': [],
    'function': python_wilber,
    'menu': '<Toolbox>/File',
    'domain': None,
    'on_query': None,
    'on_run': None,
}

register(**register_params)
#show_version()
main()
