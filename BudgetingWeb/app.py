from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from datetime import datetime
from db import db_operations
from dotenv import load_dotenv
import requests
from db import investments as investments_db
from db.database import reset_db
import json
from functools import lru_cache

# Load environment variables from .env if present
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Helper to get current month and year
now = datetime.now()
CURRENT_MONTH = now.strftime('%B')
CURRENT_YEAR = now.year

# Demo data
DEMO_BUDGETS = [
    ('Food', 500, 'July', 2025),
    ('Rent', 1200, 'July', 2025),
    ('Entertainment', 200, 'July', 2025),
    ('Groceries', 350, 'July', 2025),
    ('Transit', 100, 'July', 2025),
    ('Shopping', 250, 'July', 2025),
    ('Bills & Fees', 180, 'July', 2025),
]
DEMO_EXPENSES = [
    (22.42, 'Food', 'Groceries', '2025-07-16', 'USD'),
    (15, 'Entertainment', 'Movie streaming service', '2025-07-16', 'USD'),
    (11.82, 'Shopping', 'Dining', '2025-07-13', 'USD'),
    (45.00, 'Groceries', 'Weekly groceries', '2025-07-10', 'USD'),
    (60.00, 'Transit', 'Monthly subway pass', '2025-07-01', 'USD'),
    (1200.00, 'Rent', 'Monthly rent', '2025-07-01', 'USD'),
    (80.00, 'Bills & Fees', 'Electricity bill', '2025-07-05', 'USD'),
    (30.00, 'Entertainment', 'Concert ticket', '2025-07-12', 'USD'),
    (55.00, 'Shopping', 'Clothes', '2025-07-08', 'USD'),
    (18.00, 'Food', 'Takeout', '2025-07-15', 'USD'),
    (12.00, 'Groceries', 'Snacks', '2025-07-14', 'USD'),
    (25.00, 'Bills & Fees', 'Internet bill', '2025-07-03', 'USD'),
    (10.00, 'Transit', 'Taxi', '2025-07-09', 'USD'),
    (40.00, 'Entertainment', 'Theater', '2025-07-11', 'USD'),
]
DEMO_INCOME = 2500
DEMO_INVESTMENTS = [
    (1, 'AAPL', 10, 150.00, '2024-10-01'),
    (2, 'MSFT', 5, 320.00, '2024-11-15'),
]
DEMO_GOALS = [
    (1, 'Emergency Fund', 2000, 500, '2025-12-31'),
    (2, 'Vacation', 1500, 200, '2025-09-01'),
    (3, 'New Laptop', 1200, 300, '2025-10-15'),
]

CURRENCY_LIST = [
    ('USD', '$'),
    ('EUR', '€'),
    ('GBP', '£'),
    ('INR', '₹'),
    ('CAD', 'C$'),
    ('AUD', 'A$'),
    ('JPY', '¥'),
    ('CNY', '¥'),
    ('CHF', 'Fr'),
    ('SGD', 'S$'),
    ('ZAR', 'R'),
]

def get_currency_symbol(code):
    for c, s in CURRENCY_LIST:
        if c == code:
            return s
    return code

@lru_cache(maxsize=32)
def fetch_exchange_rate(base, target):
    if base == target:
        return 1.0
    try:
        # Use exchangerate-api.com endpoint and API key in path
        url = f"https://v6.exchangerate-api.com/v6/41f126546f9e601c9de74e2c/latest/{base}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        return data['conversion_rates'][target]
    except Exception:
        return 1.0

@app.route('/set_currency', methods=['POST', 'GET'])
def set_currency():
    code = request.values.get('currency', 'USD').upper()
    if code not in [c[0] for c in CURRENCY_LIST]:
        code = 'USD'
    session['currency'] = code
    # Fetch and store the rate to USD
    rate = fetch_exchange_rate('USD', code)
    session['currency_rate'] = rate
    return redirect(request.referrer or url_for('dashboard'))

def summarize_current_budget_web():
    budgets = db_operations.get_all_budgets()
    expenses = db_operations.get_all_expenses()
    goals = db_operations.get_all_goals()
    income = db_operations.get_income(CURRENT_MONTH, CURRENT_YEAR)
    # Investment summary
    if session.get('demo_mode'):
        investments = DEMO_INVESTMENTS
        investments_snapshot = [
            {
                'symbol': inv[1],
                'shares': inv[2],
                'purchase_price': inv[3],
                'current_price': inv[3],
                'value': inv[2] * inv[3],
                'gain': 0,
                'purchase_date': inv[4]
            } for inv in investments
        ]
        total_investments = sum(inv['value'] for inv in investments_snapshot)
    else:
        investments = investments_db.get_all_investments()
        total_investments, investments_snapshot = investments_db.calculate_portfolio(investments)
    cat_limits = {row[0]: row[1] for row in budgets if row[2] == CURRENT_MONTH and str(row[3]) == str(CURRENT_YEAR)}
    cat_spent = {cat: 0 for cat in cat_limits}
    for amt, cat, *_ in expenses:
        if cat in cat_spent:
            cat_spent[cat] += amt
    summary_lines = [f"Current budget for {CURRENT_MONTH} {CURRENT_YEAR}:"]
    if income:
        summary_lines.append(f"Monthly income: ${income:.2f}")
    total_budget = sum(cat_limits.values())
    total_spent = sum(cat_spent.values())
    summary_lines.append(f"Total budget: ${total_budget:.2f}, Total spent: ${total_spent:.2f}")
    # Explicit budget categories section
    current_budgets = [b for b in budgets if b[3] == CURRENT_MONTH and b[4] == CURRENT_YEAR]
    if current_budgets:
        summary_lines.append("All Budget Categories for this month:")
        for b in current_budgets:
            summary_lines.append(f"- {b[1]}: limit ${b[2]:.2f}")
    # Detailed budget categories
    if cat_limits:
        summary_lines.append("Budget Categories:")
        for cat in cat_limits:
            summary_lines.append(f"- {cat}: limit ${cat_limits[cat]:.2f}, spent ${cat_spent[cat]:.2f}")
    # Detailed expenses
    if expenses:
        summary_lines.append("Expenses:")
        for e in expenses:
            summary_lines.append(f"- ${e[0]:.2f} on {e[1]} ({e[2]}) at {e[3]}")
    if goals:
        summary_lines.append("Goals:")
        for g in goals:
            summary_lines.append(f"- {g[1]}: target ${g[2]:.2f}, saved ${g[3]:.2f}, deadline {g[4] if g[4] else 'N/A'}")
    # Add investments summary
    if investments_snapshot:
        summary_lines.append("Investments:")
        for inv in investments_snapshot:
            summary_lines.append(f"- {inv['symbol']}: {inv['shares']} shares, buy @ ${inv['purchase_price']:.2f}, current @ ${inv['current_price']:.2f}, value ${inv['value']:.2f}, gain/loss ${inv['gain']:.2f}")
        summary_lines.append(f"Total portfolio value: ${total_investments:.2f}")
    return "\n".join(summary_lines)

@app.route('/demo')
def demo_mode():
    session['demo_mode'] = True
    return redirect(url_for('dashboard'))

@app.route('/exit_demo')
def exit_demo():
    session.pop('demo_mode', None)
    return redirect(url_for('dashboard'))

@app.route('/')
def dashboard():
    # Always ensure currency and rate are set and up to date
    if 'currency' not in session:
        session['currency'] = 'USD'
    code = session['currency']
    # Always fetch the latest rate for accuracy
    rate = fetch_exchange_rate('USD', code)
    session['currency_rate'] = rate
    if session.get('demo_mode'):
        # Use demo data
        budgets = DEMO_BUDGETS
        expenses = DEMO_EXPENSES
        income = DEMO_INCOME
        total_budget = sum(b[1] for b in budgets)
        total_spent = sum(e[0] for e in expenses)
        categories = []
        for b in budgets:
            spent = sum(e[0] for e in expenses if e[1] == b[0])
            categories.append({'name': b[0], 'budget': b[1], 'spent': spent})
        data = {
            'total_budget': total_budget,
            'total_spent': total_spent,
            'categories': categories,
            'income': income
        }
        recent_expenses = expenses[-5:][::-1]  # last 5 demo expenses, most recent first
        investments = DEMO_INVESTMENTS
        investments_snapshot = [
            {'symbol': inv[1], 'shares': inv[2], 'purchase_price': inv[3], 'purchase_date': inv[4], 'value': inv[2] * inv[3]} for inv in investments
        ]
        demo_goals = DEMO_GOALS
        # Ensure currency and rate are always set in demo mode
        if 'currency' not in session:
            session['currency'] = 'USD'
        if 'currency_rate' not in session:
            session['currency_rate'] = 1.0
        return render_template('dashboard.html', data=data, now=datetime.now(), goals=demo_goals, recent_expenses=recent_expenses, investments_snapshot=investments_snapshot, get_currency_symbol=get_currency_symbol, CURRENCY_LIST=CURRENCY_LIST)
    # Fetch budgets and expenses from the database
    budgets = db_operations.get_all_budgets()
    expenses = db_operations.get_all_expenses()
    income = db_operations.get_income(CURRENT_MONTH, CURRENT_YEAR)
    # Calculate totals
    total_budget = sum(b[2] for b in budgets if b[3] == CURRENT_MONTH and b[4] == CURRENT_YEAR)
    total_spent = sum(e[1] for e in expenses if e[4][:7] == f"{now.year}-{now.month:02d}")
    # Prepare category breakdown (ensure all categories from budgets are in categories table)
    categories = []
    for b in budgets:
        if b[3] == CURRENT_MONTH and b[4] == CURRENT_YEAR:
            spent = sum(e[1] for e in expenses if e[2] == b[1] and e[4][:7] == f"{now.year}-{now.month:02d}")
            # Ensure category exists in categories table, add if missing
            cat = db_operations.get_category_by_name(b[1])
            if not cat:
                db_operations.add_category_if_missing(b[1])  # Only add category, not a budget row
                cat = db_operations.get_category_by_name(b[1])
            color = cat[2] if cat else '#607D8B'
            categories.append({'name': b[1], 'budget': b[2], 'spent': spent, 'color': color})
    data = {
        'total_budget': total_budget,
        'total_spent': total_spent,
        'categories': categories,
        'income': income
    }
    goals = db_operations.get_all_goals()
    recent_expenses = db_operations.get_recent_expenses(5)
    investments = investments_db.get_all_investments()
    _, investments_snapshot = investments_db.calculate_portfolio(investments)
    # Ensure currency and rate are always set
    if 'currency' not in session:
        session['currency'] = 'USD'
    if 'currency_rate' not in session:
        session['currency_rate'] = 1.0
    return render_template('dashboard.html', data=data, now=datetime.now(), goals=goals, recent_expenses=recent_expenses, investments_snapshot=investments_snapshot, get_currency_symbol=get_currency_symbol, CURRENCY_LIST=CURRENCY_LIST)

@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    message = None
    error = None
    ai_suggestion = None
    if request.method == 'GET':
        reset_db()
    if request.method == 'POST':
        income = request.form.get('income')
        rent = request.form.get('rent')
        bills = request.form.getlist('bills[]')
        bill_amounts = request.form.getlist('bill_amounts[]')
        goals = request.form.getlist('goals')
        # Compose bills string for AI
        bills_str = ", ".join([f"{name} (${amt})" for name, amt in zip(bills, bill_amounts) if name and amt]) if bills and bill_amounts else "None"
        # Compose AI prompt
        if not GEMINI_API_KEY:
            error = "Gemini API key not set. Please set GEMINI_API_KEY in your .env file."
            return render_template('onboarding.html', message=message, error=error)
        prompt = (
            "Given the following financial goals: " + ", ".join(goals) + ". "
            f"The user's monthly after-tax income is ${income}. "
            f"Their rent/mortgage is ${rent} per month. "
            f"Their fixed monthly bills/expenses are: {bills_str}. "
            "Suggest a practical budget split (categories, percentages, and a short description for each) that best helps achieve these goals and covers their fixed expenses. "
            "Also suggest 2-3 specific savings goals (with target amounts and deadlines if possible) based on the user's info and goals. "
            "Return the result as a JSON object with two keys: 'budget_split' (a list of objects with 'name', 'percent', 'description') and 'savings_goals' (a list of objects with 'name', 'target_amount', 'deadline', 'description'). "
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
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                answer = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', None)
                if answer:
                    # Try to extract JSON from the response
                    start = answer.find('{')
                    end = answer.rfind('}')
                    if start != -1 and end != -1:
                        json_str = answer[start:end+1]
                        try:
                            ai_suggestion = json.loads(json_str)
                        except Exception:
                            ai_suggestion = None
                if not ai_suggestion:
                    error = "Could not parse AI suggestion. Please try again."
                    return render_template('onboarding.html', message=message, error=error)
                # Show confirmation page with AI suggestion
                return render_template('onboarding_confirm.html', income=income, rent=rent, bills=zip(bills, bill_amounts), goals=goals, ai_suggestion=ai_suggestion)
            else:
                error = f"Gemini API error: {response.status_code}"
                return render_template('onboarding.html', message=message, error=error)
        except Exception as e:
            error = f"Error connecting to Gemini API: {e}"
            return render_template('onboarding.html', message=message, error=error)
    return render_template('onboarding.html', message=message, error=error)

@app.route('/onboarding/confirm', methods=['POST'])
def onboarding_confirm():
    income = request.form.get('income')
    rent = request.form.get('rent')
    bills = request.form.getlist('bills[]')
    bill_amounts = request.form.getlist('bill_amounts[]')
    goals = request.form.getlist('goals')
    budget_names = request.form.getlist('budget_name[]')
    budget_percents = request.form.getlist('budget_percent[]')
    # budget_descs = request.form.getlist('budget_desc[]')  # Not used for DB
    goal_names = request.form.getlist('goal_name[]')
    goal_targets = request.form.getlist('goal_target[]')
    goal_deadlines = request.form.getlist('goal_deadline[]')
    # goal_descs = request.form.getlist('goal_desc[]')  # Not used for DB
    # Save income
    if income:
        db_operations.set_income(CURRENT_MONTH, CURRENT_YEAR, float(income))
    # Only add AI-suggested budget split as categories (proportional to income)
    if income and budget_names and budget_percents:
        for name, percent in zip(budget_names, budget_percents):
            if name and percent:
                limit = float(income) * float(percent) / 100.0
                db_operations.add_to_budget(name, limit, CURRENT_MONTH, CURRENT_YEAR)
    # Save AI-suggested savings goals
    if goal_names and goal_targets:
        for name, target, deadline in zip(goal_names, goal_targets, goal_deadlines):
            if name and target:
                db_operations.add_goal(name, float(target), 0, deadline)
    return redirect(url_for('dashboard'))

@app.route('/budget', methods=['GET', 'POST'])
def budget():
    message = None
    if session.get('demo_mode'):
        budgets = DEMO_BUDGETS
        categories = list({b[0] for b in budgets})
        return render_template('budget.html', budgets=[(None, b[0], b[1], b[2], b[3], '#607D8B') for b in budgets], message=message, budget_categories=categories, category_colors={c: '#607D8B' for c in categories})
    categories = db_operations.get_all_categories()
    if request.method == 'POST':
        category = request.form.get('category')
        limit = request.form.get('budget')
        if category and limit:
            db_operations.add_to_budget(category, float(limit), CURRENT_MONTH, CURRENT_YEAR)
            message = 'Budget category added!'
    # Show all budgets for current month/year
    budgets = [b for b in db_operations.get_all_budgets() if b[3] == CURRENT_MONTH and b[4] == CURRENT_YEAR]
    return render_template('budget.html', budgets=budgets, message=message, budget_categories=[c[1] for c in categories], category_colors={c[1]: c[2] for c in categories})

@app.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
def edit_budget(budget_id):
    budget = next((b for b in db_operations.get_all_budgets() if b[0] == budget_id), None)
    categories = db_operations.get_all_categories()
    if not budget:
        return redirect(url_for('budget'))
    if request.method == 'POST':
        category = request.form.get('category')
        limit = request.form.get('budget')
        if category and limit:
            db_operations.update_budget_by_id(budget_id, category, float(limit), budget[3], budget[4])
            return redirect(url_for('budget'))
    return render_template('budget.html', edit_budget=budget, budgets=[b for b in db_operations.get_all_budgets() if b[3] == CURRENT_MONTH and b[4] == CURRENT_YEAR], budget_categories=[c[1] for c in categories], category_colors={c[1]: c[2] for c in categories})

@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
    db_operations.delete_budget_by_id(budget_id)
    return redirect(url_for('budget'))

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    message = None
    if session.get('demo_mode'):
        budgets = DEMO_BUDGETS
        budget_categories = [b[0] for b in budgets]
        expenses = DEMO_EXPENSES
        return render_template('expenses.html', expenses=expenses, message=message, budget_categories=budget_categories)
    # Only show categories that have a budget for the current month/year
    budgets = [b for b in db_operations.get_all_budgets() if b[3] == CURRENT_MONTH and b[4] == CURRENT_YEAR]
    budget_categories = [b[1] for b in budgets]
    if request.method == 'POST':
        category = request.form.get('category')
        amount = request.form.get('amount')
        description = request.form.get('description', '')
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        currency = request.form.get('currency', 'USD')
        if category and amount:
            db_operations.add_expense(float(amount), category, description, date, currency)
            message = 'Expense added!'
    # Show all expenses for current month/year
    expenses = [e for e in db_operations.get_all_expenses() if e[4][:7] == f"{now.year}-{now.month:02d}"]
    return render_template('expenses.html', expenses=expenses, message=message, budget_categories=budget_categories)

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    expense = db_operations.get_expense_by_id(expense_id)
    if not expense:
        return redirect(url_for('expenses'))
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        date = request.form.get('date')
        currency = request.form.get('currency')
        db_operations.update_expense_by_id(expense_id, amount, category, description, date, currency)
        return redirect(url_for('expenses'))
    # Get categories for dropdown
    budgets = [b for b in db_operations.get_all_budgets() if b[3] == CURRENT_MONTH and b[4] == CURRENT_YEAR]
    budget_categories = [b[1] for b in budgets]
    return render_template('edit_expense.html', expense=expense, budget_categories=budget_categories)

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    db_operations.delete_expense_by_id(expense_id)
    return redirect(url_for('expenses'))

@app.route('/advice', methods=['GET', 'POST'])
def advice():
    ai_response = None
    error = None
    if request.method == 'POST':
        question = request.form.get('question')
        if not GEMINI_API_KEY:
            error = "Gemini API key not set. Please set GEMINI_API_KEY in your .env file."
        else:
            # Compose system prompt
            budget_context = summarize_current_budget_web()
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
            conversation = [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{question}"}]}
            ]
            try:
                response = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": GEMINI_API_KEY
                    },
                    json={"contents": conversation},
                    timeout=60
                )
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', None)
                    if not ai_response:
                        error = "No advice received from Gemini."
                else:
                    error = f"Gemini API error: {response.status_code}"
            except Exception as e:
                error = f"Error connecting to Gemini API: {e}"
    return render_template('advice.html', ai_response=ai_response, error=error)

@app.route('/advice/chat', methods=['POST'])
def advice_chat():
    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({'error': 'No question provided.'}), 400
    if not GEMINI_API_KEY:
        return jsonify({'error': 'Gemini API key not set.'}), 500
    # Compose system prompt
    budget_context = summarize_current_budget_web()
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
    conversation = [
        {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{question}"}]}
    ]
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            json={"contents": conversation},
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', None)
            if not ai_response:
                return jsonify({'error': 'No advice received from Gemini.'}), 500
            return jsonify({'ai_response': ai_response})
        else:
            return jsonify({'error': f'Gemini API error: {response.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error connecting to Gemini API: {e}'}), 500

@app.route('/investments')
def investments():
    if session.get('demo_mode'):
        investments = DEMO_INVESTMENTS
        investments_snapshot = [
            {
                'symbol': inv[1],
                'shares': inv[2],
                'purchase_price': inv[3],
                'current_price': inv[3],  # For demo, current = purchase
                'value': inv[2] * inv[3],
                'gain': 0,  # No gain/loss in demo
                'purchase_date': inv[4]
            } for inv in investments
        ]
        total = sum(inv['value'] for inv in investments_snapshot)
        return render_template('investments.html', details=investments_snapshot, total=total)
    investments = investments_db.get_all_investments()
    total, details = investments_db.calculate_portfolio(investments)
    return render_template('investments.html', details=details, total=total)

@app.route('/investments/add', methods=['GET', 'POST'])
def add_investment():
    message = None
    error = None
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        shares = request.form.get('shares')
        price = request.form.get('purchase_price')
        date = request.form.get('purchase_date') or datetime.now().strftime('%Y-%m-%d')
        try:
            if not (symbol and shares and price):
                error = 'All fields except date are required.'
            else:
                investments_db.add_investment(symbol, float(shares), float(price), date)
                message = f'Investment in {symbol.upper()} added!'
        except Exception as e:
            error = f'Error: {e}'
    return render_template('add_investment.html', message=message, error=error)

@app.route('/goals')
def goals():
    if session.get('demo_mode'):
        return render_template('goals.html', goals=DEMO_GOALS)
    goals = db_operations.get_all_goals()
    return render_template('goals.html', goals=goals)

@app.route('/goals/add', methods=['GET', 'POST'])
def add_goal():
    message = None
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        target_amount = request.form.get('target_amount')
        saved_amount = request.form.get('saved_amount', 0)
        deadline = request.form.get('deadline')
        if not (name and target_amount):
            error = 'Name and target amount are required.'
        else:
            db_operations.add_goal(name, target_amount, saved_amount, deadline)
            message = f'Goal "{name}" added!'
            return redirect(url_for('goals'))
    return render_template('add_goal.html', message=message, error=error)

@app.route('/goals/edit/<int:goal_id>', methods=['GET', 'POST'])
def edit_goal(goal_id):
    goal = db_operations.get_goal_by_id(goal_id)
    if not goal:
        return redirect(url_for('goals'))
    message = None
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        target_amount = request.form.get('target_amount')
        saved_amount = request.form.get('saved_amount', 0)
        deadline = request.form.get('deadline')
        if not (name and target_amount):
            error = 'Name and target amount are required.'
        else:
            db_operations.update_goal(goal_id, name, target_amount, saved_amount, deadline)
            message = f'Goal updated!'
            return redirect(url_for('goals'))
    return render_template('edit_goal.html', goal=goal, message=message, error=error)

@app.route('/goals/delete/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    db_operations.delete_goal(goal_id)
    return redirect(url_for('goals'))

@app.route('/reset_db')
def reset_db_route():
    reset_db()
    return 'Database has been reset. All data cleared and default categories restored.'

@app.route('/reset_budget', methods=['POST'])
def reset_budget():
    reset_db()
    return redirect(url_for('onboarding'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)