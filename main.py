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

def identProfile():
    return request.cookies.get('login') 

def getNote(name):
    result = sqlutils.selectQuery('notes',['name','caption','desc','content'],'name="{}"'.format(name))
    if len(result) == 0:
        return None
    else:
        return result[0]

def deletePageQuery(name):
    try:
        conn = sqlite3.connect('ashwiki.db')
        sql = "DELETE FROM notes WHERE name=\"{}\"".format(name)

        conn.execute(sql)
        conn.commit()
    except sqlite3.Error as error:
        print(error)
    finally:
        conn.close()

def searchResult(q):
    Q = q.lower().split(' ')
    matchd = []
    result = sqlutils.selectQuery('notes',['name','desc','caption','author'],None)        
    for row in result:
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
        elif set(Q) & set(row['desc'].lower().split(' ')):
            new_desc = ""
            for word in row['desc'].split(' '):
                if any(el in word.lower() for el in Q):
                    new_desc = new_desc + " <span class='tag'>{}</span> ".format(word)
                elif any(el in word.lower()+"." for el in Q):
                    new_desc = new_desc + " <span class='tag'>{}</span> ".format(word)
                else:
                    new_desc = new_desc + " {} ".format(word)

                row['desc'] = new_desc

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

@app.route('/edit')
def editPage():
    name = request.args.get('name')
    note = getNote(name)
    return renderHTML("edit",css="/css/style.css",title="Редактирование страницы", name=name,note=note,profile=identProfile())

@app.route('/save')
def save():
    name = request.args.get('name')
    content = request.args.get('content')
    desc = request.args.get('desc')
    caption = request.args.get('caption')
    
    if getNote(name):
        sqlutils.updateQuery('notes',[
                ['desc',desc],
                ['caption',caption],
                ['content',content]
            ],'name="{}"'.format(name))
    else:
        sqlutils.insertQuery('notes',['name','desc','caption','content','author'],[[name,desc,caption,content,'0']]) 

    return redirect('/wiki/{}'.format(name),302)
#    return renderHTML("save",css="/css/style.css",name=name)

@app.route('/delete')
def deletePage():
    name = request.args.get('name')
    q = request.args.get('q')
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
               
    return renderHTML("search",q=q,result=result,css='/css/style.css',profile=identProfile())

@app.route('/login',methods = ['POST','GET'])
def loginPage():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        profile = sqlutils.selectQuery('profile',['login','password'],'login="{}"'.format(login))
        # профиль не найден
        if len(profile) == 0: 
            return renderHTML("login",css='/css/style.css',errmsg='Такого профиля не существует! :(')
        # введен неправильный пароль
        elif profile[0]['password'] != sha256(password.encode('utf-8')).hexdigest():
            return renderHTML("login",css='/css/style.css',errmsg='Неверный пароль! :(')
        else:
            resp = make_response(renderHTML("index",css='/css/style.css',profile=login))
            resp.set_cookie('login',login)
            return resp
    else:
        return renderHTML("login",css='/css/style.css')

if __name__ == "__main__":
    app.run()
