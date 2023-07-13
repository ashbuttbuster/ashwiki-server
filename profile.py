from datetime import datetime, timedelta
from flask import request
import random
import os
import re
from hashlib import sha256

import sqlutils

class Token:
    def __init__(self,login=None):
        if login:
            self.profile = getProfileID(login)
            if len(self.findTokenByLogin(login)) > 0:
                token = self.findTokenByID(self.profile)[0]
                self.key = token['id']
                self.IP = token['user_ip']
                self.date = token['expire_date']
    
    def findTokenByLogin(self,login):
        return sqlutils.selectQuery('token',['id','profile','user_ip','expire_date','verified'],f'profile={getProfileID(login)}')

    def findTokenByID(self,id):
        return sqlutils.selectQuery('token',['id','profile','user_ip','expire_date','verified'],f'profile={id}')
    def generate(self,login,expire=7):
        sqlutils.deleteQuery('token',f'profile={getProfileID(login)}')
        self.key = random.randbytes(25).hex()
        self.IP = getRealIP()
        self.date = datetime.now() + timedelta(expire)
        self.profile = getProfileID(login)
        sqlutils.insertQuery('token',['id','profile','user_ip','expire_date'],[[self.key,str(self.profile),self.IP,self.date.strftime("%Y-%m-%d")]])
    
    def validate(self):
        tokens = self.findTokenByID(self.profile)
        ip = getRealIP()
        if len(tokens) == 0:
            return False, "Требуется токен для входа."
        elif len(tokens) > 1:
            return False, "Несколько токенов на один профиль."
        elif tokens[0]['verified'] == 0:
            return False, "Токен не подтвержден"
        elif self.IP != ip:
            return False, "IP пользователя отличается от IP, привязанный к токену"
        elif datetime.now() > self.date:
            return False, "Срок действия токена истек"
        else:
            return True, None

def getRealIP():
    headers_list = request.headers.getlist("HTTP_X_FORWARDED_FOR")
    http_x_real_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    return headers_list[0] if headers_list else http_x_real_ip
    

def getProfileID(login):
    return sqlutils.selectQuery('profile',['profile_id','login'],f'login="{login}"')[0]['profile_id']

def identProfile(token=None):
    if token is None:
        token = request.cookies.get('token')
        if token is None:
            return None
        t1 = sqlutils.selectQuery('token',['token.id','token.profile','profile.profile_id','profile.login'],f'token.id="{token}"', {'profile' : ['token.profile = profile.profile_id']})
        return t1[0]['profile.login']
    else:
        t1 = sqlutils.selectQuery('token',['token.id','token.profile','profile.profile_id','profile.login'],f'token.id="{token}"', {'profile' : ['token.profile = profile.profile_id']})
        return t1[0]['profile.login']

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
