import sqlite3 as sq

class DatabaseManager():

    def __init__(self, path):
        self.conn = sq.connect(path)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def create_tables(self):
        self.query('CREATE TABLE IF NOT EXISTS products (idx INTEGER PRIMARY KEY, tag text, title text, descr text, photo blob, price int)')
        self.query('CREATE TABLE IF NOT EXISTS orders (chat_id int, user_name text, user_address text, products text)')
        self.query('CREATE TABLE IF NOT EXISTS cart (chat_id int, idx text, quantity int)')
        self.query('CREATE TABLE IF NOT EXISTS categories (idx INTEGER PRIMARY KEY, title text)')
        self.query('CREATE TABLE IF NOT EXISTS questions (chat_id int, question text)')
    

    def query(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg,values)
        self.conn.commit()


    def fetchone(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg,values)
        return self.cur.fetchone()

    
    def fetchall(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg,values)
        return self.cur.fetchall()


    def __del__(self):
        self.conn.close()
