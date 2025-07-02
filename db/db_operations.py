import sqlite3
from .database import get_db_path

'''
    Functions for the budgets table (these will be sql querys)
'''
# list all the contents of the table
def get_all_budgets():
    """Retrieve all budget records from the database.

    Executes a SELECT query to fetch all rows from the budget table, returning each as a tuple.

    Returns:
        list of tuple: Each tuple contains (category, limit_amount, month, year).

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the query.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT category, limit_amount, month, year FROM budget")
    results = cursor.fetchall()
    connection.close()
    return results

# add a query to a table
def add_to_budget(category, limit_amount, month, year):
    """Add a new budget record to the database.

    Inserts a new row into the budget table with the specified category, limit, month, and year.

    Args:
        category (str): Budget category name.
        limit_amount (float): Limit for the category.
        month (str): Month for the budget.
        year (int): Year for the budget.

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the insert.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("INSERT INTO budget (category, limit_amount, month, year) VALUES (?, ?, ?, ?)",
                   (category, float(limit_amount), month, int(year)))
    connection.commit()
    connection.close()

# delete a query from the table
def delete_from_budget(category, month, year):
    """Delete a budget record from the database by category, month, and year.

    Removes a row from the budget table matching the given category, month, and year.

    Args:
        category (str): Budget category name.
        month (str): Month for the budget.
        year (int): Year for the budget.

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the deletion.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM budget WHERE category=? AND month=? AND year=?",
                   (category, month, int(year)))
    connection.commit()
    connection.close()

'''
    Functions for the expenses table
'''

# list all the expenses
def get_all_expenses():
    """Retrieve all expense records from the database.

    Executes a SELECT query to fetch all rows from the expenses table, returning each as a tuple.

    Returns:
        list of tuple: Each tuple contains (amount, category, description, date, currency).

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the query.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT amount, category, description, date, currency FROM expenses")
    results = cursor.fetchall()
    connection.close()
    return results

# add to expenses
def add_expense(amount, category, description, date, currency):
    """Add a new expense record to the database.

    Inserts a new row into the expenses table with the specified details.

    Args:
        amount (float): Expense amount.
        category (str): Expense category.
        description (str): Description of the expense.
        date (str): Date of the expense (YYYY-MM-DD).
        currency (str): Currency code.

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the insert.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("INSERT INTO expenses (amount, category, description, date, currency) VALUES (?, ?, ?, ?, ?)",
                   (float(amount), category, description, date, currency))
    connection.commit()
    connection.close()

# delete from expense
def delete_expense(description, date):
    """Delete an expense record from the database by description and date.

    Removes a row from the expenses table matching the given description and date.

    Args:
        description (str): Description of the expense.
        date (str): Date of the expense (YYYY-MM-DD).

    Raises:
        sqlite3.DatabaseError: If a database error occurs during the deletion.
    """
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM expenses WHERE description=? AND date=?",
                   (description, date))
    connection.commit()
    connection.close()

def get_income(month, year):
    """Retrieve the income for a given month and year from the database."""
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("SELECT amount FROM income WHERE month=? AND year=?", (month, int(year)))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None

def set_income(month, year, amount):
    """Set or update the income for a given month and year in the database."""
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM income WHERE month=? AND year=?", (month, int(year)))
    cursor.execute("INSERT INTO income (month, year, amount) VALUES (?, ?, ?)", (month, int(year), float(amount)))
    connection.commit()
    connection.close()

def delete_income(month, year):
    """Delete the income record for a given month and year from the database."""
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute("DELETE FROM income WHERE month=? AND year=?", (month, int(year)))
    connection.commit()
    connection.close()