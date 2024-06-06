"""triggered_next_question.ipynb
Author:Rutuja Papade
Date:21-02-2024
Original file is located at
    https://colab.research.google.com/drive/1lLXPUPpVDGyJjXHNg_S-JIs4_U9W_ajp
Used: triggered_next_question
"""

import os
import sys
import json
import threading
import mysql.connector
import logging

os.environ["TOKENIZERS_PARALLELISM"] = "false"

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from intent_analysis import question_ans_analysis
from num_word import convert_to_indian_rupees
from emi_calculation.voice_calculation import calculate_preapproved_loan

# Database credentials and connection
db_config = {
    # "host": "192.168.100.37",
    "host": "localhost",
    "user": "dbusr",
    "password": "Cdr@2023!@#",
    "database": "bani_final"
}


def save_to_database(data):
    # Connect to the database
    mydb = mysql.connector.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"]
    )

    mycursor = mydb.cursor()
    # Extract necessary information
    call_id_value = data.get("input_id", None)
    existing_home_loan_value = data.get("existing_home_loan", "")
    bank_name_token_value = data.get("bank_name_token", "")
    more_details_token_value = data.get("more_details_token", "")
    sanction_amt_token_value = data.get("sanction_amt_token", "")
    sanction_date_token_value = data.get("sanction_date_token", "")
    emi_amt_token_value = data.get("emi_amt_token", "")
    outstanding_amt_token_value = data.get("outstanding_amt_token", "")
    designation_token_value = data.get("designation_token", "")
    dob_token_value = data.get("dob_token", "")
    appointment_details_value = data.get("appointment_details", "")

    # SQL query to insert data
    sql = "INSERT INTO chatbot_data(call_id, existing_home_loan, bank_name_token, more_details_token, sanction_amt_token, sanction_date_token, emi_amt_token, outstanding_amt_token, designation_token, dob_token, appointment_details, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s ,CURRENT_TIMESTAMP())"
    val = (
        call_id_value, existing_home_loan_value, bank_name_token_value, more_details_token_value,
        sanction_amt_token_value,sanction_date_token_value,
        emi_amt_token_value, outstanding_amt_token_value, designation_token_value, dob_token_value, appointment_details_value)

    mycursor.execute(sql, val)

    mydb.commit()  # Commit the transaction

    mydb.close()  # Close the database connection


def save_history(data, input_id):
    data_json = data.to_json(orient='records', lines=True)
    # Connect to the database
    mydb = mysql.connector.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"]
    )

    mycursor = mydb.cursor()

    # SQL query to insert data
    sql = "INSERT INTO chatbot_con(call_id, data, created_at) VALUES (%s, %s, CURRENT_TIMESTAMP())"
    val = (input_id, data_json)

    mycursor.execute(sql, val)

    mydb.commit()  # Commit the transaction
    # logging.info(f"Record inserted, ID: {mycursor.lastrowid}")

    mydb.close()  # Close the database connection


def database_save_thread(data):
    # Function to run in the thread for database save operation
    save_to_database(data)


def dump_data_in_db(result,filtered_df, input_id):
    data = json.dumps(result, default=str)
    data_dict = json.loads(data)
    # Start a thread to save the data to the database
    thread = threading.Thread(target=save_to_database, args=(data_dict,))
    thread_1 = threading.Thread(target=save_history, args=(filtered_df, input_id))
    thread.daemon = True
    thread_1.daemon = True
    thread.start()
    thread_1.start()


def triggred_questions(input_data, filtered_df, input_id):

    result = question_ans_analysis(input_data, input_id)

    positive_response = ["okay", "yes", "interested", "yeah", "sure", "ok", "yup", "yaa", "i will", "definitely",
                         "i have", "go ahead", "of course", "ofcourse"]
    if any(word in input_data.lower() for word in
           ['quit', 'exit', 'bye', "not interested", "i don't want", "cut the call",
            "end the call", "call me later", "busy", "who are you"]):
        response = "Thank you for your valuable time. You will hear from our sales manager shortly. Have a nice day " \
                   "ahead."

        dump_data_in_db(result, filtered_df, input_id)


    else:
        result = question_ans_analysis(input_data, input_id)
        if result['existing_home_loan'] is None:
            response = "Do you have any existing home loan?"

        elif result['existing_home_loan'] == "negative":
            response = "Thank you for your valuable time. You will hear from our sales manager shortly. Have a nice " \
                       "day ahead."
            dump_data_in_db(result, filtered_df, input_id)

        elif result['more_details_token'] == "negative":
            response = "Thank you for your valuable time. You will hear from our sales manager shortly. Have a nice " \
                       "day ahead."
            dump_data_in_db(result, filtered_df, input_id)

        elif result['bank_name_token'] is None:
            response = "Can you please tell me from which bank you have taken the home loan?"



        elif result['more_details_token'] is None:
            response = "Sir, can you please help me with a few more details for sharing the exact offer details?"


        elif result['sanction_amt_token'] is None:
            response = "What is your home loan sanction amount?"

        elif result['sanction_date_token'] is None:

            response = "In which year did you take a loan?"


        elif result['emi_amt_token'] is None:
            response = "What is the EMI that you are paying?"


        elif result['outstanding_amt_token'] is None:
            response = "What is your outstanding amount?"


        elif result['designation_token'] is None:
            response = "Are you salaried or self employed?"


        elif result['dob_token'] is None:
            response = "What is your Date of Birth?"


        # elif result['obligation_token'] is None:
        #     response = "Do you have any Other Obligation like Personal loan or car loan?"
        #     status = True

        elif result['appointment_details'] is None:
            bank_name_token_value = result['bank_name_token']
            sanction_amt_token_value = result['sanction_amt_token']
            if sanction_amt_token_value and all(isinstance(val, int) for val in sanction_amt_token_value):
                max_sanction_amt = max(sanction_amt_token_value)
            else:
                max_sanction_amt = 0
            # sanction_amt_integers = [int(value) for value in sanction_amt_token_value]
            # max_sanction_amt = max(sanction_amt_integers)
            preapproved_value = calculate_preapproved_loan(int(max_sanction_amt), bank_name_token_value)
            converted_value = convert_to_indian_rupees(int(preapproved_value))

            response = "Thank you Sir for your input, can you give me few minutes so that I can come up with and offer " \
                       "for you? You are qualifying for a Preapproved Home Loan Balance Transfer offer of " + str(
                converted_value) + ". Please let us know of a " \
                                   "suitable day and time for scheduling your appointment with our sales manager"


        else:
            response = "Thank you for your valuable time. You will hear from our sales manager shortly. Have a nice " \
                       "day ahead."

            dump_data_in_db(result, filtered_df, input_id)

    return response
