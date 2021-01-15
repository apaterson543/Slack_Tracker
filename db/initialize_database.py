import sqlite3

conn = sqlite3.connect('../slack_user.db')

conn.execute('''CREATE TABLE USERS
                (id         INTEGER PRIMARY KEY AUTOINCREMENT,
                 username   TEXT                NOT NULL,
                 presence   INTEGER             NOT NULL,
                 total_time TEXT); ''')
conn.execute('''CREATE TABLE DATE
                (start_date TEXT,
                 start_time TEXT);''')