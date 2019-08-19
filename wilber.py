#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals, print_function, division
import logging
from datetime import datetime
from gimpfu import register, main
from gui.wilber_gui import WilberGui
from distutils.version import LooseVersion
import subprocess

import gimp

import sys
from os.path import dirname, join, realpath
sys.path.insert(0, join(dirname(realpath(__file__)), 'gui/libs'))

import requests


COMMIT_NUMBER = 15
COMMIT_DATE = '2019-07-17'
VERSION = '0.10'
WILBER_URL = 'http://wilber.social'
LATEST_URL = WILBER_URL + '/static/releases/latest.txt'

logger = logging.getLogger('wilber')


def show_version():
    print("Started Wilber Social Plugin Version %s %d %s" % (COMMIT_DATE, COMMIT_NUMBER, datetime.now()))


def update(version):
    url = WILBER_URL + '/static/releases/wilber-social-{}.tar.gz'.format(version)
    command = "pip install -U --user {}".format(url)
    print(command)


def check_version():
    try:
        r = requests.get(LATEST_URL)
        latest_version = r.text.strip()
    except:
        print("ERROR: Trying to get the latest version")
    else:
        current = LooseVersion(VERSION)
        latest = LooseVersion(latest_version)
        if latest > current:
            update(latest_version)
        elif current > latest:
            print("You must be a Wizard!")


def python_wilber():
    show_version()
    check_version()
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
show_version()
main()
