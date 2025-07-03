"""
cli.py
------
Main CLI entry point for the Budgeting Tool. Handles user interaction, menu navigation, and high-level workflow.
"""
from modules.ux import print_info
from modules.dashboard import show_dashboard
from modules.budget import budget_menu, setup_automatic_budget, ReturnToMainMenu
from modules.expenses import expenses_menu
from modules.demo import other_options_menu
from modules.gemini_api import advice_menu
from modules.investments import investments_menu


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
        print("3. Investments")
        print("4. Get Advice (chat)")
        print("5. Other Options")
        print("6. Exit")
        print("Type 'help' for info or 'exit' to quit at any prompt.")
        choice = input("Choose an option: ").strip()
        if choice == 'exit' or choice == '6':
            print_info("Goodbye! Thanks for using the CLI Budgeting Tool.")
            break
        if choice == 'help':
            print_info("This tool helps you manage your budget, track expenses, and get financial advice—all from the command line!")
            continue
        try:
            if choice == '1':
                setup_automatic_budget()
            elif choice == '2':
                # Submenu for budget and expenses
                while True:
                    print_info("\nManage Budget & Expenses:")
                    print("1. Budget")
                    print("2. Expenses")
                    print("3. Back to Main Menu")
                    sub_choice = input("Choose an option: ").strip()
                    try:
                        if sub_choice == '1':
                            budget_menu()
                        elif sub_choice == '2':
                            expenses_menu()
                        elif sub_choice == '3' or sub_choice == 'back':
                            break
                        else:
                            print_info("Invalid choice.")
                    except ReturnToMainMenu:
                        break
            elif choice == '3':
                try:
                    investments_menu()
                except ReturnToMainMenu:
                    continue
            elif choice == '4':
                advice_menu()
            elif choice == '5':
                other_options_menu()
            else:
                print_info("Invalid choice.")
        except ReturnToMainMenu:
            continue

if __name__ == "__main__":
    main() 