import random
import os
import re
from hashlib import sha256

from flask import request

import sqlutils

def identProfile():
    return request.cookies.get('login')

def checkLevel():      
    login = identProfile()
    if login is None:  
        return 1       
    else:              
        return sqlutils.selectQuery('profile',['login','access_level'],'login="{}"'.format(login))[0]['access_level']

