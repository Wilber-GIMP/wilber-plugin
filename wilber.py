#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals, print_function, division
import sys
from os.path import dirname, realpath, join
from datetime import datetime

from gimpfu import register, main
import gimp


from gui.wilber_gui import WilberGui
from gui.wilber_config import Config


COMMIT_NUMBER = 15
COMMIT_DATE = '2019-07-17'

def show_version():
    print("Started Wilber Social Plugin Version %s %d %s" % (COMMIT_DATE, COMMIT_NUMBER, datetime.now()))


def python_wilber():
    wilber = WilberGui(gimp.directory)

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
