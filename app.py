from tabulate import tabulate

# Format it a certain Way
data = [
    ["Alice", 24, "Engineer"],
    ["Bob", 30, "Teacher"]
]

table = tabulate(data, headers = ["Name", "Age", "Profession"], tablefmt = "grid")


print(table)