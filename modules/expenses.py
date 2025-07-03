"""
expenses.py
-----------
Handles expenses menu logic and category suggestion for the Budgeting Tool.
"""
from modules.ux import print_info, print_warning, print_success, input_with_help, progress_bar, ask_confirm
from db.db_operations import get_all_expenses, add_expense, delete_expense, get_all_budgets
import datetime
from tabulate import tabulate
from colorama import Fore, Style
from modules.state import SESSION, UNDO_STACK
from modules.gemini_api import real_gemini_api_conversation
from modules.budget import ReturnToMainMenu

def get_gemini_category_suggestion(description, categories):
    """Use Gemini to suggest the best category for an expense description.

    Sends a prompt to the Gemini API to suggest the most appropriate category for a given expense description from a list of categories.

    Args:
        description (str): The expense description.
        categories (list[str]): List of available categories.

    Returns:
        str or None: Suggested category name, or None if the API call fails or input is invalid.
    """
    if not categories or not description:
        return None
    prompt = (
        f"Given the following expense description: '{description}', and these categories: {', '.join(categories)}, "
        "which category is the best fit? Respond with only the category name."
    )
    conversation = [{"role": "user", "parts": [{"text": prompt}]}]
    answer = real_gemini_api_conversation(conversation)
    if answer:
        answer = answer.strip()
        # Only return if it's a valid category
        for cat in categories:
            if answer.lower() == cat.lower():
                return cat
    return None


def expenses_menu(demo_mode=False):
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
        if demo_mode:
            print("4. Back to Demo Menu")
        else:
            print("4. Back to Main Menu")
        print("Type 'help' for info or 'back' to return to menu at any prompt.")
        choice = input_with_help("Choose an option:")
        if choice == 'back' or choice == '4':
            if demo_mode:
                break
            else:
                raise ReturnToMainMenu()
        if choice == 'help':
            print_info("Add, delete, or view your expenses. When adding, you can auto-suggest categories from your budget.")
            continue
        if choice == '1':
            budget_cats = [row[0] for row in get_all_budgets()]
            if budget_cats:
                print_info("Available categories:")
                for idx, cat in enumerate(budget_cats, 1):
                    print(f"{idx}. {cat}")
            description = input_with_help("Description (company or what you spent on):", help_text="Write a short description of the expense.")
            if description == 'back':
                if demo_mode:
                    break
                else:
                    continue
            suggested_cat = get_gemini_category_suggestion(description, budget_cats)
            if suggested_cat:
                cat_prompt = f"Category (Hit Enter for {suggested_cat}, or choose number):"
            else:
                cat_prompt = "Category (choose number or type name):"
            category_input = input_with_help(cat_prompt)
            if category_input == 'back':
                if demo_mode:
                    break
                else:
                    continue
            if category_input.isdigit() and 1 <= int(category_input) <= len(budget_cats):
                category = budget_cats[int(category_input)-1]
            elif not category_input and suggested_cat:
                category = suggested_cat
            else:
                category = category_input
            amount = input_with_help("Amount:")
            if amount == 'back':
                if demo_mode:
                    break
                else:
                    continue
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            date = input_with_help(f"Date (Hit Enter for {today_str}):", help_text="Example: 2024-04-01")
            if date == 'back':
                if demo_mode:
                    break
                else:
                    continue
            if not date:
                date = today_str
            currency = input_with_help("Currency:")
            if currency == 'back':
                if demo_mode:
                    break
                else:
                    continue
            try:
                progress_bar("Saving expense")
                add_expense(float(amount), category, description, date, currency)
                UNDO_STACK.append(('add_expense', (description, date)))
                print_success(f"Added expense: {amount} {currency} for {description}.")
            except Exception as e:
                print_error(f"Error: {e}")
        elif choice == '2':
            expenses = get_all_expenses()
            month = SESSION['month']
            year = SESSION['year']
            filtered_expenses = [row for row in expenses if row[3][:7] == f"{year}-{str(datetime.datetime.strptime(month, '%B').month).zfill(2)}"]
            if not filtered_expenses:
                print_warning(f"No expenses found for {month} {year}.")
                continue
            print_info(f"Expenses for {month} {year}:")
            for idx, row in enumerate(filtered_expenses, 1):
                amt, cat, desc, date, curr = row
                print(f"{idx}. {desc} | {cat} | {amt} {curr} | {date}")
            idx_input = input_with_help("Enter the number of the expense to delete:")
            if idx_input == 'back':
                if demo_mode:
                    break
                else:
                    continue
            try:
                idx = int(idx_input)
                if not (1 <= idx <= len(filtered_expenses)):
                    print_error("Invalid selection. No such expense.")
                    continue
            except ValueError:
                print_error("Please enter a valid number.")
                continue
            expense = filtered_expenses[idx-1]
            desc, date = expense[2], expense[3]
            if ask_confirm(f"Are you sure you want to delete the expense '{desc}' on {date}?"):
                try:
                    UNDO_STACK.append(('delete_expense', expense))
                    progress_bar("Deleting expense")
                    delete_expense(desc, date)
                    print_success(f"Deleted expense for {desc} on {date}.")
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
                month = SESSION['month']
                year = SESSION['year']
                budgets = get_all_budgets()
                cat_limits = {row[0]: row[1] for row in budgets if row[2] == month and str(row[3]) == str(year)}
                cat_spent = {cat: 0 for cat in cat_limits}
                for amt, cat, *_ in data:
                    if cat in cat_spent:
                        cat_spent[cat] += amt
                table = []
                for row in data:
                    amt, cat, desc, date, curr = row
                    spent_so_far = cat_spent.get(cat, 0) - amt if cat in cat_spent else 0
                    over = (spent_so_far + amt) > cat_limits.get(cat, float('inf'))
                    color = Fore.RED if over else Fore.GREEN
                    table.append([
                        f"{color}${amt}{Style.RESET_ALL}",
                        f"{color}{cat}{Style.RESET_ALL}",
                        f"{color}{desc}{Style.RESET_ALL}",
                        f"{color}{date}{Style.RESET_ALL}",
                        f"{color}{curr}{Style.RESET_ALL}"
                    ])
                print(tabulate(table, headers=[f"{Fore.CYAN}Amount{Style.RESET_ALL}", f"{Fore.CYAN}Category{Style.RESET_ALL}", f"{Fore.CYAN}Description{Style.RESET_ALL}", f"{Fore.CYAN}Date{Style.RESET_ALL}", f"{Fore.CYAN}Currency{Style.RESET_ALL}"], tablefmt="fancy_grid"))
        else:
            print_warning("Invalid choice.") 