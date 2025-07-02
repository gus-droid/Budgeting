"""
database.py
-----------
Database initialization and path management for the personal finance app.
Ensures the SQLite database and required tables exist. Provides a function to get the database path.
"""
import sqlite3
import os

# Get the absolute path to the database file in the db directory
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "personal_finance.db")

def get_db_path():
    """Return the absolute path to the SQLite database file.

    Returns the path to the SQLite database file used by the application. This is used by other modules to connect to the database.

    Returns:
        str: Absolute path to the SQLite database file.
    """
    return DB_PATH

# Ensure the database file exists and tables are created
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

"""
        ids to handle duplicates
 - database: personal_finance
    - Tables: 
        - 1.) budget (category, limit_amount, month, year)
        - 2.) expenses (amount, category, description, date, currency)
        
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
               currency TEXT )''')

# income table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS income (
    month TEXT,
    year INTEGER,
    amount REAL
)''')

# after making tables, commit changes
connection.commit()

# print table (budget)
# cursor.execute("SELECT * FROM budget")
# print(cursor.fetchall())

# close connection to database
connection.close()