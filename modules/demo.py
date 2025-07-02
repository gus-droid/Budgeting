"""
demo.py
-------
Handles demo mode logic and demo data for the Budgeting Tool.
"""
from modules.ux import print_info, print_warning, print_success, input_with_help
from modules.dashboard import show_dashboard
from modules.budget import budget_menu
from modules.expenses import expenses_menu
from db.db_operations import get_all_budgets, get_all_expenses, add_to_budget, add_expense, set_income
import shutil
import os
import sqlite3
import datetime
from modules.state import SESSION, UNDO_STACK
from db.database import DB_PATH

DEMO_BUDGETS = [
    ("Housing", 1200, "April", 2024),
    ("Food", 400, "April", 2024),
    ("Transport", 200, "April", 2024),
    ("Entertainment", 150, "April", 2024),
    ("Savings", 500, "April", 2024),
]
DEMO_EXPENSES = [
    (1100, "Housing", "Rent", "2024-04-01", "USD"),
    (120, "Food", "Groceries", "2024-04-03", "USD"),
    (60, "Food", "Dining Out", "2024-04-10", "USD"),
    (80, "Transport", "Gas", "2024-04-05", "USD"),
    (50, "Entertainment", "Movies", "2024-04-07", "USD"),
    (400, "Savings", "Transfer to savings", "2024-04-02", "USD"),
]
DEMO_INCOME = 3000  # Example demo income for April 2024


def run_demo_mode():
    """Run the tool in demo mode with dummy data, allowing safe exploration.

    Backs up the real database, loads demo data, and allows the user to interact with the tool in a sandboxed environment. Restores real data on exit.

    Returns:
        None
    """
    print_warning("\n=== DEMO MODE: This is a dummy population. No real data will be affected. ===")
    backup_path = DB_PATH + ".bak"
    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, backup_path)
    # Clear and repopulate demo data
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM budget")
    cursor.execute("DELETE FROM expenses")
    for b in DEMO_BUDGETS:
        cursor.execute("INSERT INTO budget (category, limit_amount, month, year) VALUES (?, ?, ?, ?)", b)
    for e in DEMO_EXPENSES:
        cursor.execute("INSERT INTO expenses (amount, category, description, date, currency) VALUES (?, ?, ?, ?, ?)", e)
    connection.commit()
    connection.close()
    # Set session to demo month/year
    SESSION['month'] = 'April'
    SESSION['year'] = 2024
    # Set demo income in the database for April 2024
    set_income('April', 2024, DEMO_INCOME)
    print_success("Demo data loaded! Explore the tool as if you were a user.")
    show_dashboard()
    print_info("Try viewing budgets, adding expenses, or using undo. When you exit demo mode, your real data will be restored.")
    # Enter a limited main loop for demo
    while True:
        print_info("\n[DEMO MODE] What do you want to do?")
        print("1. Budget (view/edit demo)")
        print("2. Expenses (view/edit demo)")
        print("3. Undo last action (demo)")
        print("4. Exit Demo Mode")
        choice = input_with_help("Choose an option:", allow_back=False)
        if choice == '1':
            budget_menu()
            show_dashboard()
        elif choice == '2':
            expenses_menu()
            show_dashboard()
        elif choice == '3':
            from modules.state import undo_last_action
            undo_last_action()
            show_dashboard()
        elif choice == '4':
            print_info("Restoring your real data...")
            if os.path.exists(backup_path):
                shutil.move(backup_path, DB_PATH)
            print_success("Exited demo mode. Your real data is restored.")
            break
        else:
            print_warning("Invalid choice.")


def other_options_menu():
    """Display the Other Options menu, including undo and demo mode.

    Shows a menu for undoing the last action, entering demo mode, or returning to the main menu.

    Returns:
        None
    """
    while True:
        print_info("\nOther Options:")
        print("1. Undo last action")
        print("2. Demo Mode (try the tool with dummy data)")
        print("3. Back to Main Menu")
        choice = input_with_help("Choose an option:")
        if choice == '1':
            from modules.state import undo_last_action
            undo_last_action()
        elif choice == '2':
            run_demo_mode()
        elif choice == '3' or choice == 'back':
            return
        else:
            print_warning("Invalid choice.") 