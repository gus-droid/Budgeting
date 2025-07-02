# library that allows us to show tabular data
from tabulate import tabulate


# Format Budgetting in a way similar to google sheets for easy visualization on the CL
# Note: Could just display a sql table instead?
data = [
    ["Alice", 24, "Engineer"],
    ["Bob", 30, "Teacher"]
]

table = tabulate(data, headers = ["Name", "Age", "Profession"], tablefmt = "grid")

'''
display on command line to user 
"What do you want to do today?":
1.) budget
2.) Check my expenses
3.) Get Advice (this is where they can type a question and it'll be sent to gemini api)

If they pick 1:
    - 1.) add category, limit_amount, month, year
    - 2.) Delete category, limit_amount, month, year
    - 3.) show budget

If they pick 2:
    - 1.) Add amount, category, description, date, currency, converted_amount_usd
    - 2.) Delete amount, category, description, date, currency, converted_amount_usd
    - 3.) show expenses

'''

print(table)