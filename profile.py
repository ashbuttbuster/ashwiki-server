from datetime import datetime
import random
import os
import re
from hashlib import sha256

from flask import request

import sqlutils
from main import getNote

def generateToken(login):
    key = random.randbytes(25).hex()


def identProfile():
    return request.cookies.get('login')

def checkLevel():      
    login = identProfile()
    if login is None:  
        return 1       
    else:              
        return sqlutils.selectQuery('profile',['login','access_level'],'login="{}"'.format(login))[0]['access_level']

def getAuthor(noteName):
    note = getNote(noteName)
    if note:
        return sqlutils.selectQuery('profile',['profile_id','login'],'profile_id={}'.format(note['author']))[0]['login']
    else:
        return None
