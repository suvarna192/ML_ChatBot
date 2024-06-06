# from running_bot import running_bot

# user_input = input(str("enter the message :"))
# input_id = input(str("enter the unique id :"))

# # response = running_bot(user_input, input_id)
# result = running_bot(user_input, input_id)
# print(result)

from running_bot import running_bot
import json

input_id = input("Enter the unique ID: ")
customer_details = {'balance_transfer': 'balance transfer of 12 lakh', 'topup_offer': 'topup value upto 7 lakhs'}
# customer_details = {
#     "offer":"123456"
# }
customer_details = json.dumps(customer_details)
while True:
    user_input = input("Enter the message: ")
    response, status = running_bot(user_input, input_id,customer_details)
    print("bot: ", response)
    print("status: ", status)

