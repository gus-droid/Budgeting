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
import time
from modules.state import SESSION, UNDO_STACK
from db.database import DB_PATH
from modules.investments import investments_menu

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
    # Clear and repopulate demo data (all tables)
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM budget")
    cursor.execute("DELETE FROM expenses")
    cursor.execute("CREATE TABLE IF NOT EXISTS investments (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL, shares REAL NOT NULL, purchase_price REAL NOT NULL, purchase_date TEXT)")
    cursor.execute("DELETE FROM investments")
    for b in DEMO_BUDGETS:
        cursor.execute("INSERT INTO budget (category, limit_amount, month, year) VALUES (?, ?, ?, ?)", b)
    for e in DEMO_EXPENSES:
        cursor.execute("INSERT INTO expenses (amount, category, description, date, currency) VALUES (?, ?, ?, ?, ?)", e)
    # Add demo investments
    demo_investments = [
        ("AAPL", 10, 150.00, "2023-10-01"),
        ("MSFT", 5, 320.00, "2023-11-15"),
        ("TSLA", 2, 700.00, "2024-01-20"),
        ("GOOGL", 3, 2700.00, "2023-12-10"),
        ("AMZN", 1, 3300.00, "2024-02-05"),
    ]
    for symbol, shares, price, date in demo_investments:
        cursor.execute("INSERT INTO investments (symbol, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)", (symbol, shares, price, date))
    connection.commit()
    connection.close()
    # Save the real session month/year to restore later
    real_month = SESSION.get('month')
    real_year = SESSION.get('year')
    # Set session to demo month/year
    SESSION['month'] = 'April'
    SESSION['year'] = 2024
    set_income('April', 2024, DEMO_INCOME)
    print_success("Demo data loaded! Explore the tool as if you were a user.")
    try:
        while True:
            show_dashboard()
            print_info("\n[DEMO MODE] What do you want to do?")
            print("1. Manage Budget & Expenses")
            print("2. Investments")
            print("3. Get Advice (chat)")
            print("4. Exit Demo Mode")
            choice = input_with_help("Choose an option:", allow_back=False)
            if choice == '1':
                # Submenu for budget and expenses
                while True:
                    print_info("\nManage Budget & Expenses:")
                    print("1. Budget")
                    print("2. Expenses")
                    print("3. Back to Demo Menu")
                    sub_choice = input_with_help("Choose an option:", allow_back=False)
                    if sub_choice == '1':
                        budget_menu(demo_mode=True)
                    elif sub_choice == '2':
                        expenses_menu(demo_mode=True)
                    elif sub_choice == '3' or sub_choice == 'back':
                        break
                    else:
                        print_warning("Invalid choice.")
                    show_dashboard()
            elif choice == '2':
                investments_menu(demo_mode=True)
            elif choice == '3':
                from modules.gemini_api import advice_menu
                advice_menu()
            elif choice == '4':
                print_info("Restoring your real data...")
                break
            else:
                print_warning("Invalid choice.")
    finally:
        # Always restore the original DB file (all tables) after demo mode
        # Wait briefly to ensure all connections are closed
        time.sleep(0.2)
        try:
            if os.path.exists(backup_path):
                # Try to remove the demo DB if it exists (to allow atomic replace)
                try:
                    if os.path.exists(DB_PATH):
                        os.remove(DB_PATH)
                except Exception as e:
                    print_warning(f"Could not remove demo DB: {e}")
                try:
                    os.replace(backup_path, DB_PATH)
                    print_success("Exited demo mode. Your real data is restored.")
                except Exception as e:
                    print_warning(f"Failed to restore your real data: {e}")
            else:
                print_warning("No backup found to restore real data. Your demo changes may persist.")
        except Exception as e:
            print_warning(f"Unexpected error during restore: {e}")
        # Restore the real session month/year
        if real_month:
            SESSION['month'] = real_month
        if real_year:
            SESSION['year'] = real_year
        return  # Do not show dashboard or any other menu after demo


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
            return  # Immediately return to main menu after demo mode
        elif choice == '3' or choice == 'back':
            return
        else:
            print_warning("Invalid choice.") 