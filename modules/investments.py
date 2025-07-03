import datetime
from tabulate import tabulate
import matplotlib.pyplot as plt
import yfinance as yf
import sqlite3
from modules.ux import print_info, print_success, input_with_help
from modules.budget import ReturnToMainMenu
import plotext as plt
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'db'))
from database import get_db_path

DB_PATH = get_db_path()

def add_investment(symbol, shares, purchase_price, purchase_date):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                shares REAL NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date TEXT
            )
            """
        )
        c.execute(
            "INSERT INTO investments (symbol, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
            (symbol.upper(), shares, purchase_price, purchase_date)
        )
        conn.commit()

def get_all_investments():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, symbol, shares, purchase_price, purchase_date FROM investments")
        return c.fetchall()

def get_current_price(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    if not data.empty:
        return float(data['Close'].iloc[0])
    return None

def calculate_portfolio(investments):
    details = []
    total_value = 0
    for inv in investments:
        id, symbol, shares, purchase_price, purchase_date = inv
        current_price = get_current_price(symbol)
        if current_price:
            value = current_price * shares
            gain = value - (purchase_price * shares)
            details.append({
                "id": id,
                "symbol": symbol,
                "shares": shares,
                "purchase_price": purchase_price,
                "current_price": current_price,
                "value": value,
                "gain": gain,
                "purchase_date": purchase_date
            })
            total_value += value
    return total_value, details

def show_portfolio(details, total):
    table = []
    for d in details:
        gain = d['gain']
        # Color gain: green if positive, red if negative
        if gain > 0:
            gain_str = f"\033[92m${gain:.2f}\033[0m"  # Green
        elif gain < 0:
            gain_str = f"\033[91m${gain:.2f}\033[0m"  # Red
        else:
            gain_str = f"${gain:.2f}"
        table.append([
            d['symbol'],
            d['shares'],
            f"${d['purchase_price']:.2f}",
            f"${d['current_price']:.2f}",
            f"${d['value']:.2f}",
            gain_str,
            d['purchase_date']
        ])
    print(tabulate(table, headers=["Symbol", "Shares", "Buy Price", "Current Price", "Value", "Gain/Loss", "Date"], tablefmt="fancy_grid"))
    print_info(f"Total Portfolio Value: ${total:.2f}")

def summarize_portfolio():
    investments = get_all_investments()
    total, details = calculate_portfolio(investments)
    if not details:
        return "No investments in portfolio."
    lines = ["Current investment portfolio:"]
    for d in details:
        gain_str = f"+${d['gain']:.2f}" if d['gain'] > 0 else f"-${abs(d['gain']):.2f}"
        lines.append(
            f"- {d['symbol']}: {d['shares']} shares, bought at ${d['purchase_price']:.2f}, current ${d['current_price']:.2f}, value ${d['value']:.2f}, gain/loss {gain_str} (purchased {d['purchase_date']})"
        )
    lines.append(f"Total portfolio value: ${total:.2f}")
    return "\n".join(lines)

def investments_menu(demo_mode=False):
    while True:
        print_info("\n[Investments Menu]")
        print("1. Add investment")
        print("2. Show portfolio")
        if demo_mode:
            print("3. Back to Demo Menu")
        else:
            print("4. Back to main menu")
        choice = input_with_help("Choose an option:")
        if choice == 'back' or (demo_mode and choice == '3') or (not demo_mode and choice == '4'):
            if demo_mode:
                break
            else:
                raise ReturnToMainMenu()
        elif choice == '1':
            symbol = input_with_help("Stock symbol (e.g. AAPL):")
            if symbol == 'back':
                if demo_mode:
                    break
                else:
                    continue
            shares = input_with_help("Number of shares:")
            if shares == 'back':
                if demo_mode:
                    break
                else:
                    continue
            price = input_with_help("Purchase price per share:")
            if price == 'back':
                if demo_mode:
                    break
                else:
                    continue
            date = input_with_help("Purchase date (YYYY-MM-DD):")
            if date == 'back':
                if demo_mode:
                    break
                else:
                    continue
            if not date:
                date = datetime.datetime.now().strftime('%Y-%m-%d')
            add_investment(symbol, float(shares), float(price), date)
            print_success("Investment added!")
        elif choice == '2':
            investments = get_all_investments()
            total, details = calculate_portfolio(investments)
            show_portfolio(details, total) 