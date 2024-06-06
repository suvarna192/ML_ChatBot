import subprocess
import sys

# Function to install a package
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install redis package if not already installed
try:
    import redis
except ImportError:
    install('redis')
    import redis

import pandas as pd
import datetime
import time, os, sys
import json
import threading
import mysql.connector
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from triggered_next_question import triggred_questions

# Define function to respond to user input
current_dir = os.getcwd()

# Connect to Redis server
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

def set_cached_data(key, sub_key, value, expiration_time=3600):
    # Serialize the value (dictionary) into a JSON string
    serialized_value = json.dumps(value, default=str)

    # Store the serialized value in Redis cache with a compound key
    redis_key = f"{key}:{sub_key}"
    if expiration_time is not None:
        redis_client.set(redis_key, serialized_value, ex=expiration_time)
    else:
        redis_client.set(redis_key, serialized_value)

def get_cached_data(key):
    # Retrieve all data from Redis cache associated with the given key
    return redis_client.keys(f"{key}:*")

def running_bot(user_input, input_id, customer_details):
    global update_status
    cached_keys = get_cached_data(input_id)
    cached_data = []
    if cached_keys:
        for cached_key in cached_keys:
            cached_value = redis_client.get(cached_key)
            if cached_value is not None:
                cached_dict = json.loads(cached_value.decode())
                if isinstance(cached_dict, dict):
                    cached_data.append(cached_dict)

    # offer id
    customer_details = json.loads(customer_details)
    offer_id = customer_details["balance_transfer"]
    topup_offer = customer_details["topup_offer"]

    if not cached_data:  # If no cached data found
        existing_dataframe = pd.DataFrame(columns=['call_id', 'user_input', 'bot', 'timestamp'])
    else:
        existing_dataframe = pd.DataFrame(cached_data)

    filtered_df = existing_dataframe
    filtered_df = filtered_df.sort_values(by='timestamp', ascending=True)
    topup_triggered = filtered_df['bot'].str.contains('you can get a High Topup of value', case=False).any()

    positive_response = ["okay", "yes", "interested", "interested", "yeah", "sure", "ok", "yup", "yaa",
                         "i will", "definitely", "i have", "go ahead", "of course", "ofcourse", "why not"]
    negative_response = ['quit', 'exit', 'bye', "not interested", "i don't want",
                         "end the call", "thank you", "call me later", "busy", "who are you", "later", "no ",
                         "i dont know", "dont have", "i dont remember", "no."]
    if user_input is None or not user_input.strip():
        previous_question_row = filtered_df.iloc[-1]
        previous_question = previous_question_row['bot']
        chat_hist = previous_question

    else:
        if any(word in user_input.lower() for word in ["rate of interest", "interest rate", "rate interest"]):
            chat_hist = "Rate of interest depends on multiple factors; In case you are interested, based on your " \
                        "eligibility,our authorized sales representative will get in touch with you to discuss the " \
                        "rate of interest."

        elif any(word in user_input.lower() for word in
                 ["Previously I had taken a home loan", "status", "previous loan", "more details", "more information"]):
            chat_hist = "Yes, certainly. Can you please help me with a few details and I can help you better with " \
                        "your Pre-approved Home Loan balance transfer Offer."

        elif any(word in user_input.lower() for word in
                 ["loan applications", "How long it will take for loan applications to get processed", "process",
                  "application"]):
            chat_hist = "Your loan application will get approved within 48 hours post document submission. Our sales " \
                        "representative will get in touch with you shortly to help you with the list of documents."

        elif not topup_triggered and any(word in user_input.lower() for word in
                                         ["hi", "hello", "gm", "good morning", "hey", "good afternoon",
                                          "good evening"]):
            chat_hist = "Since you are a valuable Customer to company, we have a Pre-Approved Home Loan - Balance " \
                        "Transfer offer of " + str(
                offer_id) + ". By availing this Offer, you can get a High Topup of value upto " + str(topup_offer) + \
                        " with maximum savings in EMI. Are you interested in this Offer?"

        elif topup_triggered:
            filtered_df_2 = filtered_df[~filtered_df['bot'].str.contains(
                "Since you are a valuable Customer to company, we have a Pre-Approved Home Loan")]

            if not filtered_df_2.empty:
                previous_question_row_new = filtered_df_2.iloc[-1]
                combined_message = f"{previous_question_row_new['bot']}"
                my_string = f"{combined_message}. {user_input} ."
            else:
                my_string = user_input

            combined_message = f"{filtered_df['bot'], filtered_df['user_input']}"
            my_string_2 = f"{combined_message}. {user_input} ."
            my_string_lower = my_string_2.lower()
            word_counts = {word: my_string_lower.count(word) for word in positive_response}
            count = sum(word_counts.values())
            if count >= 1:
                chat_hist = triggred_questions(my_string, filtered_df, input_id)
            else:
                if any(word in user_input.lower() for word in negative_response):
                    chat_hist = "Thank you for your valuable time. You will hear from our sales manager shortly. Have a nice " \
                                "day ahead."
                else:
                    previous_question_row = filtered_df.iloc[-1]
                    previous_question = previous_question_row['bot']
                    chat_hist = previous_question

        elif any(word in user_input.lower() for word in negative_response):
            chat_hist = "Thank you for your valuable time. You will hear from our sales manager shortly. Have a nice " \
                        "day ahead."

        else:
            chat_hist = "We appreciate your patience. Can you please repeat?"

    timestamp = datetime.datetime.now()
    update_status = True
    if not filtered_df.empty:
        previous_question_row = filtered_df.iloc[-1]
        previous_question = previous_question_row['bot']
        if chat_hist == previous_question:
            update_status = False
        else:
            update_status = True

    new_entry = {
        "call_id": input_id,
        "bot": chat_hist,
        "user_input": user_input + ". ",
        "timestamp": timestamp,
        "status": update_status
    }
    set_cached_data(input_id, timestamp, new_entry)
    return chat_hist, update_status
