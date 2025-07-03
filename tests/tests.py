# File for unit tests of functions
import pytest
from unittest.mock import patch
from modules.budget import setup_automatic_budget, budget_menu

@pytest.fixture
def mock_dependencies():
    with patch('budget.print_info'), \
         patch('budget.print_warning'), \
         patch('budget.print_success'), \
         patch('budget.progress_bar'), \
         patch('budget.ask_confirm', return_value=True), \
         patch('budget.get_all_budgets', return_value=[]), \
         patch('budget.delete_from_budget'), \
         patch('budget.add_to_budget'), \
         patch('budget.set_income'), \
         patch('budget.get_income', return_value=None), \
         patch('budget.get_all_expenses', return_value=[]), \
         patch('budget.input_with_help') as mock_input, \
         patch('budget.get_gemini_budget_split', return_value=None), \
         patch('budget.format_split_preview', return_value="formatted"):
        yield mock_input

def test_valid_flow_with_default_split(mock_dependencies):
    # Simulate inputs: income, rent, fixed bills, goal choices, customization = 'n'
    mock_dependencies.side_effect = [
        '4000',       # income
        '1000',       # rent
        'done',       # no fixed bills
        '1,3',        # goals
        'n',          # use Gemini split? (mocked to return None anyway)
        'n'
    ]
    setup_automatic_budget()

def test_invalid_income_retry(mock_dependencies):
    mock_dependencies.side_effect = [
        '-100',       # invalid income
        'abc',        # invalid again
        '5000',       # valid
        '1000',       # rent
        'done',       # no bills
        '1',          # goal
        'n',          # use gemini
        'n'           # customize
    ]
    setup_automatic_budget()

def test_budget_menu_add_and_view(mock_dependencies):
    mock_dependencies.side_effect = [
        '5000',      # initial income set
        '1',         # Add category
        'Groceries', # category name
        '1000',      # limit
        '', '',      # use default month/year
        '3',         # Show budget
        '4'          # Exit
    ]
    budget_menu()

def test_budget_menu_delete(mock_dependencies):
    # Mock get_all_budgets to include one category
    with patch('budget.get_all_budgets', return_value=[
        ('Groceries', 1000, 'July', 2025)
    ]):
        mock_dependencies.side_effect = [
            '5000',       # income
            '2',          # delete category
            'Groceries',  # category to delete
            '', '',       # default month/year
            '4'           # exit
        ]
        budget_menu()
