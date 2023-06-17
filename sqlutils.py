import config
import mysql.connector

DB = mysql.connector.connect(
        host='localhost',
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database='ashwiki'
)

def selectQuery(table,keywords,condition = None,innerJoin = None):
    cursor = DB.cursor()
    sql = "SELECT {} FROM {}".format(','.join(keywords),table)
    if innerJoin:
        for tab,alias in innerJoin.items():
            sql = sql + " INNER JOIN {} ON {}".format(tab,','.join(alias))
    if condition:
        sql = sql + " WHERE {}".format(condition)
    sql = sql + ';'
    print(sql)
    result = []
    cursor.execute(sql)
    for row in cursor:
        record = {}
        for i in range(len(keywords)):
            record[keywords[i].split(' as ')[-1]] = row[i]
        result.append(record)
    print(str(result))
    return result


def insertQuery(table,keywords,values):
        cursor = DB.cursor()
        strval = ""
        for l in values:
            sl = "('{}')".format("','".join(l))
            strval = strval + sl + ','
        strval = strval[:-1] + ';'

        sql = "INSERT INTO {}({}) VALUES {}".format(table,','.join(keywords),strval)
        cursor.execute(sql)
        DB.commit()
        print(sql)

def updateQuery(table,sets,condition):
    cursor = DB.cursor()
    updates = ""
    for pair in sets:
        pair[1] = "'{}'".format(pair[1])
        updates = updates + " = ".join(pair) + ","

    sql = "UPDATE {} SET {} WHERE {};".format(table,updates[:-1],condition)
    cursor.execute(sql)
    DB.commit()
    print(sql)

def deleteQuery(table,condition):
    cursor = DB.cursor()
    sql = "DELETE FROM {} WHERE {};".format(table,condition)
    print(sql)
    cursor.execute(sql)
    DB.commit()
