def convert_to_indian_rupees(number):
    # Indian numbering system
    indian_number_system = {
        0: 'Zero',
        1: 'One',
        2: 'Two',
        3: 'Three',
        4: 'Four',
        5: 'Five',
        6: 'Six',
        7: 'Seven',
        8: 'Eight',
        9: 'Nine',
        10: 'Ten',
        11: 'Eleven',
        12: 'Twelve',
        13: 'Thirteen',
        14: 'Fourteen',
        15: 'Fifteen',
        16: 'Sixteen',
        17: 'Seventeen',
        18: 'Eighteen',
        19: 'Nineteen',
        20: 'Twenty',
        30: 'Thirty',
        40: 'Forty',
        50: 'Fifty',
        60: 'Sixty',
        70: 'Seventy',
        80: 'Eighty',
        90: 'Ninety'
    }

    if number < 20:
        return indian_number_system[number]

    result = ''

    if number >= 10000000:
        crores = number // 10000000
        if crores > 0:
            result += convert_to_indian_rupees(crores) + ' Crore '
        number %= 10000000

    if number >= 100000:
        lakhs = number // 100000
        if lakhs > 0:
            result += convert_to_indian_rupees(lakhs) + ' Lakh '
        number %= 100000

    if number >= 1000:
        thousands = number // 1000
        if thousands > 0:
            result += convert_to_indian_rupees(thousands) + ' Thousand '
        number %= 1000

    if number >= 100:
        hundreds = number // 100
        if hundreds > 0:
            result += convert_to_indian_rupees(hundreds) + ' Hundred '
        number %= 100

    if number > 0:
        if result != '':
            result += 'and '
        if number < 20:
            result += indian_number_system[number]
        else:
            result += indian_number_system[number // 10 * 10] + ' ' + indian_number_system[number % 10]

    return result.strip().replace(" Zero", "")
