# File for unit tests of functions
import pytest
from unittest.mock import patch
from modules.budget import setup_automatic_budget, budget_menu

<<<<<<< HEAD
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
=======
import unittest
import tempfile
import os
import sqlite3
from unittest import mock

# --- investments.py ---
from modules import investments

class TestInvestments(unittest.TestCase):
    def setUp(self):
        # Use a temp DB file
        self.db_fd, self.db_path = tempfile.mkstemp()
        investments.DB_PATH = self.db_path
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                shares REAL NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date TEXT
            )''')

    def tearDown(self):
        os.close(self.db_fd)
        os.remove(self.db_path)

    def test_add_and_get_investment(self):
        investments.add_investment('AAPL', 10, 150.0, '2024-01-01')
        rows = investments.get_all_investments()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], 'AAPL')

    def test_add_multiple_investments(self):
        investments.add_investment('AAPL', 10, 150.0, '2024-01-01')
        investments.add_investment('MSFT', 5, 200.0, '2024-02-01')
        rows = investments.get_all_investments()
        self.assertEqual(len(rows), 2)
        self.assertSetEqual(set(r[1] for r in rows), {'AAPL', 'MSFT'})

    def test_calculate_portfolio(self):
        with mock.patch('modules.investments.get_current_price', return_value=200.0):
            investments.add_investment('AAPL', 2, 100.0, '2024-01-01')
            rows = investments.get_all_investments()
            total, details = investments.calculate_portfolio(rows)
            self.assertAlmostEqual(total, 400.0)
            self.assertEqual(details[0]['gain'], 200.0)

    def test_calculate_portfolio_no_investments(self):
        total, details = investments.calculate_portfolio([])
        self.assertEqual(total, 0)
        self.assertEqual(details, [])

# --- expenses.py ---
from modules import expenses

class TestExpenses(unittest.TestCase):
    def test_gemini_category_suggestion(self):
        with mock.patch('modules.expenses.real_gemini_api_conversation', return_value='Food'):
            result = expenses.get_gemini_category_suggestion('Lunch at cafe', ['Food', 'Transport'])
            self.assertEqual(result, 'Food')
        self.assertIsNone(expenses.get_gemini_category_suggestion('Lunch', []))
        self.assertIsNone(expenses.get_gemini_category_suggestion('', ['Food']))

    def test_gemini_category_suggestion_invalid(self):
        with mock.patch('modules.expenses.real_gemini_api_conversation', return_value='NotACategory'):
            result = expenses.get_gemini_category_suggestion('Something', ['Food', 'Transport'])
            self.assertIsNone(result)

# --- budget.py ---
from modules import budget

class TestBudget(unittest.TestCase):
    def test_return_to_main_menu_exception(self):
        with self.assertRaises(budget.ReturnToMainMenu):
            raise budget.ReturnToMainMenu()

    def test_income_in_session(self):
        self.assertIn('income', budget.SESSION)

# --- ux.py ---
from modules import ux

class TestUX(unittest.TestCase):
    def test_print_success(self):
        with mock.patch('builtins.print') as mock_print:
            ux.print_success('ok')
            mock_print.assert_called()
    def test_ask_confirm_yes(self):
        with mock.patch('builtins.input', return_value='y'):
            self.assertTrue(ux.ask_confirm('Confirm?'))
    def test_ask_confirm_no(self):
        with mock.patch('builtins.input', return_value='n'):
            self.assertFalse(ux.ask_confirm('Confirm?'))
    def test_input_with_help_back(self):
        with mock.patch('builtins.input', return_value='back'):
            self.assertEqual(ux.input_with_help('Prompt'), 'back')
    def test_input_with_help_help(self):
        with mock.patch('builtins.input', side_effect=['help', 'value']):
            with mock.patch('modules.ux.print_info') as mock_print:
                result = ux.input_with_help('Prompt', help_text='Help!')
                mock_print.assert_called_with('Help!')
                self.assertEqual(result, 'value')

# --- gemini_api.py ---
from modules import gemini_api

class TestGeminiAPI(unittest.TestCase):
    def test_format_split_preview(self):
        split = [{"name": "Needs", "percent": 50, "examples": ["Rent"]}]
        result = gemini_api.format_split_preview(split, 2000)
        self.assertIn('Needs', result)
        self.assertIn('$1000', result)
    def test_summarize_current_budget(self):
        with mock.patch('modules.gemini_api.get_all_budgets', return_value=[]), \
             mock.patch('modules.gemini_api.get_all_expenses', return_value=[]):
            summary = gemini_api.summarize_current_budget()
            self.assertIn('Current budget', summary)
    def test_real_gemini_api_conversation_no_key(self):
        with mock.patch('modules.gemini_api.GEMINI_API_KEY', None):
            with mock.patch('modules.gemini_api.print_warning') as mock_warn:
                result = gemini_api.real_gemini_api_conversation([{"role": "user", "parts": [{"text": "hi"}]}])
                self.assertIsNone(result)
                mock_warn.assert_called()

# --- dashboard.py ---
from modules import dashboard

class TestDashboard(unittest.TestCase):
    def test_show_dashboard_runs(self):
        with mock.patch('modules.ux.print_info'), mock.patch('builtins.print'):
            with mock.patch('modules.dashboard.get_all_budgets', return_value=[]), \
                 mock.patch('modules.dashboard.get_all_expenses', return_value=[]):
                dashboard.show_dashboard()

# --- state.py ---
from modules import state

class TestState(unittest.TestCase):
    def test_undo_last_action_empty(self):
        state.UNDO_STACK.clear()
        with mock.patch('builtins.print') as mock_print:
            state.undo_last_action()
            mock_print.assert_called_with('Nothing to undo.')
    def test_undo_last_action_add_and_delete(self):
        # Add and undo a budget addition
        state.UNDO_STACK.clear()
        state.UNDO_STACK.append(('add_budget', ('TestCat', 'May', 2024)))
        with mock.patch('modules.state.delete_from_budget') as mock_delete, \
             mock.patch('builtins.print') as mock_print:
            state.undo_last_action()
            mock_delete.assert_called_with('TestCat', 'May', 2024)
            mock_print.assert_called()
        # Add and undo a budget deletion
        state.UNDO_STACK.append(('delete_budget', ('TestCat', 100, 'May', 2024)))
        with mock.patch('modules.state.add_to_budget') as mock_add, \
             mock.patch('builtins.print') as mock_print:
            state.undo_last_action()
            mock_add.assert_called_with('TestCat', 100, 'May', 2024)
            mock_print.assert_called()

# --- demo.py ---
from modules import demo

class TestDemo(unittest.TestCase):
    def test_demo_budgets_exist(self):
        self.assertTrue(len(demo.DEMO_BUDGETS) > 0)
    def test_demo_expenses_exist(self):
        self.assertTrue(len(demo.DEMO_EXPENSES) > 0)
    def test_run_demo_mode_backup_restore(self):
        # Patch DB_PATH and file operations
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            fake_db = tmp.name
        try:
            with mock.patch('modules.demo.DB_PATH', fake_db), \
                 mock.patch('os.path.exists', return_value=True), \
                 mock.patch('shutil.copy'), \
                 mock.patch('shutil.move'), \
                 mock.patch('sqlite3.connect') as mock_connect, \
                 mock.patch('modules.demo.show_dashboard'), \
                 mock.patch('modules.demo.set_income'), \
                 mock.patch('modules.demo.input_with_help', side_effect=['5']):
                mock_conn = mock.MagicMock()
                mock_connect.return_value = mock_conn
                demo.run_demo_mode()
                mock_connect.assert_called()
                mock_conn.close.assert_called()
        finally:
            os.remove(fake_db)

if __name__ == '__main__':
    unittest.main()

>>>>>>> 6d49a1c (feat: investments added + last min changes)
