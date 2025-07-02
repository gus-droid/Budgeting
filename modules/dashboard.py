"""
dashboard.py
------------
Handles dashboard display and reporting for the Budgeting Tool.
"""
from modules.ux import print_info, print_warning, get_category_color_map, per_category_bar_chart
from db.db_operations import get_all_budgets, get_all_expenses
import datetime
from modules.state import SESSION
from colorama import Fore, Style


def show_dashboard():
    """Display the main budget dashboard with totals and category breakdowns.

    Shows the current month's budget, total spent, percent used, and a per-category bar chart. Warns if viewing a non-current month.

    Returns:
        None
    """
    month = SESSION['month']
    year = SESSION['year']
    budgets = get_all_budgets()
    expenses = get_all_expenses()
    total_budget = sum(row[1] for row in budgets if row[2] == month and str(row[3]) == str(year))
    budget_cats = {row[0] for row in budgets if row[2] == month and str(row[3]) == str(year)}
    total_spent = sum(row[0] for row in expenses if row[1] in budget_cats)
    percent_used = (total_spent / total_budget * 100) if total_budget else 0
    color = Fore.GREEN if percent_used < 80 else (Fore.YELLOW if percent_used < 100 else Fore.RED)
    spent_color = Fore.RED if total_spent > total_budget else Fore.MAGENTA
    print(f"{Fore.CYAN}Month: {month} {year}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total Budget: {Fore.GREEN}${total_budget}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total Spent: {spent_color}${total_spent}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Budget Used: {color}{percent_used:.1f}%{Style.RESET_ALL}")
    if (month != datetime.datetime.now().strftime('%B') or str(year) != str(datetime.datetime.now().year)):
        print_warning(f"Note: You are viewing {month} {year}, not the current month.")
    print_info("\nSpending by Category:")
    cat_limits = {row[0]: row[1] for row in budgets if row[2] == month and str(row[3]) == str(year)}
    cat_spent = {cat: 0 for cat in cat_limits}
    for amt, cat, *_ in expenses:
        if cat in cat_spent:
            cat_spent[cat] += amt
    color_map = get_category_color_map(list(cat_limits.keys()))
    per_category_bar_chart(cat_spent, cat_limits, color_map=color_map)
    print_info("\nType 'help' at any menu for guidance.") 