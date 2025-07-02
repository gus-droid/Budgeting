"""
state.py
--------
Shared state for session and undo stack for the Budgeting Tool.
"""
import datetime
from db.db_operations import add_to_budget, delete_from_budget, add_expense, delete_expense

SESSION = {'month': datetime.datetime.now().strftime('%B'), 'year': datetime.datetime.now().year}
"""
Global session state for the current budgeting month and year.
"""

UNDO_STACK = []
"""
Global undo stack for storing reversible actions.
"""

def undo_last_action():
    """Undo the last action performed by the user.

    Pops the last action from the UNDO_STACK and reverses it in the database.

    Returns:
        None
    """
    if not UNDO_STACK:
        print("Nothing to undo.")
        return
    action, data = UNDO_STACK.pop()
    if action == 'delete_budget':
        # Undo a budget deletion by re-adding the budget
        category, limit_amount, month, year = data
        add_to_budget(category, limit_amount, month, year)
        print(f"Undo: Restored budget for {category} ({month} {year}).")
    elif action == 'delete_expense':
        # Undo an expense deletion by re-adding the expense
        amount, category, description, date, currency = data
        add_expense(amount, category, description, date, currency)
        print(f"Undo: Restored expense '{description}' on {date}.")
    elif action == 'add_budget':
        # Undo a budget addition by deleting the budget
        category, month, year = data
        delete_from_budget(category, month, year)
        print(f"Undo: Removed budget for {category} ({month} {year}).")
    elif action == 'add_expense':
        # Undo an expense addition by deleting the expense
        description, date = data
        delete_expense(description, date)
        print(f"Undo: Removed expense '{description}' on {date}.")
    else:
        print(f"Unknown undo action: {action}") 