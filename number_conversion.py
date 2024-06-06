"""number_conversion.ipynb
Author:Rutuja Papade
Date:20-03-2024
Original file is located at
    https://colab.research.google.com/drive/1lLXPUPpVDGyJjXHNg_S-JIs4_U9W_ajp
Used: convert the string format of number into integer
"""

import re


def convert_to_numeric(number_str):

    def lakh_word_to_num(text):
        if not text.strip():
            return 0

        text = text.replace(' ', '')
        pattern = r"(\d+)\s*lakh*(\d+)*"
        match = re.match(pattern, text, re.IGNORECASE)

        if match:
            lakh_part = int(match.group(1)) * 100000
            if match.group(2):
                thousand_part = int(match.group(2))  # Thousand part remains the same
                lakh = lakh_part + thousand_part
                return lakh

            return lakh_part

        else:
            return text

    number_str = number_str.replace(',', '').replace('like', 'lakh').replace('lakhs', 'lakh').replace("crores", "crore")

    if "crore" in number_str:
        split_text = number_str.split("crore")
        lakh_cal = lakh_word_to_num(split_text[1])

        crore_matches = re.findall(r'\d+', split_text[0])
        crore_num = int(crore_matches[0]) * 10000000
        total = crore_num + int(lakh_cal)

    else:
        total = lakh_word_to_num(number_str)

    return total


