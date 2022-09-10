from flask import Flask, request, send_from_directory, redirect
from flask import render_template,flash, redirect, url_for

import markdown
from markdown.extensions.wikilinks import WikiLinkExtension

import random
import os
import re
import sqlite3

SQLITE_FILE = 'ashwiki.db'

def selectQuery(table,keywords,condition):
    try:
        conn = sqlite3.connect(SQLITE_FILE)
        sql = "SELECT {} FROM {}".format(','.join(keywords),table)
        if condition:
            sql = sql + " WHERE {};".format(condition)
        print(sql)
        cursor = conn.execute(sql)
        result = []

        for row in cursor:
            record = {}
            for i in range(len(keywords)):
                record[keywords[i]] = row[i]
            result.append(record)
            print(record)
        return result
    except sqlite3.Error as error:
        print('Error: ',error)
        return None
    finally:
        conn.close()

def renderHTML(pagetype,**args):
    return render_template(pagetype+".html", **args)

def getNote(name):
    result = selectQuery('notes',['name','caption','desc','content'],'name="{}"'.format(name))
    if len(result) == 0:
        return None
    else:
        return result[0]

def savePage(name,desc,caption,content):
    try:
        conn = sqlite3.connect('ashwiki.db')
        if getNote(name):
            sql = "UPDATE notes SET caption = '{}',desc = '{}', content = '{}' WHERE name = '{}';".format(caption,desc,content,name)
        else:
            sql = "INSERT INTO notes(name,caption,desc,content,author) VALUES ('{}','{}','{}','{}','{}')".format(name,caption,desc,content,'0')
        conn.execute(sql)
        conn.commit()
    except sqlite3.Error:
        print(error)
    finally:
        conn.close()

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
    result = selectQuery('notes',['name','desc','caption','author'],None)        
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
    return renderHTML("index",css="/css/style.css")

@app.route('/wiki/<name>/')
def page_name(name):
    note = getNote(name) 

    if note:
        note['content'] = markdown.markdown(note['content'], extensions=[WikiLinkExtension(base_url='/wiki/')])
        title = note['caption']
    else:
        title = name
    return renderHTML("wiki",title=title, name=name,note=note,css='/css/style.css')

@app.route('/edit')
def editPage():
    name = request.args.get('name')
    note = getNote(name)
    return renderHTML("edit",css="/css/style.css",title="Редактирование страницы", name=name,note=note)

@app.route('/save')
def save():
    name = request.args.get('name')
    content = request.args.get('content')
    desc = request.args.get('desc')
    caption = request.args.get('caption')
    
    savePage(name,desc,caption,content)

    return redirect('/wiki/{}'.format(name),302)
#    return renderHTML("save",css="/css/style.css",name=name)

@app.route('/delete')
def deletePage():
    name = request.args.get('name')
    q = request.args.get('q')
    deletePageQuery(name)
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
               
    return renderHTML("search",q=q,result=result,css='/css/style.css')

if __name__ == "__main__":
    app.run()
