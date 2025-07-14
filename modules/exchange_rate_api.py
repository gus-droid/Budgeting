import os
from dotenv import load_dotenv
import requests
import random

# load api key
load_dotenv()
api_key = os.getenv("EXCHANGE_RATE_API_KEY")
url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'

# load data
response = requests.get(url)
data = response.json()
# list of valid currencies
valid_currencies = data["conversion_rates"].keys()

"""Inputs: string Current Currency, string currency wish to be converted to
Requirements: 
    1.) Ask user to input a 3 symbol current currency?
    2.) Definitely ask user to input a 3 symbol desired currency

    Outputs: return conversion number (Do we want a pure integer or string: "integer_amount ABC")
    Where ABC is the abbreviation for some currency.
"""
def currency_conversion(currency, desired_currency):
    # if the currency is valid, load the conversion data
    if currency in valid_currencies:
        url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{currency}'
        response = requests.get(url)
        data = response.json()
        conversion = data["conversion_rates"][desired_currency]
        return round(conversion, 2)
    else:
        return "Please Input A Valid Currency"

print(currency_conversion("USD", "CNY"))
