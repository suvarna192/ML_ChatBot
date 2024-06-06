
import pandas as pd
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from bank import bank_multipliers


# get preapproved loan
def calculate_preapproved_loan(loan_amount, bank_name, product=None, customer_profile=None):
    if not isinstance(loan_amount, int):
        raise ValueError("loan amount value should be integers only")
    if loan_amount < 0:
        raise ValueError("Loan amount and base loan should not be negative")
    if not isinstance(bank_name, str):
        raise ValueError("bank name value should be str only")
    if product is not None and not isinstance(product, str):
        raise ValueError("Product value should be a string")
    if customer_profile is not None and not isinstance(customer_profile, str):
        raise ValueError("Customer profile value should be a string")

    # bank_multipliers = read_bank_multipliers('/home/sumasoft/Pictures/Multiplier.xlsx')
    bank = bank_name.lower().strip()
    multiplier = bank_multipliers.get(bank)

    # Check if bank exists in multipliers
    if bank not in bank_multipliers:
        multiplier = 1.15  # Default multiplier if bank not found
    else:
        multiplier = bank_multipliers[bank]

    # Calculate preapproved loan based on product and customer_profile
    concatenated_info = product + customer_profile if product is not None and customer_profile is not None else None
    max_loan = 3500000 if concatenated_info == "LAPSENP" else 5000000
    preapproved_loan = min(loan_amount * multiplier, max_loan)

    return preapproved_loan

