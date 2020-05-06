## Should only be ran once to set up the database

import sqlite3

DATABASE = 'ecco.db'

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

c.execute('CREATE TABLE wordtable (word text, translation text, date text, userid integer)')
c.execute('CREATE TABLE historytable (word text, translation text, date text, userid integer)')
conn.commit()

conn.close()
