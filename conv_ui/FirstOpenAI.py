import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set - please head to the troubleshooting guide in the setup folder")

openai = OpenAI()

def myfunc(message):



    prompt = f"\
    Given the user request below, classify it as either being about `Book Flight`,\
    `Greeting`, or `Farewell` or `Others`\
    If the user request to book or reserve a flight then classify it as `Book Flight`.\
    If the user greets you then classify it as `Greeting`.\
    If the user leaves the chat and says good bye then classify it as `Farewell`.\
    If the user request looks out of the context then classify it as `Other`.\n\
    The databse has following tables:\
    create table tiket_reservation (\
        PNR_Number VARCHAR(10),\
        Customer_Name VARCHAR(50),\
        Flight_ID VARCHAR(50),\
        Airline VARCHAR(50),\
        From_City VARCHAR(50),\
        To_City VARCHAR(50),\
        Departure_Time DATE,\
        Arrival_Time DATE,\
        Travel_Date DATE,\
        Booking_Date DATE,\
        Booking_Status VARCHAR(20),\
        Refund_Status VARCHAR(20)\
    );\
    Do not respond with more than two words.\n\
    Request: {message}\
    Classification:\n\
    "
   
    messages = [{"role": "user", "content":prompt}]

    print(messages)
    response = openai.chat.completions.create(
        model = "gpt-4.1-mini",
        messages=messages
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    myfunc()
