import sys
from unified_models.models import Budget, Transaction, Category, Wallet
from datetime import datetime, date
from typing import List, Optional
import uuid

# --- Demo Data (for initial testing) ---
wallets = [Wallet(id=str(uuid.uuid4()), name='Main Account', balance=5000)]
categories = [Category(id=str(uuid.uuid4()), name='Groceries'), Category(id=str(uuid.uuid4()), name='Rent')]
budgets = []
transactions = []

# --- Formatting helpers (Cashew-inspired) ---
def format_money(amount: float) -> str:
    return f"${amount:,.2f}"

def format_date(dt: date) -> str:
    return dt.strftime('%b %d, %Y')

def print_header(title: str):
    print(f"\n\033[1;36m=== {title} ===\033[0m\n")

def print_budget(budget: Budget):
    print(f"\033[1;34m{budget.name}\033[0m | Limit: {format_money(budget.amount)} | Period: {budget.reoccurrence or 'Once'} | Start: {format_date(budget.start_date)}")

def print_transaction(tx: Transaction):
    cat = next((c.name for c in categories if c.id == tx.category_id), 'Unknown')
    print(f"{format_date(tx.date_created.date())} | {cat:12} | {format_money(tx.amount):>10} | {tx.name}")

# --- CLI Menus ---
def main_menu():
    while True:
        print_header('Cashew-Inspired Budget CLI')
        print("1. Budgets\n2. Transactions\n3. Categories\n4. Wallets\n5. Exit")
        choice = input('Choose an option: ').strip()
        if choice == '1':
            budgets_menu()
        elif choice == '2':
            transactions_menu()
        elif choice == '3':
            categories_menu()
        elif choice == '4':
            wallets_menu()
        elif choice == '5':
            print('Goodbye!')
            sys.exit(0)
        else:
            print('Invalid choice.')

def budgets_menu():
    print_header('Budgets')
    for b in budgets:
        print_budget(b)
    print("\n1. Add Budget\n2. Back")
    choice = input('Choose an option: ').strip()
    if choice == '1':
        name = input('Budget name: ')
        amount = float(input('Limit amount: '))
        rec = input('Recurrence (monthly/once): ')
        b = Budget(id=str(uuid.uuid4()), name=name, amount=amount, reoccurrence=rec, start_date=date.today())
        budgets.append(b)
        print('Budget added!')
    elif choice == '2':
        return

def transactions_menu():
    print_header('Transactions')
    for t in transactions:
        print_transaction(t)
    print("\n1. Add Transaction\n2. Back")
    choice = input('Choose an option: ').strip()
    if choice == '1':
        name = input('Transaction name: ')
        amount = float(input('Amount: '))
        cat_name = input('Category: ')
        cat = next((c for c in categories if c.name.lower() == cat_name.lower()), None)
        if not cat:
            print('Category not found.')
            return
        t = Transaction(id=str(uuid.uuid4()), name=name, amount=amount, category_id=cat.id, date_created=datetime.now())
        transactions.append(t)
        print('Transaction added!')
    elif choice == '2':
        return

def categories_menu():
    print_header('Categories')
    for c in categories:
        print(f"{c.name}")
    print("\n1. Add Category\n2. Back")
    choice = input('Choose an option: ').strip()
    if choice == '1':
        name = input('Category name: ')
        c = Category(id=str(uuid.uuid4()), name=name)
        categories.append(c)
        print('Category added!')
    elif choice == '2':
        return

def wallets_menu():
    print_header('Wallets')
    for w in wallets:
        print(f"{w.name} | Balance: {format_money(w.balance)} | Currency: {w.currency}")
    print("\n1. Add Wallet\n2. Back")
    choice = input('Choose an option: ').strip()
    if choice == '1':
        name = input('Wallet name: ')
        currency = input('Currency: ')
        w = Wallet(id=str(uuid.uuid4()), name=name, currency=currency)
        wallets.append(w)
        print('Wallet added!')
    elif choice == '2':
        return

if __name__ == '__main__':
    main_menu() 