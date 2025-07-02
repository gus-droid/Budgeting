"""
gemini_api.py
-------------
Handles Gemini API integration and conversational budgeting advice logic for the CLI Budgeting Tool.
"""
import os
import requests
from dotenv import load_dotenv
from modules.ux import print_info, print_warning, print_error, input_with_help, progress_bar
from db.db_operations import get_all_budgets, get_all_expenses
from modules.state import SESSION

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


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
    progress_bar("Contacting Gemini API")
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


def get_gemini_budget_split(goals, income, rent, bills_str):
    """Ask Gemini for a unique budget split based on user goals, income, rent, and fixed bills."""
    if not GEMINI_API_KEY:
        return None
    progress_bar("Contacting Gemini API for budget split")
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
        import textwrap
        desc_wrapped = "\n".join(textwrap.wrap(desc, width=48))
        preview.append([
            cat["name"],
            f"{percent}%",
            f"${amt}",
            desc_wrapped
        ])
    from tabulate import tabulate
    headers = ["Category", "%", "Amount", "Description" if is_gemini else "Example Expenses"]
    return tabulate(preview, headers=headers, tablefmt="fancy_grid", stralign="center", numalign="center") 