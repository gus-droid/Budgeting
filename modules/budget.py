"""
budget.py
---------
Handles budget menu logic and automatic budget setup for the Budgeting Tool.
"""
from modules.ux import print_info, print_warning, print_success, input_with_help, progress_bar, ask_confirm
from db.db_operations import get_all_budgets, add_to_budget, delete_from_budget, get_all_expenses, get_income, set_income
import datetime
from tabulate import tabulate
from colorama import Fore, Style
from modules.state import SESSION, UNDO_STACK

# Add a global/session income tracker
if 'income' not in SESSION:
    SESSION['income'] = None

def setup_automatic_budget():
    """Interactive wizard to set up an automatic budget based on user input and Gemini suggestions.

    Guides the user through entering income, rent, and fixed bills, then uses Gemini or a default rule to suggest a budget split. Allows customization and saves the result to the database.

    Returns:
        None
    """
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
                print_warning("Income must be positive.")
                continue
            break
        except ValueError:
            print_warning("Please enter a valid number.")

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
                print_warning("Rent cannot be negative.")
                continue
            break
        except ValueError:
            print_warning("Please enter a valid number.")

    # Ask for fixed bills/expenses
    fixed_bills = []
    print_info("\nList any fixed bills or recurring expenses you have each month (e.g., utilities, insurance, subscriptions). Type 'done' when finished.")
    while True:
        bill_name = input_with_help("Bill/Expense name (or 'done' to finish):")
        if bill_name.strip().lower() == 'done':
            break
        if not bill_name:
            print_warning("Name cannot be empty.")
            continue
        bill_amt = input_with_help(f"Monthly amount for {bill_name}: $")
        if bill_amt == 'back':
            return
        try:
            bill_amt = float(bill_amt)
            if bill_amt < 0:
                print_warning("Amount cannot be negative.")
                continue
            fixed_bills.append((bill_name, bill_amt))
        except ValueError:
            print_warning("Please enter a valid number.")

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
    from modules.gemini_api import get_gemini_budget_split, format_split_preview
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
            total = sum(cat['percent'] for cat in categories)
            percent_left = 100 - total
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat['name']} ({cat['percent']}%)")
            print(f"{len(categories)+1}. Add new category")
            print(f"{len(categories)+2}. Done customizing")
            print_info(f"{percent_left:.2f}% of Income left to allocate.")
            if percent_left < 0:
                print_warning(f"You have over-allocated your income by {-percent_left:.2f}%. Please adjust your categories.")
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
                                # Check for over-allocation
                                total = sum(cat['percent'] for cat in categories)
                                percent_left = 100 - total
                                if percent_left < 0:
                                    print_warning(f"You have over-allocated your income by {-percent_left:.2f}%. Please adjust your categories.")
                                    cat['percent'] -= val  # revert
                                    continue
                            else:
                                print_warning("Percentage must be between 0 and 100.")
                        except ValueError:
                            print_warning("Invalid number.")
                elif idx == len(categories)+1:
                    # Add new
                    if percent_left == 0:
                        print_info("You have already allocated 100% of your income. Cannot add another category.")
                        continue
                    new_name = input_with_help("New category name:")
                    if new_name == 'back':
                        return
                    if not new_name:
                        print_warning("Name cannot be empty.")
                        continue
                    new_percent = input_with_help(f"Percentage for '{new_name}':")
                    if new_percent == 'back':
                        return
                    try:
                        val = float(new_percent)
                        if 0 < val <= 100:
                            categories.append({"name": new_name, "percent": val, "examples": []})
                            total = sum(cat['percent'] for cat in categories)
                            percent_left = 100 - total
                            if percent_left < 0:
                                print_warning(f"You have over-allocated your income by {-percent_left:.2f}%. Please adjust your categories.")
                                categories.pop()  # revert
                                continue
                        else:
                            print_warning("Percentage must be between 0 and 100.")
                    except ValueError:
                        print_warning("Invalid number.")
                elif idx == len(categories)+2:
                    # Done
                    total = sum(cat['percent'] for cat in categories)
                    percent_left = 100 - total
                    if abs(percent_left) > 0.01:
                        print_warning(f"You must allocate exactly 100% of your income. {percent_left:.2f}% left to allocate.")
                        continue
                    break
            else:
                print_warning("Invalid choice.")
        # After editing, check total
        total = sum(cat['percent'] for cat in categories)
        if abs(total - 100) > 0.01:
            print_warning(f"You must allocate exactly 100% of your income. {100-total:.2f}% left to allocate.")
            return

    # Save to database
    now = datetime.datetime.now()
    month = now.strftime("%B")
    year = now.year
    # Save income to database for this month/year
    set_income(month, year, income)
    print_info("\nSaving your budget...")
    # Wipe previous budget for this month/year
    budgets = get_all_budgets()
    for row in budgets:
        if row[2] == month and str(row[3]) == str(year):
            delete_from_budget(row[0], month, year)
    for cat in categories:
        limit = round(income * cat['percent'] / 100, 2)
        add_to_budget(cat['name'], limit, month, year)
    print_success("Budget saved!")
    # Show final table
    print_info("\nYour automatic budget:")
    table = [[cat['name'], f"{cat['percent']}%", f"${round(income * cat['percent'] / 100, 2)}"] for cat in categories]
    print(tabulate(table, headers=["Category", "%", "Amount"], tablefmt="fancy_grid"))
    print_info("\nYou can always edit your budget categories later from the Budget menu.")


def budget_menu():
    """Display the Budget menu for adding, deleting, and viewing budget categories.

    Allows the user to add, delete, or view budget categories and limits for the current month and year.

    Returns:
        None
    """
    month = SESSION['month']
    year = SESSION['year']
    income = get_income(month, year)
    if income is None:
        while True:
            income_input = input_with_help(f"Enter your monthly after-tax income for {month} {year} (required for budget % checks): $")
            if income_input == 'back':
                return
            try:
                income = float(income_input)
                if income <= 0:
                    print_warning("Income must be positive.")
                    continue
                set_income(month, year, income)
                break
            except ValueError:
                print_warning("Please enter a valid number.")
    while True:
        print_info("\nBudget Menu:")
        print("1. Add category")
        print("2. Delete category")
        print("3. Show budget")
        print("4. Back to Main Menu")
        print("Type 'help' for info or 'back' to return to main menu at any prompt.")
        # Show percent left to allocate
        budgets = get_all_budgets()
        total_limit = sum(row[1] for row in budgets if row[2] == month and str(row[3]) == str(year))
        percent_used = (total_limit / income) * 100 if income else 0
        percent_left = 100 - percent_used
        print_info(f"{percent_left:.2f}% of Income left to allocate.")
        choice = input_with_help("Choose an option:")
        if choice == 'back' or choice == '4':
            return
        if choice == 'help':
            print_info("Add, delete, or view your budget categories and limits for the current month/year.")
            continue
        if choice == '1':
            # Show current categories before adding
            current_cats = [row[0] for row in budgets if row[2] == month and str(row[3]) == str(year)]
            if current_cats:
                print_info("Current categories:")
                for cat in current_cats:
                    print(f"- {cat}")
            else:
                print_info("No categories yet for this month/year.")
            category = input_with_help("Category:")
            if category == 'back': continue
            limit_amount = input_with_help("Limit Amount:")
            if limit_amount == 'back': continue
            try:
                limit_amount = float(limit_amount)
            except ValueError:
                print_warning("Please enter a valid number.")
                continue
            # Check if adding this would exceed 100%
            new_total = total_limit + limit_amount
            new_percent = (new_total / income) * 100 if income else 0
            percent_left = 100 - (total_limit / income) * 100 if income else 0
            if new_percent > 100.01:
                print_warning(f"Cannot add this category. Only {percent_left:.2f}% of income left to allocate.")
                continue
            if percent_left < 0:
                print_warning(f"You have over-allocated your income by {-percent_left:.2f}%. Please adjust your categories.")
                continue
            month = input_with_help(f"Month (default: {month}):") or month
            if month == 'back': continue
            year = input_with_help(f"Year (default: {year}):") or year
            if year == 'back': continue
            try:
                progress_bar("Saving budget")
                add_to_budget(category, float(limit_amount), month, int(year))
                UNDO_STACK.append(('add_budget', (category, month, int(year))))
                print_success(f"Added budget for {category}.")
            except Exception as e:
                print_warning(f"Error: {e}")
        elif choice == '2':
            # Show current categories before deleting
            current_cats = [row[0] for row in budgets if row[2] == month and str(row[3]) == str(year)]
            if current_cats:
                print_info("Current categories:")
                for cat in current_cats:
                    print(f"- {cat}")
            else:
                print_info("No categories yet for this month/year.")
            category = input_with_help("Category to delete:")
            if category == 'back': continue
            if category not in current_cats:
                print_warning(f"Category '{category}' not found for {month} {year}.")
                continue
            month = input_with_help(f"Month (default: {month}):") or month
            if month == 'back': continue
            year = input_with_help(f"Year (default: {year}):") or year
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
                    # Show new percent left
                    budgets = get_all_budgets()
                    total_limit = sum(row[1] for row in budgets if row[2] == month and str(row[3]) == str(year))
                    percent_used = (total_limit / income) * 100 if income else 0
                    percent_left = 100 - percent_used
                    print_info(f"{percent_left:.2f}% of Income left to allocate.")
                except Exception as e:
                    print_warning(f"Error: {e}")
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
        else:
            print_warning("Invalid choice.")

    pass  # Placeholder for full function body 