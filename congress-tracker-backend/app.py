import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from flask import Flask, jsonify, request
import requests
import datetime
import openai
from PyPDF2 import PdfReader
import os
import re
from flask_cors import CORS
import sys
import db_utils

sys.path.append("../")

from SECRET import OPENAI_API_KEY


# cred = credentials.Certificate('billtrack-a2369-72eca0fdbb6d.json')

# app = firebase_admin.initialize_app(cred)

# db = firestore.client()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
OPENAI_API_KEY = 'sk-proj-tBbHRorynUbGV9FtebQhT3BlbkFJVrZzpw6auk20631KEVtn'
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
            for bill in bills:
                title = bill['title']
                introduced_date = bill['introduced_date']
                sponsor = bill['sponsor']['name'] if 'sponsor' in bill else 'Unknown Sponsor'
                
                summary = get_bill_summary(bill)
                if summary == '': 
                    continue

                bill_list.append({
                    'title': title, 
                    'introduced_date': introduced_date, 
                    'summary': summary,
                    'sponsor': sponsor
                })
            return bill_list
        else:
            return []
    else:
        return []

def get_bill_summary(bill):
    text_info = bill.get('text_info', {})
    title = bill.get("title", {})
    title_name = title.split(":")[0]

    if db_utils.document_exists(title_name):
        return db_utils.return_bill_content(bill)
    else:
        db_utils.insert_bill(bill, content="put ChatGPT content here")

    return "not cached"
    
    if not text_info:
        return "No text as of now. \n Bills are generally sent to the Library of Congress from GPO, the Government Publishing Office, a day or two after they are introduced on the floor of the House or Senate. Delays can occur when there are a large number of bills to prepare or when a very large bill has to be printed."

    gpo_pdf_url = text_info.get('gpo_pdf_url', '')
    if not gpo_pdf_url:
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
        # response = openai.chat.completions.create(       
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": f"Summarize the following information: {text}",
        #         }
        #     ],
        #     model="gpt-4",
        # )
        # os.remove(pdf_path)
        # return response.choices[0].message.content
        return "Temp Summary"
    except Exception as e:
        os.remove(pdf_path)
        return f"Failed to summarize text: {str(e)}"

@app.route('/api/bills', methods=['GET'])
def bills():
    summarized_bills = get_bills_introduced_last_year()
    
    # Get the search term query parameter
    search_term = request.args.get('search')
    
    # Filter bills based on the search term
    if search_term:
        regex = re.compile(search_term, re.IGNORECASE)
        summarized_bills = [
            bill for bill in summarized_bills
            if regex.search(bill['title']) or regex.search(bill['summary']) or regex.search(bill['introduced_date'])
        ]

    return jsonify(summarized_bills)

@app.route('/api/person_bills', methods=['GET'])
def person_bills():
    print("received request")
    summarized_bills = get_bills_introduced_last_year()
    
    # Get the search term query parameter
    search_term = request.args.get('search')
    
    # Filter bills based on the sponsor's name
    if search_term:
        regex = re.compile(search_term, re.IGNORECASE)
        summarized_bills = [
            bill for bill in summarized_bills
            if regex.search(bill['sponsor'])
        ]
    
    print("sending info to frontend")
    return jsonify(summarized_bills)

@app.route('/api/summarize_person_bills', methods=['POST'])
def summarize_person_bills():
    data = request.json
    search_term = data.get('search')
    
    summarized_bills = get_bills_introduced_last_year()
    
    if search_term:
        regex = re.compile(search_term, re.IGNORECASE)
        person_bills = [
            bill for bill in summarized_bills
            if regex.search(bill['sponsor'])
        ]

        # Instead of aggregating summaries, return "Hello, World!" for testing
        summary = "Hello, World!"
        
        return jsonify({"summary": summary})
    
    return jsonify({"summary": "No search term provided"}), 400

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    selected_text = data.get('selectedText')
    user_input = data.get('userInput')

    # Handle the incoming data here. For example, you can call OpenAI API
    try:
        response = openai.ChatCompletion.create(       
            messages=[
                {
                    "role": "user",
                    "content": f"The following text is selected: {selected_text}. Please answer this question: {user_input}",
                }
            ],
            model="gpt-4",
        )
        answer = response.choices[0].message.content
        return jsonify({"response": answer})
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
