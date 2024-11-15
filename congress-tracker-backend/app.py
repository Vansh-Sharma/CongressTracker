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

# Initialize Firebase with credentials if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate('billtrack-a2369-72eca0fdbb6d.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set OpenAI API key
OPENAI_API_KEY = "sk-proj-tBbHRorynUbGV9FtebQhT3BlbkFJVrZzpw6auk20631KEVtn"
openai.api_key = OPENAI_API_KEY

def get_bills_introduced_last_year():
    today = datetime.datetime.now()
    last = today - datetime.timedelta(days=30)
    today_str = today.strftime('%Y-%m-%d')
    last_str = last.strftime('%Y-%m-%d')
    
    url = f"https://www.govtrack.us/api/v2/bill?congress=118&introduced_date__gte={last_str}&introduced_date__lte={today_str}&sort=-introduced_date"
    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        data = response.json()
        bills = data.get('objects', [])
        bill_list = []
        if bills:
            for bill in bills:
                print("reading bills")
                title = bill['title']
                introduced_date = bill['introduced_date']
                sponsor = bill['sponsor']['name'] if 'sponsor' in bill else 'Unknown Sponsor'
                
                summary, pdf_text = get_bill_summary(bill)
                if summary == '': 
                    continue
                
                bill_list.append({
                    'title': title, 
                    'introduced_date': introduced_date, 
                    'summary': summary,
                    'sponsor': sponsor,
                    'pdf_text': pdf_text
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
        if not text_info:
            return "", ""

        gpo_pdf_url = text_info.get('gpo_pdf_url', '')
        if not gpo_pdf_url:
            return "", ""    
        print("Summarizing")
        summary, pdf_text = summarize_text(gpo_pdf_url)
        db_utils.insert_bill(bill, original=summary, translated=pdf_text)
        return summary, pdf_text

def summarize_text(gpo_pdf_url):
    response = requests.get(gpo_pdf_url)
    
    pdf_path = "bill.pdf"
    with open(pdf_path, "wb") as file:
        file.write(response.content)
    
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    
    os.remove(pdf_path)  # Remove the PDF file after extraction

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following information: {text}",
                }
            ],
        )
        full_text_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": f"Please format this text better, getting rid of any random characters: {text}",
                }
            ],
        )
        return response.choices[0].message.content, full_text_response.choices[0].message.content
    except Exception as e:
        return f"Failed to summarize text: {str(e)}", text

@app.route('/api/bills', methods=['GET'])
def bills():
    summarized_bills = get_bills_introduced_last_year()
    
    search_term = request.args.get('search')
    
    if search_term:
        regex = re.compile(search_term, re.IGNORECASE)
        summarized_bills = [
            bill for bill in summarized_bills
            if regex.search(bill['title']) or regex.search(bill['summary']) or regex.search(bill['introduced_date'])
        ]
    
    return jsonify(summarized_bills)

@app.route('/api/person_bills', methods=['GET'])
def person_bills():
    summarized_bills = get_bills_introduced_last_year()
    
    search_term = request.args.get('search')
    
    if search_term:
        regex = re.compile(search_term, re.IGNORECASE)
        summarized_bills = [
            bill for bill in summarized_bills
            if regex.search(bill['sponsor'])
        ]
    
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

        # Aggregate summaries of the person's bills
        summaries = [bill['summary'] for bill in person_bills if bill['summary']]
        combined_summary = "\n\n".join(summaries)
        
        # Call OpenAI API to summarize the combined summaries
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize the following information: {combined_summary}",
                    }
                ],
            )
            summary = response.choices[0].message.content
        except Exception as e:
            summary = f"Failed to summarize text: {str(e)}"
        
        return jsonify({"summary": summary})
    
    return jsonify({"summary": "No search term provided"}), 400

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    selected_text = data.get('selectedText')
    user_input = data.get('userInput')

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": f"The following text is selected: {selected_text}. Please answer this question: {user_input}",
                }
            ],
        )
        answer = response.choices[0].message.content
        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
