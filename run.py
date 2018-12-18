# encoding: utf-8
import base64
import hashlib
import json
import multiprocessing
import signal
import sys
import pyDes
import requests
from prettytable import PrettyTable

from function import API

def destroy():
    print("#### Good bye ! Have a good day ! ####")

api = API()
api.init()
api.menu()