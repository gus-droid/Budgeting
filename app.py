# library that allows us to show tabular data
from tabulate import tabulate
from colorama import init, Fore, Style
import random
import time
import shutil
import os
import sqlite3
from dotenv import load_dotenv
import requests
import textwrap

'''
display on command line to user 
"What do you want to do today?":
1.) budget
2.) Check my expenses
3.) Get Advice (this is where they can type a question and it'll be sent to gemini api)

If they pick 1:
    - 1.) add category, limit_amount, month, year
    - 2.) Delete category, limit_amount, month, year
    - 3.) show budget

If they pick 2:
    - 1.) Add amount, category, description, date, currency, converted_amount_usd
    - 2.) Delete amount, category, description, date, currency, converted_amount_usd
    - 3.) show expenses
'''

import sys
from db.db_operations import (
    get_all_budgets, add_to_budget, delete_from_budget,
    get_all_expenses, add_expense, delete_expense
)

import datetime

init(autoreset=True)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

# --- UX Helper Functions ---
def print_success(msg, **kwargs):
    """Print a success message in green text.

    Displays the provided message in green color to indicate a successful operation.

    Args:
        msg (str): The message to display.
        **kwargs: Additional keyword arguments passed to print().
    """
    print(Fore.GREEN + msg + Style.RESET_ALL, **kwargs)

def print_error(msg, **kwargs):
    """Print an error message in red text.

    Displays the provided message in red color to indicate an error or failure.

    Args:
        msg (str): The error message to display.
        **kwargs: Additional keyword arguments passed to print().
    """
    print(Fore.RED + msg + Style.RESET_ALL, **kwargs)

def print_info(msg, **kwargs):
    """Print an informational message in cyan text.

    Displays the provided message in cyan color to indicate informational output.

    Args:
        msg (str): The informational message to display.
        **kwargs: Additional keyword arguments passed to print().
    """
    print(Fore.CYAN + msg + Style.RESET_ALL, **kwargs)

def print_warning(msg, **kwargs):
    """Print a warning message in yellow text.

    Displays the provided message in yellow color to indicate a warning or caution.

    Args:
        msg (str): The warning message to display.
        **kwargs: Additional keyword arguments passed to print().
    """
    print(Fore.YELLOW + msg + Style.RESET_ALL, **kwargs)

def ask_confirm(prompt):
    """Prompt the user for a yes/no confirmation.

    Continuously prompts the user until they enter 'y' or 'n'. Returns True for 'y', False for 'n'.

    Args:
        prompt (str): The confirmation prompt to display.

    Returns:
        bool: True if the user confirms ('y'), False otherwise ('n').
    """
    while True:
        ans = input(Fore.YELLOW + prompt + ' (y/n): ' + Style.RESET_ALL + " ").strip().lower()
        if ans in ['y', 'n']:
            return ans == 'y'
        print_error('Please enter y or n.')

def input_with_help(prompt, help_text=None, allow_back=True):
    """Prompt the user for input, optionally providing help text and a 'back' option.

    Prompts the user for input, displaying help text if requested. Allows the user to type 'back' to return if allow_back is True.

    Args:
        prompt (str): The input prompt to display.
        help_text (str, optional): Help text to show if the user types 'help'.
        allow_back (bool, optional): Whether to allow the user to type 'back' to return. Defaults to True.

    Returns:
        str: The user's input, or 'back' if the user chooses to go back.
    """
    while True:
        val = input(Fore.CYAN + prompt + (" (type 'help' for info)" if help_text else "") + Style.RESET_ALL + " ").strip()
        if allow_back and val.lower() == 'back':
            return 'back'
        if help_text and val.lower() == 'help':
            print_info(help_text)
            continue
        return val

# Session memory for month/year
SESSION = {'month': datetime.datetime.now().strftime('%B'), 'year': datetime.datetime.now().year}

# --- Fake API Calls ---
def fake_carbon_api(company):
    print_info(f"[FAKE API] Carbon emissions for {company}: 123kg CO2/year")
    print_info(f"[FAKE API] Ethical rating for {company}: Ethical")
    print_info(f"[FAKE API] Suggested alternatives: GreenCo, EcoBuy")

def get_gemini_budget_split(goals, income, rent, bills_str):
    """Ask Gemini for a unique budget split based on user goals, income, rent, and fixed bills."""
    if not GEMINI_API_KEY:
        return None
    prompt = (
        "Given the following financial goals: " + ", ".join(goals) + ". "
        f"The user's monthly after-tax income is ${income:.2f}. "
        f"Their rent/mortgage is ${rent:.2f} per month. "
        f"Their fixed monthly bills/expenses are: {bills_str}. "
        "Suggest a practical budget split (categories, percentages, and a short description for each) that best helps achieve these goals and covers their fixed expenses. "
        "Return the result as a JSON list of objects with keys: 'name', 'percent', and 'description'. "
        "Percentages should sum to 100 and be rounded to the nearest integer."
    )
    conversation = [
        {"role": "user", "parts": [{"text": prompt}]}
    ]
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            json={"contents": conversation},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', None)
            import json as _json
            # Try to extract JSON from the response
            if answer:
                try:
                    # Find the first JSON array in the text
                    start = answer.find('[')
                    end = answer.rfind(']')
                    if start != -1 and end != -1:
                        json_str = answer[start:end+1]
                        split = _json.loads(json_str)
                        # Convert to expected format and round percentages
                        rounded_split = []
                        for c in split:
                            percent = int(round(float(c["percent"])))
                            rounded_split.append({"name": c["name"], "percent": percent, "examples": [c.get("description","")]})
                        return rounded_split
                except Exception as ex:
                    pass
    except Exception as ex:
        pass
    return None

def format_split_preview(split, income, is_gemini=False):
    preview = []
    for cat in split:
        percent = int(round(cat["percent"]))
        amt = round(income * percent / 100, 2)
        # Wrap description for better table formatting
        desc = ", ".join(cat["examples"]) if cat.get("examples") else ""
        desc_wrapped = "\n".join(textwrap.wrap(desc, width=48))
        preview.append([
            cat["name"],
            f"{percent}%",
            f"${amt}",
            desc_wrapped
        ])
    headers = ["Category", "%", "Amount", "Description" if is_gemini else "Example Expenses"]
    return tabulate(preview, headers=headers, tablefmt="fancy_grid", stralign="center", numalign="center")

# --- Automatic Budget Setup Wizard ---
def setup_automatic_budget():
    print_info("\n--- Automatic Budget Setup Wizard ---")
    while True:
        income = input_with_help(
            "What is your monthly after-tax income? $",
            help_text="Enter your take-home pay after taxes. Example: 3000"
        )
        if income == 'back':
            return
        try:
            income = float(income)
            if income <= 0:
                print_error("Income must be positive.")
                continue
            break
        except ValueError:
            print_error("Please enter a valid number.")

    # Ask for rent
    while True:
        rent = input_with_help(
            "What is your monthly rent or mortgage payment? $",
            help_text="Enter the amount you pay for rent or mortgage each month. Example: 1200"
        )
        if rent == 'back':
            return
        try:
            rent = float(rent)
            if rent < 0:
                print_error("Rent cannot be negative.")
                continue
            break
        except ValueError:
            print_error("Please enter a valid number.")

    # Ask for fixed bills/expenses
    fixed_bills = []
    print_info("\nList any fixed bills or recurring expenses you have each month (e.g., utilities, insurance, subscriptions). Type 'done' when finished.")
    while True:
        bill_name = input_with_help("Bill/Expense name (or 'done' to finish):")
        if bill_name.strip().lower() == 'done':
            break
        if not bill_name:
            print_error("Name cannot be empty.")
            continue
        bill_amt = input_with_help(f"Monthly amount for {bill_name}: $")
        if bill_amt == 'back':
            return
        try:
            bill_amt = float(bill_amt)
            if bill_amt < 0:
                print_error("Amount cannot be negative.")
                continue
            fixed_bills.append((bill_name, bill_amt))
        except ValueError:
            print_error("Please enter a valid number.")

    print_info("\nSummary of your fixed expenses:")
    print(f"- Rent/Mortgage: ${rent:.2f}")
    if fixed_bills:
        for name, amt in fixed_bills:
            print(f"- {name}: ${amt:.2f}")
    else:
        print("- No additional fixed bills/expenses listed.")

    print_info("\nWhat are your top financial goals? (Type numbers separated by commas)")
    goals = [
        "Build emergency fund",
        "Pay off debt",
        "Save for retirement",
        "Save for a big purchase (house, car, etc.)",
        "Other (type your own)"
    ]
    for i, g in enumerate(goals, 1):
        print(f"{i}. {g}")
    chosen = input_with_help("Your choices:", help_text="Example: 1,3 for emergency fund and retirement.")
    if chosen == 'back':
        return
    chosen_goals = []
    for idx in chosen.split(','):
        idx = idx.strip()
        if idx.isdigit() and 1 <= int(idx) <= len(goals):
            if int(idx) == len(goals):
                custom = input_with_help("Type your custom goal:")
                if custom == 'back':
                    return
                chosen_goals.append(custom)
            else:
                chosen_goals.append(goals[int(idx)-1])
    print_success("\nThank you! Here are your selected goals:")
    for g in chosen_goals:
        print(f"- {g}")

    # --- Gemini API for unique split ---
    print_info("\nAsking Gemini for a budget split tailored to your goals and fixed expenses...")
    # Compose a more detailed prompt
    bills_str = ", ".join([f"{name} (${amt:.2f})" for name, amt in fixed_bills]) if fixed_bills else "None"
    split = get_gemini_budget_split(chosen_goals, income, rent, bills_str)
    if split:
        print_success("Gemini suggested the following split:")
        print(format_split_preview(split, income, is_gemini=True))
        use_gemini = input_with_help("Use this split? (y/n):", help_text="Type 'y' to accept Gemini's suggestion or 'n' to customize.").strip().lower()
        if use_gemini == 'back':
            return
        if use_gemini == 'y':
            categories = split
        else:
            categories = None
    else:
        print_warning("Could not get a unique split from Gemini. Using the default 50/30/20 rule.")
        categories = None

    # Default 50/30/20 split if Gemini fails or user declines
    if not categories:
        default_split = [
            {"name": "Needs", "percent": 50, "examples": ["Rent", "Groceries", "Utilities", "Insurance", "Transportation", "Minimum debt payments"]},
            {"name": "Wants", "percent": 30, "examples": ["Dining out", "Entertainment", "Shopping", "Travel", "Hobbies"]},
            {"name": "Savings/Debt", "percent": 20, "examples": ["Emergency fund", "Retirement", "Extra debt payments", "Investments"]},
        ]
        # Calculate user's actual needs percent
        needs_amount = rent + sum(amt for _, amt in fixed_bills)
        needs_percent = int(round((needs_amount / income) * 100))
        if needs_percent > 50:
            # Take away from Wants
            excess = needs_percent - 50
            new_wants = default_split[1]["percent"] - excess
            if new_wants < 0:
                print_warning(f"Your fixed needs exceed 80% of your income! Setting Wants to 0% and increasing Needs to {needs_percent}%. Consider reducing fixed expenses.")
                default_split[0]["percent"] = needs_percent
                default_split[1]["percent"] = 0
                # Savings/Debt stays at 20%
            else:
                print_warning(f"Your fixed needs exceed 50% of your income. Reducing Wants to {new_wants}% and increasing Needs to {needs_percent}%.")
                default_split[0]["percent"] = needs_percent
                default_split[1]["percent"] = new_wants
        # Round all percentages to nearest integer
        for cat in default_split:
            cat["percent"] = int(round(cat["percent"]))
        print_info("\nBased on the 50/30/20 rule, here's a suggested split:")
        print(format_split_preview(default_split, income, is_gemini=False))
        categories = default_split

    # Customization
    custom = input_with_help("Would you like to customize your categories or percentages? (y/n):", help_text="Type 'y' to edit categories or 'n' to accept the current split.").strip().lower()
    if custom == 'back':
        return
    if custom == 'y':
        print_info("\nLet's customize your budget categories.")
        while True:
            print_info("\nCurrent categories:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat['name']} ({cat['percent']}%)")
            print(f"{len(categories)+1}. Add new category")
            print(f"{len(categories)+2}. Done customizing")
            choice = input_with_help("Choose a category to edit, add, or finish:")
            if choice == 'back':
                return
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(categories):
                    # Edit existing
                    cat = categories[idx-1]
                    new_name = input_with_help(f"Rename '{cat['name']}' (or press Enter to keep):")
                    if new_name == 'back':
                        return
                    if new_name:
                        cat['name'] = new_name
                    new_percent = input_with_help(f"Change percentage for '{cat['name']}' (current: {cat['percent']}%) (or press Enter to keep):")
                    if new_percent == 'back':
                        return
                    if new_percent:
                        try:
                            val = float(new_percent)
                            if 0 < val <= 100:
                                cat['percent'] = val
                            else:
                                print_error("Percentage must be between 0 and 100.")
                        except ValueError:
                            print_error("Invalid number.")
                elif idx == len(categories)+1:
                    # Add new
                    new_name = input_with_help("New category name:")
                    if new_name == 'back':
                        return
                    if not new_name:
                        print_error("Name cannot be empty.")
                        continue
                    new_percent = input_with_help(f"Percentage for '{new_name}':")
                    if new_percent == 'back':
                        return
                    try:
                        val = float(new_percent)
                        if 0 < val <= 100:
                            categories.append({"name": new_name, "percent": val, "examples": []})
                        else:
                            print_error("Percentage must be between 0 and 100.")
                    except ValueError:
                        print_error("Invalid number.")
                elif idx == len(categories)+2:
                    # Done
                    break
            else:
                print_error("Invalid choice.")
        # After editing, check total
        total = sum(cat['percent'] for cat in categories)
        if abs(total - 100) > 0.01:
            print_warning(f"\nWarning: Your total is {total}%. Adjusting to 100%. Proportionally scaling.")
            for cat in categories:
                cat['percent'] = round(cat['percent'] * 100 / total, 2)

    # Save to database
    now = datetime.datetime.now()
    month = now.strftime("%B")
    year = now.year
    print_info("\nSaving your budget...")
    for cat in categories:
        limit = round(income * cat['percent'] / 100, 2)
        add_to_budget(cat['name'], limit, month, year)
    print_success("Budget saved!")
    # Show final table
    print_info("\nYour automatic budget:")
    table = [[cat['name'], f"{cat['percent']}%", f"${round(income * cat['percent'] / 100, 2)}"] for cat in categories]
    print(tabulate(table, headers=["Category", "%", "Amount"], tablefmt="fancy_grid"))
    print_info("\nYou can always edit your budget categories later from the Budget menu.")

# --- Progress Bar ---
def progress_bar(task="Processing", duration=1.5):
    print(f"{Fore.CYAN}{task}...{Style.RESET_ALL}", end=" ")
    for _ in range(10):
        print(Fore.YELLOW + "█", end="", flush=True)
        time.sleep(duration / 10)
    print(Style.RESET_ALL)

# --- Pastel Color Palette for Categories (ANSI 256-color codes) ---
# Reserved CLI colors: cyan, yellow, green, red (do not use for categories)
# Do not use white (15, 231)
PASTEL_ANSI_CODES = [186, 189, 151, 159, 117, 180, 144, 223, 222, 221, 225, 224, 194, 191, 153, 150, 186, 189, 151, 159, 117, 180, 144, 223, 222, 221, 225, 224, 194, 191]
PASTEL_COLORS = [f"\033[38;5;{code}m" for code in PASTEL_ANSI_CODES]
RESET_COLOR = Style.RESET_ALL

# --- Category Color Assignment ---
def get_category_color_map(categories):
    color_map = {}
    n = len(categories)
    if n > len(PASTEL_COLORS):
        print_warning(f"More than {len(PASTEL_COLORS)} categories! Some colors will repeat.")
    for i, cat in enumerate(categories):
        color_map[cat] = PASTEL_COLORS[i % len(PASTEL_COLORS)]
    return color_map

# --- Per-Category Bar Chart ---
def per_category_bar_chart(cat_spent, cat_limits, width=40, color_map=None):
    for cat, limit in cat_limits.items():
        used = cat_spent.get(cat, 0)
        color = color_map.get(cat, RESET_COLOR) if color_map else RESET_COLOR
        if limit == 0:
            percent = 0
        else:
            percent = min(used / limit, 1)
        filled = int(percent * width)
        left = width - filled
        bar = f"{color}{'█' * filled}{RESET_COLOR}"
        if left > 0:
            pattern = ''.join(['░' if i % 2 == 0 else '▒' for i in range(left)])
            bar += f"{Style.BRIGHT}{pattern}{RESET_COLOR}"
        percent_str = f"{percent*100:.1f}%"
        print(f"|{bar}| {color}{cat:<15}{RESET_COLOR} {Fore.YELLOW}${used:.2f}{Style.RESET_ALL} of ${limit:.2f} ({percent_str})")

# --- Dashboard ---
def show_dashboard():
    """Display the main budget dashboard with totals and category breakdowns.

    Shows the current month's budget, total spent, percent used, and a per-category bar chart. Warns if viewing a non-current month.

    Returns:
        None
    """
    print_info("\n=== Budget Dashboard ===")
    budgets = get_all_budgets()
    expenses = get_all_expenses()
    month = SESSION['month']
    year = SESSION['year']
    total_budget = sum(row[1] for row in budgets if row[2] == month and str(row[3]) == str(year))
    # Only sum expenses for categories in the current month/year
    budget_cats = {row[0] for row in budgets if row[2] == month and str(row[3]) == str(year)}
    total_spent = sum(row[0] for row in expenses if row[1] in budget_cats)
    percent_used = (total_spent / total_budget * 100) if total_budget else 0
    color = Fore.GREEN if percent_used < 80 else (Fore.YELLOW if percent_used < 100 else Fore.RED)
    print(f"{Fore.CYAN}Month: {month} {year}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total Budget: {Fore.GREEN}${total_budget}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total Spent: {Fore.MAGENTA}${total_spent}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Budget Used: {color}{percent_used:.1f}%{Style.RESET_ALL}")
    if (month != datetime.datetime.now().strftime('%B') or str(year) != str(datetime.datetime.now().year)):
        print_warning(f"Note: You are viewing {month} {year}, not the current month.")
    print_info("\nSpending by Category:")
    # Calculate spending by category for the bar charts
    cat_limits = {row[0]: row[1] for row in budgets if row[2] == month and str(row[3]) == str(year)}
    cat_spent = {cat: 0 for cat in cat_limits}
    for amt, cat, *_ in expenses:
        if cat in cat_spent:
            cat_spent[cat] += amt
    color_map = get_category_color_map(list(cat_limits.keys()))
    per_category_bar_chart(cat_spent, cat_limits, color_map=color_map)
    print_info("\nType 'help' at any menu for guidance.")

# --- Undo Feature ---
def undo_last_action():
    """Undo the last budget or expense deletion, if possible.

    Restores the most recently deleted budget or expense using the undo stack. If nothing can be undone, prints a warning.

    Returns:
        None
    """
    if not UNDO_STACK:
        print_warning("Nothing to undo.")
        return
    action, args = UNDO_STACK.pop()
    if action == 'delete_budget':
        add_to_budget(*args)
        print_success("Undo: Restored deleted budget category.")
    elif action == 'delete_expense':
        add_expense(*args)
        print_success("Undo: Restored deleted expense.")
    else:
        print_warning("Nothing to undo.")

# --- Motivational Quote ---
def print_motivational():
    """Print a random motivational quote.

    Selects and prints a random motivational quote from the predefined list.

    Returns:
        None
    """
    print_info(random.choice(MOTIVATIONAL_QUOTES))

# --- Demo Data ---
DEMO_BUDGETS = [
    ("Housing", 1200, "April", 2024),
    ("Food", 400, "April", 2024),
    ("Transport", 200, "April", 2024),
    ("Entertainment", 150, "April", 2024),
    ("Savings", 500, "April", 2024),
]
DEMO_EXPENSES = [
    (1100, "Housing", "Rent", "2024-04-01", "USD", 1100),
    (120, "Food", "Groceries", "2024-04-03", "USD", 120),
    (60, "Food", "Dining Out", "2024-04-10", "USD", 60),
    (80, "Transport", "Gas", "2024-04-05", "USD", 80),
    (50, "Entertainment", "Movies", "2024-04-07", "USD", 50),
    (400, "Savings", "Transfer to savings", "2024-04-02", "USD", 400),
]

# --- Demo Mode ---
def run_demo_mode():
    """Run the tool in demo mode with dummy data, allowing safe exploration.

    Backs up the real database, loads demo data, and allows the user to interact with the tool in a sandboxed environment. Restores real data on exit.

    Returns:
        None
    """
    print_warning("\n=== DEMO MODE: This is a dummy population. No real data will be affected. ===")
    # Backup real DB if exists
    from db.database import DB_PATH
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
        cursor.execute("INSERT INTO expenses (amount, category, description, date, currency, converted_amount_usd) VALUES (?, ?, ?, ?, ?, ?)", e)
    connection.commit()
    connection.close()
    # Set session to demo month/year
    SESSION['month'] = 'April'
    SESSION['year'] = 2024
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
            undo_last_action()
            show_dashboard()
        elif choice == '4':
            print_info("Restoring your real data...")
            if os.path.exists(backup_path):
                shutil.move(backup_path, DB_PATH)
            print_success("Exited demo mode. Your real data is restored.")
            break
        else:
            print_error("Invalid choice.")

# --- Main Menu (add Demo Mode option) ---
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
            undo_last_action()
        elif choice == '2':
            run_demo_mode()
        elif choice == '3' or choice == 'back':
            return
        else:
            print_error("Invalid choice.")

def main():
    """Main entry point for the CLI Budgeting Tool. Handles the main menu and navigation.

    Displays the main menu, processes user choices, and routes to the appropriate submenus or exits the program.

    Returns:
        None
    """
    print_info("Welcome to the CLI Budgeting Tool!")
    while True:
        show_dashboard()
        print_info("\nWhat do you want to do today?")
        print("1. Set up automatic budget")
        print("2. Manage Budget & Expenses")
        print("3. Get Advice (chat)")
        print("4. Other Options")
        print("5. Exit")
        print("Type 'help' for info or 'exit' to quit at any prompt.")
        choice = input_with_help("Choose an option:", help_text="1: Set up a new budget, 2: Add/view/edit budget or expenses, 3: Chat with Gemini, 4: Undo/Demo, 5: Exit.", allow_back=False)
        if choice == 'exit' or choice == '5':
            print_success("Goodbye! Thanks for using the CLI Budgeting Tool.")
            sys.exit(0)
        if choice == 'help':
            print_info("This tool helps you manage your budget, track expenses, and get financial advice—all from the command line!")
            continue
        if choice == '1':
            setup_automatic_budget()
            print_motivational()
        elif choice == '2':
            # Submenu for budget and expenses
            while True:
                print_info("\nManage Budget & Expenses:")
                print("1. Budget")
                print("2. Expenses")
                print("3. Back to Main Menu")
                sub_choice = input_with_help("Choose an option:")
                if sub_choice == '1':
                    budget_menu()
                    print_motivational()
                elif sub_choice == '2':
                    expenses_menu()
                    print_motivational()
                elif sub_choice == '3' or sub_choice == 'back':
                    break
                else:
                    print_error("Invalid choice.")
        elif choice == '3':
            advice_menu()
        elif choice == '4':
            other_options_menu()
        else:
            print_error("Invalid choice.")

# --- Budget Menu (with undo and progress bar) ---
def budget_menu():
    """Display the Budget menu for adding, deleting, and viewing budget categories.

    Allows the user to add, delete, or view budget categories and limits for the current month and year.

    Returns:
        None
    """
    while True:
        print_info("\nBudget Menu:")
        print("1. Add category")
        print("2. Delete category")
        print("3. Show budget")
        print("4. Back to Main Menu")
        print("Type 'help' for info or 'back' to return to main menu at any prompt.")
        choice = input_with_help("Choose an option:")
        if choice == 'back':
            return
        if choice == 'help':
            print_info("Add, delete, or view your budget categories and limits for the current month/year.")
            continue
        if choice == '1':
            category = input_with_help("Category:")
            if category == 'back': continue
            limit_amount = input_with_help("Limit Amount:")
            if limit_amount == 'back': continue
            month = input_with_help(f"Month (default: {SESSION['month']}):") or SESSION['month']
            if month == 'back': continue
            year = input_with_help(f"Year (default: {SESSION['year']}):") or SESSION['year']
            if year == 'back': continue
            try:
                progress_bar("Saving budget")
                add_to_budget(category, float(limit_amount), month, int(year))
                print_success(f"Added budget for {category}.")
            except Exception as e:
                print_error(f"Error: {e}")
        elif choice == '2':
            category = input_with_help("Category to delete:")
            if category == 'back': continue
            month = input_with_help(f"Month (default: {SESSION['month']}):") or SESSION['month']
            if month == 'back': continue
            year = input_with_help(f"Year (default: {SESSION['year']}):") or SESSION['year']
            if year == 'back': continue
            if ask_confirm(f"Are you sure you want to delete the budget for {category} in {month} {year}?"):
                try:
                    # Save for undo
                    budgets = get_all_budgets()
                    for row in budgets:
                        if row[0] == category and row[2] == month and str(row[3]) == str(year):
                            UNDO_STACK.append(('delete_budget', (row[0], row[1], row[2], row[3])))
                    progress_bar("Deleting budget")
                    delete_from_budget(category, month, int(year))
                    print_success(f"Deleted budget for {category}.")
                except Exception as e:
                    print_error(f"Error: {e}")
            else:
                print_info("Deletion cancelled.")
        elif choice == '3':
            print_info("[Budget Table]")
            data = get_all_budgets()
            if not data:
                print_warning("No budget categories found.")
            else:
                # Colorize over-budget categories
                expenses = get_all_expenses()
                cat_spent = {cat: 0 for cat, *_ in data}
                for amt, cat, *_ in expenses:
                    if cat in cat_spent:
                        cat_spent[cat] += amt
                table = []
                for row in data:
                    cat, limit, month, year = row
                    spent = cat_spent.get(cat, 0)
                    over = spent > limit
                    color = Fore.RED if over else Fore.GREEN
                    table.append([
                        f"{color}{cat}{Style.RESET_ALL}",
                        f"{color}${limit}{Style.RESET_ALL}",
                        f"{color}${spent}{Style.RESET_ALL}",
                        f"{color}{month}{Style.RESET_ALL}",
                        f"{color}{year}{Style.RESET_ALL}",
                        f"{color}{'OVER' if over else ''}{Style.RESET_ALL}"
                    ])
                print(tabulate(table, headers=[f"{Fore.CYAN}Category{Style.RESET_ALL}", f"{Fore.CYAN}Limit{Style.RESET_ALL}", f"{Fore.CYAN}Spent{Style.RESET_ALL}", f"{Fore.CYAN}Month{Style.RESET_ALL}", f"{Fore.CYAN}Year{Style.RESET_ALL}", f"{Fore.CYAN}Status{Style.RESET_ALL}"], tablefmt="fancy_grid"))
        elif choice == '4':
            return
        else:
            print_error("Invalid choice.")

def get_gemini_category_suggestion(description, categories):
    """Use Gemini to suggest the best category for an expense description.

    Sends a prompt to the Gemini API to suggest the most appropriate category for a given expense description from a list of categories.

    Args:
        description (str): The expense description.
        categories (list[str]): List of available categories.

    Returns:
        str or None: Suggested category name, or None if the API call fails or input is invalid.
    """
    if not GEMINI_API_KEY or not description or not categories:
        return None
    prompt = (
        f"Given the following expense description: '{description}'. "
        f"Choose the single most appropriate category from this list: {', '.join(categories)}. "
        "Return only the category name."
    )
    conversation = [
        {"role": "user", "parts": [{"text": prompt}]}
    ]
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            json={"contents": conversation},
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', None)
            if answer:
                return answer.strip().split('\n')[0]
    except Exception:
        pass
    return None

# --- Expenses Menu (with undo and progress bar) ---
def expenses_menu():
    """Display the Expenses menu for adding, deleting, and viewing expenses.

    Allows the user to add, delete, or view expenses. Provides category suggestions using Gemini if available.

    Returns:
        None
    """
    while True:
        print_info("\nExpenses Menu:")
        print("1. Add expense")
        print("2. Delete expense")
        print("3. Show expenses")
        print("4. Back to Main Menu")
        print("Type 'help' for info or 'back' to return to main menu at any prompt.")
        choice = input_with_help("Choose an option:")
        if choice == 'back':
            return
        if choice == 'help':
            print_info("Add, delete, or view your expenses. When adding, you can auto-suggest categories from your budget.")
            continue
        if choice == '1':
            budget_cats = [row[0] for row in get_all_budgets()]
            if budget_cats:
                print_info("Available categories:")
                for cat in budget_cats:
                    print(f"- {cat}")
            # Ask for description first
            description = input_with_help("Description (company or what you spent on):")
            if description == 'back': continue
            # Gemini category suggestion
            suggested_cat = get_gemini_category_suggestion(description, budget_cats) if budget_cats else None
            if suggested_cat:
                cat_prompt = f"Category (Hit enter for {suggested_cat}):"
            else:
                cat_prompt = "Category:"
            category = input_with_help(cat_prompt)
            if category == 'back': continue
            if not category and suggested_cat:
                category = suggested_cat
            amount = input_with_help("Amount:")
            if amount == 'back': continue
            # Date: default to today if blank
            import datetime
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            date = input_with_help(f"Date (Hit Enter for {today_str}):", help_text="Example: 2024-04-01")
            if date == 'back': continue
            if not date:
                date = today_str
            currency = input_with_help("Currency:")
            if currency == 'back': continue
            converted_amount_usd = input_with_help("Converted Amount (USD):")
            if converted_amount_usd == 'back': continue
            try:
                progress_bar("Saving expense")
                add_expense(float(amount), category, description, date, currency, float(converted_amount_usd))
                print_success(f"Added expense: {amount} {currency} for {description}.")
                fake_carbon_api(description)
            except Exception as e:
                print_error(f"Error: {e}")
        elif choice == '2':
            description = input_with_help("Description (company) to delete:")
            if description == 'back': continue
            date = input_with_help("Date (YYYY-MM-DD) of expense to delete:")
            if date == 'back': continue
            if ask_confirm(f"Are you sure you want to delete the expense for {description} on {date}?"):
                try:
                    # Save for undo
                    expenses = get_all_expenses()
                    for row in expenses:
                        if row[2] == description and row[3] == date:
                            UNDO_STACK.append(('delete_expense', row))
                    progress_bar("Deleting expense")
                    delete_expense(description, date)
                    print_success(f"Deleted expense for {description} on {date}.")
                except Exception as e:
                    print_error(f"Error: {e}")
            else:
                print_info("Deletion cancelled.")
        elif choice == '3':
            print_info("[Expenses Table]")
            data = get_all_expenses()
            if not data:
                print_warning("No expenses found.")
            else:
                table = []
                for row in data:
                    amt, cat, desc, date, curr, usd = row
                    color = Fore.RED if amt > 1000 else Fore.GREEN
                    table.append([
                        f"{color}${amt}{Style.RESET_ALL}",
                        f"{color}{cat}{Style.RESET_ALL}",
                        f"{color}{desc}{Style.RESET_ALL}",
                        f"{color}{date}{Style.RESET_ALL}",
                        f"{color}{curr}{Style.RESET_ALL}",
                        f"{color}${usd}{Style.RESET_ALL}"
                    ])
                print(tabulate(table, headers=[f"{Fore.CYAN}Amount{Style.RESET_ALL}", f"{Fore.CYAN}Category{Style.RESET_ALL}", f"{Fore.CYAN}Description{Style.RESET_ALL}", f"{Fore.CYAN}Date{Style.RESET_ALL}", f"{Fore.CYAN}Currency{Style.RESET_ALL}", f"{Fore.CYAN}USD{Style.RESET_ALL}"], tablefmt="fancy_grid"))
        elif choice == '4':
            return
        else:
            print_error("Invalid choice.")

# --- Advice Menu ---
def summarize_current_budget():
    """Summarize the current budget and spending for the advice system prompt.

    Compiles a summary of the current month's budget and expenses for use in the Gemini advice prompt.

    Returns:
        str: Multi-line summary of the current budget and spending.
    """
    month = SESSION['month']
    year = SESSION['year']
    budgets = get_all_budgets()
    expenses = get_all_expenses()
    cat_limits = {row[0]: row[1] for row in budgets if row[2] == month and str(row[3]) == str(year)}
    cat_spent = {cat: 0 for cat in cat_limits}
    for amt, cat, *_ in expenses:
        if cat in cat_spent:
            cat_spent[cat] += amt
    summary_lines = [f"Current budget for {month} {year}:"]
    total_budget = sum(cat_limits.values())
    total_spent = sum(cat_spent.values())
    summary_lines.append(f"Total budget: ${total_budget:.2f}, Total spent: ${total_spent:.2f}")
    for cat in cat_limits:
        summary_lines.append(f"- {cat}: limit ${cat_limits[cat]:.2f}, spent ${cat_spent[cat]:.2f}")
    return "\n".join(summary_lines)

def real_gemini_api_conversation(conversation):
    """Send a conversation to the Gemini API and return the model's response.

    Sends the conversation history to the Gemini API and returns the model's response text. Handles API errors and missing API key.

    Args:
        conversation (list[dict]): List of conversation turns for the Gemini API.

    Returns:
        str or None: The model's response, or None if the API call fails.
    """
    if not GEMINI_API_KEY:
        print_warning("Gemini API key not found. Please set GEMINI_API_KEY in your .env file.")
        return None
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            headers=headers,
            json={"contents": conversation},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', None)
            return answer
        print_warning("Could not get a valid response from Gemini API.")
    except Exception as e:
        print_error(f"Error connecting to Gemini API: {e}")
    return None

def advice_menu():
    """Interactive conversational menu for getting budgeting advice from Gemini.

    Provides a conversational interface for the user to ask budgeting questions and receive advice from Gemini, using the current budget as context.

    Returns:
        None
    """
    print_info("\nConversational Budgeting Advice (type /exit to leave at any time)")
    budget_context = summarize_current_budget()
    system_prompt = (
        f"{budget_context}\n\n"
        "You are a helpful, concise, and practical financial budgeting assistant. "
        "Give actionable, friendly, and specific advice for personal budgeting and money management. "
        "If the user asks a general question, provide a budgeting tip. "
        "If the user asks about their own budget, give tailored suggestions. "
        "Always be encouraging and clear. "
        "Format your response as a short, clear paragraph followed by 2-3 concise, actionable bullet points. "
        "Use plain text, not markdown."
    )
    conversation = []
    first_turn = True
    while True:
        user_input = input_with_help("You: ")
        if user_input.strip().lower() == '/exit':
            print_info("Exiting advice section.")
            break
        # Prepend system prompt and budget context to the first user message
        if first_turn:
            user_message = f"{system_prompt}\n\n{user_input}"
            first_turn = False
        else:
            user_message = user_input
        conversation.append({"role": "user", "parts": [{"text": user_message}]})
        answer = real_gemini_api_conversation(conversation)
        if answer:
            print_info("\nGemini's Budgeting Advice:")
            print(f"{answer.strip()}\n")
            conversation.append({"role": "model", "parts": [{"text": answer.strip()}]})
        else:
            print_warning("No advice received from Gemini.")

MOTIVATIONAL_QUOTES = [
    "Every dollar you save is a step closer to your goals!",
    "Small savings add up to big results.",
    "Budgeting is the first step to financial freedom!",
    "You're doing great—keep it up!",
    "A budget is telling your money where to go instead of wondering where it went."
]

UNDO_STACK = []

if __name__ == "__main__":
    main()