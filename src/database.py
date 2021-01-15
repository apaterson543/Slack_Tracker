#!/usr/bin/python

import sqlite3
import pandas as pd

def createDatabaseConnection():
    conn = sqlite3.connect('slack_user.db')
    return conn

def check_database():
    conn = createDatabaseConnection()
    df = pd.read_sql("Select * From userdata", con=conn)
    print(df)

if __name__ == '__main__':
    check_database()