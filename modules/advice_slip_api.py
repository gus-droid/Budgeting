import requests

"""Function to output random string of advice"""
def get_random_advice():
    response = requests.get("https://api.adviceslip.com/advice")
    data = response.json()
    return data["slip"]["advice"]

# test print
print(get_random_advice())