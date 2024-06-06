

import re, ast
import os, sys, json

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from span_marker import SpanMarkerModel
from nltk.tokenize import sent_tokenize, word_tokenize
from spacy.lang.en import English
from number_conversion import convert_to_numeric
from word_num_to_integer import text2int
import redis, threading
import datetime
import spacy

ner = spacy.load("en_core_web_trf")

model = SpanMarkerModel.from_pretrained("tomaarsen/span-marker-bert-base-uncased-cross-ner")
nlp = English()

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=1)


def set_cached_data(key, sub_key, value, expiration_time=3600):
    serialized_value = json.dumps(value, default=str)
    redis_key = f"{key}:{sub_key}"
    if expiration_time is not None:
        redis_client.set(redis_key, serialized_value, ex=expiration_time)
    else:
        redis_client.set(redis_key, serialized_value)


def get_cached_data(key):
    # Retrieve all data from Redis cache associated with the given key
    return redis_client.keys(f"{key}:*")


def question_ans_analysis(ques_ans_string, input_id):

    def find_type(list_words, text_data):
        combined_result = []
        text_data_lower = text_data.lower()
        for target_phrase in list_words:
            target_phrase_lower = target_phrase.lower()
            if target_phrase_lower in text_data_lower:
                # Tokenize the text data and the target phrase
                text_tokens = word_tokenize(text_data_lower)
                phrase_tokens = word_tokenize(target_phrase_lower)

                # Find the position of the target phrase in the tokenized text
                for i in range(len(text_tokens) - len(phrase_tokens) + 1):
                    if text_tokens[i:i + len(phrase_tokens)] == phrase_tokens:
                        # Get the next 8 words after the target phrase

                        next_words = text_tokens[i + len(phrase_tokens):i + len(phrase_tokens) + 8]
                        final_words = phrase_tokens + next_words
                        combined_result.append(" ".join(final_words))

        # Combine the results into a single string
        combined_result_join = " ".join(combined_result)
        return combined_result_join

    negative_response = ["not interested", "no", "dont", "dont have", "don't", "i dont remember"]

    def negative_word(user_input):
        # global found_negative_words
        found_negative_words = None
        for word in negative_response:
            if word.lower() in user_input.lower():
                found_negative_words = word
                break
        return found_negative_words

    def find_bank_name(input_bank_name_sentence):
        if input_bank_name_sentence:
            entities = model.predict(str(input_bank_name_sentence.title()))
            bank_name_list = []
            for entity in entities:
                if entity['label'] == "organisation":
                    bank_name = entity['span']
                    if bank_name.lower() not in ["emi","thank you"]:
                        bank_name_list.append(bank_name)

            if not bank_name_list:
                negative_words = negative_word(input_bank_name_sentence)
            else:
                negative_words = bank_name_list[0]

            return negative_words if negative_words else None

    def find_number(input_sentence):
        if input_sentence:
            fetch_number = re.findall(r'\d+', input_sentence)

            if fetch_number:  # Check if fetch_numbers is not empty
                number_pattern = r"\d{1,9}(?:,\d{9})*(?:\.\d+)?\s*(?:crores|crore|cr)?(?:\s+\d{1,9}(?:,\d{9})*)?\s*(?:lakhs|lakh|like)?(?:\s+\d{1,9}(?:,\d{9})*)?"

                text = input_sentence.replace(',', '')
                fetch_numbers = re.findall(number_pattern, text, re.IGNORECASE)
                numbers_list = set()
                for num in fetch_numbers:
                    word_int = convert_to_numeric(num)
                    numbers_list.add(int(word_int))

                numbers_list = sorted(numbers_list)
                return {numbers_list[-1]} if numbers_list else None

            words_num_format = r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|lakh|lac|like|crore|cr|trillion)(?:[-\s]?(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|lakh|lac|like|crore|cr|trillion))*\b'
            modified_text = input_sentence.replace("-", " ")
            word_matches = re.findall(words_num_format, modified_text, re.IGNORECASE)
            if word_matches:
                word_numbers_list = set()
                for num in set(word_matches):
                    word_int = text2int(num)
                    word_numbers_list.add(word_int)

                    return word_numbers_list

            else:
                negative_words = negative_word(input_sentence)
                return {negative_words} if negative_words else None

        else:
            return None

    def find_number(input_sentence):
        if input_sentence:
            fetch_number = re.findall(r'\d+', input_sentence)

            if fetch_number:  # Check if fetch_numbers is not empty
                number_pattern = r"\d{1,9}(?:,\d{9})*(?:\.\d+)?\s*(?:crores|crore|cr)?(?:\s+\d{1,9}(?:,\d{9})*)?\s*(?:lakhs|lakh|like)?(?:\s+\d{1,9}(?:,\d{9})*)?"

                text = input_sentence.replace(',', '')
                fetch_numbers = re.findall(number_pattern, text, re.IGNORECASE)
                numbers_list = []
                for num in fetch_numbers:
                    word_int = convert_to_numeric(num)
                    numbers_list.append(int(word_int))

                numbers_list = sorted(numbers_list)
                return {numbers_list[-1]} if numbers_list else None

            words_num_format = r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|lakh|lac|like|crore|cr|trillion)(?:[-\s]?(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|lakh|lac|like|crore|cr|trillion))*\b'
            modified_text = input_sentence.replace("-", " ")
            word_matches = re.findall(words_num_format, modified_text, re.IGNORECASE)
            if word_matches:
                word_numbers_list = set()
                for num in set(word_matches):
                    word_int = text2int(num)
                    word_numbers_list.add(word_int)

                    return word_numbers_list

            else:
                negative_words = negative_word(input_sentence)
                return {negative_words} if negative_words else None
        else:
            return None

    def obiligation_token(input_sentence):
        if input_sentence:
            # Phrases indicating responses or obligations
            yes_no_phrases = [
                "yes",
                "ok",
                "okay",
                "I have",
                "don't",
                "do not",
                "dont",
                "yup",
                'yeah',
                'yaa',
                "self-employed",
                "self employed",
                "business",
                "salary",
                "salaried",
                "employee"
            ]
            input_sentence = re.sub(r'[^\w\s]', ' ', input_sentence)
            yes_no_pattern = "|".join(yes_no_phrases)
            matches = re.findall(yes_no_pattern, input_sentence, re.IGNORECASE)
            if not matches:
                negative_words = negative_word(input_sentence)
                if not negative_words:
                    number_matches = find_number(input_sentence)
                    return number_matches if number_matches else None
                else:
                    return set(negative_words) if negative_words else None
            else:
                return set(matches) if matches else None

    def yes_okay(input_sentence):
        if input_sentence:
            yes_ok_phrase = [
                r"yes",
                r"okay",
                r"I have",
                r"yeah",
                r"yup",
                r'yaa',
                r'sure',
                r"ok",
                r"definitely",
                r'i will',
                r'of course',
                r'ofcourse',
                r'go ahead',
                r'took loan',
                r'loan with'
            ]
            input_sentence = re.sub(r'[^\w\s]', ' ', input_sentence)
            yes_ok_pattern = "|".join(yes_ok_phrase)
            yes_ok_matches = re.findall(yes_ok_pattern, input_sentence, re.IGNORECASE)
            if not yes_ok_matches:
                negative_words = negative_word(input_sentence)
                return "negative" if negative_words else None
            else:
                return set(yes_ok_matches) if yes_ok_matches else None

    def detect_days_time(input_sentence):
        if input_sentence:
            days_pattern = r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|tomorrow|day after tomorrow|morning|afternoon|evening|night)\b'
            time_pattern = r'\b(?:[0-9]|0[0-9]|1[0-2])(?::[0-5][0-9])?\s*(?:am|pm|a\.m\.|p\.m\.|a.m.|p.m.)\b'
            days_matches = re.findall(days_pattern, input_sentence, flags=re.IGNORECASE)

            # Remove special characters using the pattern
            cleaned_sentence = re.sub(r'[^a-zA-Z0-9\s]', '', input_sentence)
            time_matches = re.findall(time_pattern, cleaned_sentence, flags=re.IGNORECASE)
            result_day_time = days_matches + time_matches

            result = ", ".join(set(result_day_time))

            if result_day_time is None:
                negative_words = negative_word(input_sentence)
                return negative_words if negative_words else None
            else:
                return result if result else None

    def detect_date_year(text_data):
        doc = ner(text_data)
        result_date = []
        for ent in doc.ents:
            if ent.label_ == "DATE":
                date_year = ent.text
                result_date.append(date_year)
        return result_date[0] if result_date else None

    # existing home loan
    list_words = ["existing home loan"]
    existing_home_loan_sentence = find_type(list_words, ques_ans_string)
    existing_home_loan_token = yes_okay(existing_home_loan_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"existing_home_loan": existing_home_loan_token})

    # bank name
    list_words = ["which bank", "bank name", "loan from", "loan in", "taken", "existing home loan",
                  "Can you please repeat?","loan with"]
    bank_name_sentence = find_type(list_words, ques_ans_string)
    bank_name_token = find_bank_name(bank_name_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"bank_name_token": bank_name_token})

    # interested in more details## no
    list_words = ["can you please help me with a few more details for sharing the exact offer details?"]
    more_details_sentence = find_type(list_words, ques_ans_string)
    more_details_token = yes_okay(more_details_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"more_details_token": more_details_token})

    # sanction amount
    list_words = ["sanction", "home loan of", "loan of", "loan was", "sanctioned for"]
    sanction_amt_sentence = find_type(list_words, ques_ans_string)
    sanction_amt_token = find_number(sanction_amt_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"sanction_amt_token": sanction_amt_token})

    # sanction date
    list_words = ["which year did you take a loan", "took loan","sanction", "home loan of", "loan of", "loan was", "took a loan","sanctioned","loan from"]
    sanction_date_sentence = find_type(list_words, ques_ans_string)
    sanction_date_token = detect_date_year(sanction_date_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"sanction_date_token": sanction_date_token})

    # emi amount
    list_words = ["emi", "installment"]
    emi_amt_sentence = find_type(list_words, ques_ans_string)
    emi_amt_token = find_number(emi_amt_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"emi_amt_token": emi_amt_token})

    # outstanding amount
    list_words = [ "remaining", "left", "outstanding"]
    outstanding_amt_sentence = find_type(list_words, ques_ans_string)
    outstanding_amt_token = find_number(outstanding_amt_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"outstanding_amt_token": outstanding_amt_token})

    # designation
    list_words = ["salaried", "self employed", "salary", "business"]
    ques_ans_string = re.sub(r'[^\w\s]', ' ', ques_ans_string)
    designation_sentence = find_type(list_words, ques_ans_string)
    designation_token = obiligation_token(designation_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"designation_token": designation_token})

    # date of birth
    list_words = ["date of birth","age","I am","i was","old"]
    dob_sentence = find_type(list_words, ques_ans_string)
    dob_token = detect_date_year(dob_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"dob_token": dob_token})


    # appointment details
    list_words = ["appointment", "Can you please repeat?"]
    app_details_sentence = find_type(list_words, ques_ans_string)
    app_details_token = detect_days_time(app_details_sentence)
    set_cached_data(input_id, datetime.datetime.now(), {"appointment_details": app_details_token})

    cached_keys = get_cached_data(input_id)
    cached_data = {}
    if cached_keys:
        for cached_key in cached_keys:
            cached_value_new = redis_client.get(cached_key)
            if cached_value_new is not None:
                cached_dict = json.loads(cached_value_new.decode())
                for key, value in cached_dict.items():
                    if value is not None:  # Skip None values
                        if key not in cached_data:
                            cached_data[key] = []
                        cached_data[key].append(value)

    data_1 = {
        "input_id": str(input_id),
        "existing_home_loan": None,
        "bank_name_token": None,
        "more_details_token": None,
        "sanction_amt_token": None,
        "sanction_date_token": None,
        "emi_amt_token": None,
        "outstanding_amt_token": None,
        "designation_token": None,
        "dob_token": None,
        "appointment_details": None
    }

    for key, value in cached_data.items():
        if value is not None:  # Skip None values
            if isinstance(value[0], list):  # Check if value is a list of lists
                # Flatten the list of lists
                flattened_value = [item for sublist in value for item in sublist]
                data_1[key] = ast.literal_eval(flattened_value[0]) if flattened_value else None
            elif isinstance(value[0], str) and value[0].startswith('{') and value[0].endswith('}'):
                # Handle cases like '{3456789}' for numeric values
                data_1[key] = ast.literal_eval(value[0])
            else:
                # Extract string from the list
                data_1[key] = value[0] if isinstance(value[0], str) else None
        else:
            data_1[key] = None

    return data_1
