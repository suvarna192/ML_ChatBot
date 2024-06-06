"""intent_analysis.ipynb
Author:Rutuja Papade
Date:23-05-2024
Original file is located at
    https://colab.research.google.com/drive/1lLXPUPpVDGyJjXHNg_S-JIs4_U9W_ajp
Used: it converts the word number into integer format
"""



def text2int(textnum, numwords={}):
    if not numwords:
        units = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen"
        ]

        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

        scales = ["hundred", "thousand", "lakh", "lac", "like","crore", "cr", "million", "billion", "trillion"]

        numwords["and"] = (1, 0)
        for idx, word in enumerate(units):
            numwords[word] = (1, idx)
        for idx, word in enumerate(tens):
            numwords[word] = (1, idx * 10)
        for idx, word in enumerate(scales):
            if word == "hundred":
                numwords[word] = (100, 0)
            elif word == "thousand":
                numwords[word] = (1000, 0)
            elif word in ["lakh", "lac", "like"]:
                numwords[word] = (100000, 0)
            elif word in ["crore", "cr"]:
                numwords[word] = (10000000, 0)
            else:
                numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
            pass

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current
