# from flask import Flask, jsonify, request
# import requests
# import datetime
# import openai

# app = Flask(__name__)

# # Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
# OPENAI_API_KEY = 'sk-proj-tBbHRorynUbGV9FtebQhT3BlbkFJVrZzpw6auk20631KEVtn'
# openai.api_key = OPENAI_API_KEY

# def get_bills_introduced_last_year():
#     today = datetime.datetime.now()
#     last = today - datetime.timedelta(days=7)
#     today_str = today.strftime('%Y-%m-%d')
#     last_str = last.strftime('%Y-%m-%d')

#     url = f"https://www.govtrack.us/api/v2/bill?congress=118&introduced_date__gte={last_str}&introduced_date__lte={today_str}&sort=-introduced_date"
#     response = requests.get(url)

#     if response.status_code == 200:
#         data = response.json()
#         bills = data.get('objects', [])
#         summarized_bills = []
#         for bill in bills:
#             summary = get_bill_summary(bill)
#             summarized_bills.append({
#                 'title': bill['title'],
#                 'introduced_date': bill['introduced_date'],
#                 'summary': summary
#             })
#         print("done reading bills")
#         return summarized_bills
#     else:
#         return []

# def get_bill_summary(bill):
#     text_info = bill.get('text_info', {})
#     if not text_info:
#         print("No text available")
#         return "No text available for this bill."

#     gpo_pdf_url = text_info.get('gpo_pdf_url', '')
#     if not gpo_pdf_url:
#         print("No Bill")
#         return "No bill text URL available."

#     summary = summarize_text(gpo_pdf_url)
#     return summary

# def summarize_text(url):
#     try:
#         response = openai.chat.completions.create(       
#             messages=[
#                 {
#                     "role": "user",
#                     "content": f"Summarize the following information: {url}",
#                 }
#             ],
#             model="gpt-4",
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         return f"Failed to summarize text: {str(e)}"

# @app.route('/api/bills', methods=['GET'])
# def bills():
#     print("recieved get")
#     summarized_bills = get_bills_introduced_last_year()
#     print("sending info to frontend")
#     return jsonify(summarized_bills)

# if __name__ == '__main__':
#     #app.run(debug=True)
#     print(get_bills_introduced_last_year())


#------------------------------------------------------------------------------------------------------------------------------------------------------

# from flask import Flask, jsonify, request
# import requests
# import datetime
# import openai
# from PyPDF2 import PdfReader
# import os

# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# # Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
# OPENAI_API_KEY = 'sk-proj-tBbHRorynUbGV9FtebQhT3BlbkFJVrZzpw6auk20631KEVtn'
# openai.api_key = OPENAI_API_KEY

# def get_bills_introduced_last_year():
#     # Calculate the date range for the last year
#     today = datetime.datetime.now()
#     last = today - datetime.timedelta(days=7)
#     today_str = today.strftime('%Y-%m-%d')
#     last_str = last.strftime('%Y-%m-%d')
    
#     # Construct the API endpoint
#     url = f"https://www.govtrack.us/api/v2/bill?congress=118&introduced_date__gte={last_str}&introduced_date__lte={today_str}&sort=-introduced_date"
    
#     # Make the request
#     response = requests.get(url)
    
#     # Check if the request was successful
#     if response.status_code == 200:
#         data = response.json()
#         bills = data.get('objects', [])
        
#         # Print the bills introduced in the last year
#         bill_list = []
#         if bills:
#             print(f"Bills introduced from {last_str} to {today_str}:")
#             for bill in bills:
#                 title = bill['title']
#                 introduced_date = bill['introduced_date']
#                 # Print bill details
#                 print(f"Title: {title}")
#                 print(f"Introduced Date: {introduced_date}")
                
#                 # Get the full text of the bill and summarize it
#                 summary = get_bill_summary(bill)
#                 print(f"Summary: {summary}")
#                 print('-' * 40)
#                 bill_list.append(
#                     {
#                         'title': title, 
#                         'introduced_date': introduced_date, 
#                         'summary': summary,
#                     }
#                 )
#             return bill_list
#         else:
#             print(f"No bills introduced from {last_str} to {today_str}.")
#             return []
#     else:
#         print(f"Failed to retrieve data: {response.status_code}")
#         return []

# def get_bill_summary(bill):
#     text_info = bill.get('text_info', {})
#     if not text_info:
#         print("no text available")
#         reason = "No text as of now. \n Bills are generally sent to the Library of Congress from GPO, the Government Publishing Office, a day or two after they are introduced on the floor of the House or Senate. Delays can occur when there are a large number of bills to prepare or when a very large bill has to be printed."
#         return reason

#     gpo_pdf_url = text_info.get('gpo_pdf_url', '')
#     if not gpo_pdf_url:
#         print("No bill available")
#         return "No bill text URL available."

#     # Use OpenAI to summarize the bill
#     summary = summarize_text(gpo_pdf_url)
#     return summary

# def summarize_text(gpo_pdf_url):

#     response = requests.get(gpo_pdf_url)
    
#     # Save the PDF locally
#     pdf_path = "bill.pdf"
#     with open(pdf_path, "wb") as file:
#         file.write(response.content)
    
#     # Read the PDF
#     reader = PdfReader(pdf_path)
#     text = ""
#     for page in reader.pages:
#         text += page.extract_text()
    
#     print("Bill Text:", text)

#     try:
#         response = openai.chat.completions.create(       
#             messages=[
#                 {
#                     "role": "user",
#                     "content": f"Summarize the following information: {text}",
#                 }
#             ],
#             model="gpt-4",
#         )
#         os.remove(pdf_path)
#         return response.choices[0].message.content
#     except Exception as e:
#         os.remove(pdf_path)
#         return f"Failed to summarize text: {str(e)}"

# @app.route('/api/bills', methods=['GET'])
# def bills():
#     print("received request")
#     summarized_bills = get_bills_introduced_last_year()
#     print("sending info to frontend")
#     return jsonify(summarized_bills)

# if __name__ == '__main__':
#     app.run(debug=True)
#     #print(get_bills_introduced_last_year())
import sys

sys.path.append('../')


from flask import Flask, jsonify, request
import requests
import datetime
import openai
from PyPDF2 import PdfReader
import os
from flask_cors import CORS

from SECRET import OPENAI_API_KEY

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
openai.api_key = OPENAI_API_KEY

def get_bills_introduced_last_year():
    today = datetime.datetime.now()
    last = today - datetime.timedelta(days=7)
    today_str = today.strftime('%Y-%m-%d')
    last_str = last.strftime('%Y-%m-%d')
    
    url = f"https://www.govtrack.us/api/v2/bill?congress=118&introduced_date__gte={last_str}&introduced_date__lte={today_str}&sort=-introduced_date"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        bills = data.get('objects', [])
        
        bill_list = []
        if bills:
            print(f"Bills introduced from {last_str} to {today_str}:")
            for bill in bills:
                title = bill['title']
                introduced_date = bill['introduced_date']
                print(f"Title: {title}")
                print(f"Introduced Date: {introduced_date}")
                
                summary = get_bill_summary(bill)
                print(f"Summary: {summary}")
                print('-' * 40)
                bill_list.append({
                    'title': title, 
                    'introduced_date': introduced_date, 
                    'summary': summary,
                })
            return bill_list
        else:
            print(f"No bills introduced from {last_str} to {today_str}.")
            return []
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return []

def get_bill_summary(bill):
    text_info = bill.get('text_info', {})
    if not text_info:
        print("no text available")
        return "No text as of now. \n Bills are generally sent to the Library of Congress from GPO, the Government Publishing Office, a day or two after they are introduced on the floor of the House or Senate. Delays can occur when there are a large number of bills to prepare or when a very large bill has to be printed."

    gpo_pdf_url = text_info.get('gpo_pdf_url', '')
    if not gpo_pdf_url:
        print("No bill available")
        return "No bill text URL available."

    summary = summarize_text(gpo_pdf_url)
    return summary

def summarize_text(gpo_pdf_url):
    response = requests.get(gpo_pdf_url)
    
    pdf_path = "bill.pdf"
    with open(pdf_path, "wb") as file:
        file.write(response.content)
    
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    
    print("Bill Text:", text)

    try:
        response = openai.chat.completions.create(       
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following information: {text}",
                }
            ],
            model="gpt-4",
        )
        os.remove(pdf_path)
        return response.choices[0].message.content
    except Exception as e:
        os.remove(pdf_path)
        return f"Failed to summarize text: {str(e)}"

@app.route('/api/bills', methods=['GET'])
def bills():
    print("received request")
    summarized_bills = get_bills_introduced_last_year()
    print("sending info to frontend")
    return jsonify(summarized_bills)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
