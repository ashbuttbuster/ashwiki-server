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
        return result
    except sqlite3.Error as error:
        print('Error: ',error)
        return None
    finally:
        conn.close()

def insertQuery(table,keywords,values):
    try:
        conn = sqlite3.connect(SQLITE_FILE)

        strval = ""
        for l in values:
            sl = "('{}')".format("','".join(l))
            strval = strval + sl + ','
        strval = strval[:-1] + ';'

        sql = "INSERT INTO {}({}) VALUES {}".format(table,','.join(keywords),strval)
        conn.execute(sql)
        conn.commit()
        print(sql)
    except sqlite3.Error as error:
        print("Error: ",error)
    finally:
        conn.close()

def updateQuery(table,sets,condition):
    try:
        conn = sqlite3.connect(SQLITE_FILE)
        updates = ""
        for pair in sets:
            pair[1] = "'{}'".format(pair[1])
            updates = updates + " = ".join(pair) + ","

        sql = "UPDATE {} SET {} WHERE {};".format(table,updates[:-1],condition)
        conn.execute(sql)
        conn.commit()
        print(sql)
    except sqlite3.Error as error:
        print(sql)
        print('Error: ',error)
    finally:
        conn.close()

def deleteQuery(table,condition):
    try:
        conn = sqlite3.connect(SQLITE_FILE)
        sql = "DELETE FROM {} WHERE {};".format(table,condition)
        print(sql)
        conn.execute(sql)
        conn.commit()
    except sqlite3.Error as error:
        print(sql)
        print('Error: ',error)
    finally:
        conn.close()
