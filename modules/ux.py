"""
ux.py
-----
User experience and CLI helper functions for the Budgeting Tool.
Handles colored output, user prompts, and progress bars.
"""
from colorama import init, Fore, Style
import time
import textwrap

init(autoreset=True)

# Color constants
PASTEL_ANSI_CODES = [186, 189, 151, 159, 117, 180, 144, 223, 222, 221, 225, 224, 194, 191, 153, 150, 186, 189, 151, 159, 117, 180, 144, 223, 222, 221, 225, 224, 194, 191]
PASTEL_COLORS = [f"\033[38;5;{code}m" for code in PASTEL_ANSI_CODES]
RESET_COLOR = Style.RESET_ALL


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


def progress_bar(task="Processing", duration=1.5):
    """Display a simple progress bar for a given task.

    Shows a progress bar in the CLI for a specified duration to indicate processing.

    Args:
        task (str, optional): Description of the task. Defaults to "Processing".
        duration (float, optional): Duration in seconds. Defaults to 1.5.
    """
    print(f"{Fore.CYAN}{task}...{Style.RESET_ALL}", end=" ")
    for _ in range(10):
        print(Fore.YELLOW + "█", end="", flush=True)
        time.sleep(duration / 10)
    print(Style.RESET_ALL)


def get_category_color_map(categories):
    """Assign a unique pastel color to each category for CLI display.

    Maps each category to a pastel color for use in CLI bar charts and tables. Colors repeat if there are more categories than available colors.

    Args:
        categories (list[str]): List of category names.

    Returns:
        dict: Mapping of category names to ANSI color codes.
    """
    color_map = {}
    n = len(categories)
    if n > len(PASTEL_COLORS):
        print_warning(f"More than {len(PASTEL_COLORS)} categories! Some colors will repeat.")
    for i, cat in enumerate(categories):
        color_map[cat] = PASTEL_COLORS[i % len(PASTEL_COLORS)]
    return color_map


def per_category_bar_chart(cat_spent, cat_limits, width=40, color_map=None):
    """Display a bar chart of spending by category.

    Prints a horizontal bar chart for each category, showing the proportion of budget used.

    Args:
        cat_spent (dict): Mapping of category names to amounts spent.
        cat_limits (dict): Mapping of category names to budget limits.
        width (int, optional): Width of the bar chart. Defaults to 40.
        color_map (dict, optional): Mapping of category names to colors. Defaults to None.
    """
    # Find max lengths for alignment
    max_cat_len = max((len(cat) for cat in cat_limits), default=15)
    amount_width = 10
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
        # Align category and amounts
        cat_str = f"{cat:<{max_cat_len}}"
        used_str = f"${used:.2f}".rjust(amount_width)
        limit_str = f"${limit:.2f}".rjust(amount_width)
        # Make used amount red if over budget
        used_color = Fore.RED if used > limit else Fore.YELLOW
        print(f"|{bar}| {color}{cat_str}{RESET_COLOR} {used_color}{used_str}{Style.RESET_ALL} of {limit_str} ({percent_str})") 