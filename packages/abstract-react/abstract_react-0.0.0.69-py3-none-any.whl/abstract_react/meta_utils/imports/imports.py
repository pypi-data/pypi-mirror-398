from abstract_flask import get_request_data,Flask, render_template, abort,Blueprint,jsonify,request
from abstract_utilities import eatAll,get_all_directories,get_all_files,get_logFile,make_list
logOn = True
def logit(logger,message,*args):
    if logOn:
        logger(message,*args)
from PIL import Image
from io import BytesIO
import os,glob,requests,urllib.parse,re
from datetime import datetime
from typing import *
import re
from abstract_webtools.managers.urlManager import *
