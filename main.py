from flask import Flask, request, send_from_directory, redirect, abort, jsonify
from flask import render_template,flash, redirect, url_for, make_response

import markdown
from markdown.extensions.wikilinks import WikiLinkExtension

import random
import os
import re
from hashlib import sha256

import profile
import sqlutils

def renderHTML(pagetype,**args):
    if 'css' not in args:
        args['css'] = '/css/style.css'
    if 'profile' not in args:
        args['profile'] = profile.identProfile()
    if 'level' not in args:
        args['level'] = profile.checkLevel()
    return render_template(pagetype+".html", **args)

def renderCookedHTML(cookie,pagetype, **args):
    result = make_response(renderHTML(pagetype,**args))
    for key in cookie:
        result.set_cookie(key,cookie[key])
    return result

def getNote(name):
    result = sqlutils.selectQuery('notes',['name','caption','annotation','content','author'],'name="{}"'.format(name))
    if len(result) == 0:
        return None
    else:
        return result[0]

def searchResult(q):
    Q = q.lower().split(' ')
    matchd = []
    result = sqlutils.selectQuery('notes',['name','annotation','caption','author'],None)        
    for row in result:
        row['author'] = sqlutils.selectQuery('profile',['profile_id','login'],'profile_id=' + str(row['author']))[0]['login']
        if any(el in row['caption'].lower() for el in re.split(" .,!?-",q.lower())):
            caption = ""

            for word in row['caption'].split(' '):
                if any(el in word.lower() for el in Q):
                    caption = caption + " <span class='tag'>{}</span> ".format(word)
                elif any(el in word.lower()+"." for el in Q):
                    caption = caption + " <span class='tag'>{}</span>. ".format(word)
                else:
                    caption = caption + " {}. ".format(word)

                row['caption'] = caption
            matchd.append(row)
        elif set(Q) & set(row['annotation'].lower().split(' ')):
            new_desc = ""
            for word in row['annotation'].split(' '):
                if any(el in word.lower() for el in Q):
                    new_desc = new_desc + " <span class='tag'>{}</span> ".format(word)
                elif any(el in word.lower()+"." for el in Q):
                    new_desc = new_desc + " <span class='tag'>{}</span> ".format(word)
                else:
                    new_desc = new_desc + " {} ".format(word)

                row['annotation'] = new_desc

            matchd.append(row)
    return matchd

app = Flask(__name__)

@app.route('/')
def index():
    return renderHTML("index")

@app.route('/wiki/<name>/')
def page_name(name):
    note = getNote(name) 

    if note:
        note['content'] = markdown.markdown(note['content'], extensions=[WikiLinkExtension(base_url='/wiki/')])
        title = note['caption']
    else:
        title = name
    return renderHTML("wiki",title=title, name=name,note=note)

@app.route('/edit',methods = ['POST','GET'])
def editPage():
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        desc = request.form['desc']
        caption = request.form['caption']
        note = getNote(name)
        if note:
            author = profile.getAuthor(name)
            print(author)
            if (profile.identProfile() == author) or (profile.checkLevel() >= 3):
                sqlutils.updateQuery('notes',[
                        ['annotation',desc],
                        ['caption',caption],
                        ['content',content],
                    ],'name="{}"'.format(name))
            else:
                abort(401)
        else:
            if profile.checkLevel() >= 2:
                sqlutils.insertQuery('notes',['name','annotation','caption','content','author'],[[name,desc,caption,content,str(sqlutils.selectQuery('profile',['profile_id','login'],'login="{}"'.format(profile.identProfile()))[0]['profile_id'])]]) 
            else:
                abort(401)
        return redirect('/wiki/{}'.format(name),302)
    else:
        name = request.args.get('name')
        author = profile.getAuthor(name)
        note = getNote(name)
        if not author:
            author = profile.identProfile()
        if (profile.identProfile() == author) or (profile.checkLevel() >= 3) or ((not note) and profile.checkLevel() >= 2):
            return renderHTML("edit",title="Редактирование страницы", name=name,note=note)
        else:
            return redirect('/login',302)

@app.route('/delete')
def deletePage():
    name = request.args.get('name')
    q = request.args.get('q')
    author = profile.getAuthor(name)
    if (profile.checkLevel() >= 4) or (profile.identProfile() == author):
        sqlutils.deleteQuery('notes','name="{}"'.format(name))
        return redirect('/search?q={}'.format(q))
    else:
        abort(401)

@app.route('/random')
def randomPage():
    notes = searchResult('')
    note = random.choice(notes)
    return redirect('/wiki/{}'.format(note['name']))

@app.route('/img/<name>')
def receiveImage(name):
    file = open('img/' + name,'rb')
    res = file.read()
    file.close()
    return res

@app.route('/css/<name>')
def receiveCSS(name):
    return send_from_directory('css', name, mimetype='text/css')

@app.route('/js/<name>')
def receiveJavaScript(name):
    return send_from_directory('js', name, mimetype='text/javascript')

@app.route('/fonts/<font>')
def receiveFont(font):
    return send_from_directory('fonts',font)

@app.route('/search')
def searchPage():
    q = request.args.get('q')
    result = searchResult(q)
               
    return renderHTML("search",q=q,result=result,css='/css/style.css',profile=profile.identProfile(),level=profile.checkLevel())

@app.route('/login',methods = ['POST','GET'])
def loginPage():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        profile = sqlutils.selectQuery('profile',['login','password'],'login="{}"'.format(login))
        # профиль не найден
        if len(profile) == 0: 
            return renderHTML("login",errmsg='Такого профиля не существует! :(')
        # введен неправильный пароль
        elif profile[0]['password'] != sha256(password.encode('utf-8')).hexdigest():
            return renderHTML("login",errmsg='Неверный пароль! :(')
        else:
            return renderCookedHTML({'login' : login},"index",profile=login)
    else:
        return renderHTML("login")

@app.route("/logout")
def actionLogout():
    resp = make_response(renderHTML("index",profile=None))
    resp.set_cookie('login','', expires=0)
    return resp

@app.route("/register", methods = ['POST','GET'])
def registerPage():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        rptpwd = request.form['rptpwd']
        profile = sqlutils.selectQuery('profile',['login'],'login="{}"'.format(login))
        if len(profile) > 0:
            return renderHTML("register",errmsg='Данный логин занят! Попробуйте другой.')
        elif not (all(x.isalnum() or (x == '_') for x in login) and login[1].isalpha()):
            return renderHTML("register",errmsg='Логин должен состоять только из букв, _ и цифр без пробелов. А также начинаться с буквы.')
        elif len(password) < 8:
            return renderHTML("register",errmsg='Минимальная длина пароля 8 символов!')
        elif password != rptpwd:
            return renderHTML("register",errmsg='Пароли не совпадают!')
        else:
            sqlutils.insertQuery('profile',['profile_id','login','password','access_level'],[[str(len(sqlutils.selectQuery('profile',['login'],None))),login,sha256(password.encode('utf-8')).hexdigest(),'2']])
            return renderCookedHTML({'login' : login},"index",profile=login)
    else:
        return renderHTML("register")

@app.route("/myip", methods=['GET'])
def getMyIP():
    return jsonify({'ip' : request.remote_addr}),200
