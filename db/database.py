# import sql database 
import sqlite3

# connection object
# name of database is personal_finance
connection = sqlite3.connect("personal_finance.db")

#cursor object
cursor = connection.cursor()

"""
        ids to handle duplicates
 - database: personal_finance
    - Tables: 
        - 1.) budget (category, limit_amount, month, year)
        - 2.) expenses (amount, category, description, date, currency, converted_amount_usd)
        
"""

# budget table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS budget (
               id INTEGER,
               category TEXT,
               limit_amount REAL,
               month TEXT,
               year INTEGER
                )''')

# expenses table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
               id INTEGER,
               amount REAL,
               category TEXT,
               description TEXT,
               date DATE,
               currency TEXT,
               converted_amount_usd REAL )''')

# after making tables, commit changes
connection.commit()

# print table (budget)
# cursor.execute("SELECT * FROM budget")
# print(cursor.fetchall())

# close connection to database
connection.close()