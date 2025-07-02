# CLI Budgeting Tool

A powerful, interactive command-line tool to help you manage your personal finances, set up budgets, track expenses, and get AI-powered financial advice—all from your terminal.

---

## Features

- **Automatic Budget Setup**: Guided wizard to set up a budget based on your income, rent, bills, and financial goals. Optionally uses Google Gemini AI to suggest a personalized budget split.
- **Customizable Budgets**: Add, edit, or delete budget categories and limits for each month.
- **Expense Tracking**: Log, view, and delete expenses by category, with color-coded feedback for overspending.
- **Dashboard**: Visual summary of your budget, spending, and category breakdowns for the current month.
- **Conversational Advice**: Ask budgeting questions and get tailored, actionable advice from Gemini AI, with your real budget as context.
- **Undo Actions**: Undo your last budget or expense change.
- **Demo Mode**: Try out the app with sample data, risk-free.

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd SEO-Project-1/Budgeting
   ```
2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **(Optional) Set up Gemini API key:**
   - Create a `.env` file in the `Budgeting/` directory:
     ```
     GEMINI_API_KEY=your_google_gemini_api_key_here
     ```
   - Without an API key, the app will use default rules and skip AI-powered features.

---

## Usage

Run the CLI tool from the `Budgeting/` directory:

```bash
python cli.py
```

### Main Menu Options

1. **Set up automatic budget**: Launches a wizard to create a budget based on your income, rent, bills, and goals. Accept or customize AI suggestions.
2. **Manage Budget & Expenses**:
   - **Budget**: Add, edit, or delete budget categories and limits for the current month.
   - **Expenses**: Add, view, or delete expenses. Get AI category suggestions for new expenses.
3. **Get Advice (chat)**: Enter a conversational mode to ask budgeting questions and receive advice from Gemini AI.
4. **Other Options**: Access demo mode, undo last action, or view additional features.
5. **Exit**: Quit the application.

### Tips
- Type `'help'` at any prompt for guidance.
- Type `'back'` to return to the previous menu.
- In advice mode, type `/exit` to leave the chat.

---

## Dependencies
- Python 3.7+
- [tabulate](https://pypi.org/project/tabulate/)
- [colorama](https://pypi.org/project/colorama/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [requests](https://pypi.org/project/requests/)

Install all dependencies with:
```bash
pip install -r requirements.txt
```

---

## Project Structure

```
Budgeting/
  cli.py                # Main CLI entry point
  app.py                # Core logic and helpers
  modules/              # Feature modules (budget, expenses, dashboard, AI, etc.)
  db/                   # SQLite database and operations
  requirements.txt      # Python dependencies
  README.md             # This file
  tests/                # Test scripts
```

---

## Data Storage
- Uses SQLite (`personal_finance.db`) for persistent storage of budgets and expenses.
- No data is sent externally except when using Gemini AI features (if enabled).

---

## Credits
- Developed by [Your Name or Team].
- AI features powered by [Google Gemini](https://ai.google.com/gemini/).
- Open source libraries: tabulate, colorama, python-dotenv, requests.

---

## License
[MIT License](../LICENSE) (or specify your license here)
