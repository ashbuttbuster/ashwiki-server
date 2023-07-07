from datetime import datetime, timedelta
from flask import request
import random
import os
import re
from hashlib import sha256

import sqlutils

class Token:
    def __init__(self):
        pass

    def generate(self,login,expire=7):
        self.key = random.randbytes(25).hex()
        self.IP = request.environ['HTTP_X_FORWARDED_FOR']
        self.date = datetime.now() + timedelta(expire)
        self.profile = getProfileID(login)
        sqlutils.insertQuery('token',['id','profile','user_ip','expire_date'],[[self.key,str(self.profile),self.IP,self.date.strftime("%Y-%m-%d")]])

def getProfileID(login):
    return sqlutils.selectQuery('profile',['profile_id','login'],f'login="{login}"')[0]['profile_id']

def generateToken(login, expire=7):
    key = random.randbytes(25).hex()
    ip = request.environ['HTTP_X_FORWARDED_FOR']
    expire_date = datetime.now() + timedelta(expire)
    profile_id = getProfileID(login)
    sqlutils.insertQuery('token',['id','profile','user_ip','expire_date'],[[key,str(profile_id),ip,expire_date.strftime("%Y-%m-%d")]])

def validateToken(login,ip):
    profile_id = getProfileID(login)
    tokens = sqlutils.selectQuery('token',['id','profile','user_ip','expire_date'],f'profile={profile_id}')
    if len(tokens) < 1:
        return False, "Profile has no token."
    elif len(tokens) > 1:
        return False, "Несколько токенов на один профиль."
    elif tokens[0]['user_ip'] != ip:
        return False, "IP пользователя отличается от IP, привязанный к токену"
    elif datetime.now() > datetime.strptime(tokens[0]['expire_date'],"%Y-%m-%d"):
        return False, "Срок действия токена истек"
    else:
        return True

def identProfile():
    return request.cookies.get('login')

def checkLevel():      
    login = identProfile()
    if login is None:  
        return 1       
    else:              
        return sqlutils.selectQuery('profile',['login','access_level'],'login="{}"'.format(login))[0]['access_level']

def getAuthor(noteName):
    notes = sqlutils.selectQuery('notes',['notes.name','notes.author','profile.profile_id','profile.login'],'notes.name="{}"'.format(noteName),
                                 {'profile' : ['notes.author = profile.profile_id']}
                                )
    note = None
    if len(notes) > 0:
        note = notes[0]
    if note:
        return notes[0]['profile.login']
    else:
        return None
