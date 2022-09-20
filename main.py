from flask import Flask, request, send_from_directory, redirect
from flask import render_template,flash, redirect, url_for, make_response

import markdown
from markdown.extensions.wikilinks import WikiLinkExtension

import random
import os
import re
from hashlib import sha256

import sqlutils

def renderHTML(pagetype,**args):
    return render_template(pagetype+".html", **args)

def renderCookedHTML(cookie,pagetype, **args):
    result = make_response(renderHTML(pagetype,**args))
    for key in cookie:
        result.set_cookie(key,cookie[key])
    return result

def identProfile():
    return request.cookies.get('login') 

def checkLevel():
    login = identProfile()
    if login is None:
        return 1
    else:
        return sqlutils.selectQuery('profile',['login','access_level'],'login="{}"'.format(login))[0]['access_level']

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
    return renderHTML("index",css="/css/style.css", profile=identProfile())

@app.route('/wiki/<name>/')
def page_name(name):
    note = getNote(name) 

    if note:
        note['content'] = markdown.markdown(note['content'], extensions=[WikiLinkExtension(base_url='/wiki/')])
        title = note['caption']
    else:
        title = name
    return renderHTML("wiki",title=title, name=name,note=note,css='/css/style.css',profile=identProfile())

@app.route('/edit',methods = ['POST','GET'])
def editPage():
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        desc = request.form['desc']
        caption = request.form['caption']
    
        if getNote(name):
            sqlutils.updateQuery('notes',[
                    ['annotation',desc],
                    ['caption',caption],
                    ['content',content]
                ],'name="{}"'.format(name))
        else:
            sqlutils.insertQuery('notes',['name','annotation','caption','content','author'],[[name,desc,caption,content,'0']]) 
        return redirect('/wiki/{}'.format(name),302)
    else:
        name = request.args.get('name')
        note = getNote(name)
        author = sqlutils.selectQuery('profile',['profile_id','login'],'profile_id={}'.format(note['author']))[0]['login']
        if (identProfile() == author) or (checkLevel() >= 3):
            return renderHTML("edit",css="/css/style.css",title="Редактирование страницы", name=name,note=note,profile=identProfile())
        else:
            return redirect('/login',302)

@app.route('/delete')
def deletePage():
    name = request.args.get('name')
    q = request.args.get('q')
    if checkLevel() >= 4:
        sqlutils.deleteQuery('notes','name="{}"'.format(name))
    return redirect('/search?q={}'.format(q))

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
               
    return renderHTML("search",q=q,result=result,css='/css/style.css',profile=identProfile(),level=checkLevel())

@app.route('/login',methods = ['POST','GET'])
def loginPage():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        profile = sqlutils.selectQuery('profile',['login','password'],'login="{}"'.format(login))
        # профиль не найден
        if len(profile) == 0: 
            return renderHTML("login",css='/css/style.css',errmsg='Такого профиля не существует! :(',profile=identProfile())
        # введен неправильный пароль
        elif profile[0]['password'] != sha256(password.encode('utf-8')).hexdigest():
            return renderHTML("login",css='/css/style.css',errmsg='Неверный пароль! :(',profile=identProfile())
        else:
            return renderCookedHTML({'login' : login},"index",css='/css/style.css',profile=login)
    else:
        return renderHTML("login",css='/css/style.css',profile=identProfile())

@app.route("/logout")
def actionLogout():
    resp = make_response(renderHTML("index",css='/css/style.css'))
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
            return renderHTML("register",css='/css/style.css',errmsg='Данный логин занят! Попробуйте другой.',profile=identProfile())
        elif len(password) < 8:
            return renderHTML("register",css='/css/style.css',errmsg='Минимальная длина пароля 8 символов!',profile=identProfile())
        elif password != rptpwd:
            return renderHTML("register",css='/css/style.css',errmsg='Пароли не совпадают!')
        else:
            sqlutils.insertQuery('profile',['profile_id','login','password','access_level'],[[str(len(sqlutils.selectQuery('profile',['login'],None))),login,sha256(password.encode('utf-8')).hexdigest(),'2']])
            return renderCookedHTML({'login' : login},"index",css='/css/style.css',profile=login)
    else:
        return renderHTML("register",css='/css/style.css')
    

if __name__ == "__main__":
    app.run()
