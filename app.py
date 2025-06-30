# library that allows us to show tabular data
from tabulate import tabulate

# Format Budgetting in a way similar to google sheets for easy visualization on the CL
# Note: Could just display a sql table instead?
data = [
    ["Alice", 24, "Engineer"],
    ["Bob", 30, "Teacher"]
]

table = tabulate(data, headers = ["Name", "Age", "Profession"], tablefmt = "grid")


print(table)