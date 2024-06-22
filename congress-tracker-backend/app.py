from flask import Flask, jsonify, request
import requests
import datetime
import openai
from PyPDF2 import PdfReader
import os
import re
from flask_cors import CORS
import sys

sys.path.append("../")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
OPENAI_API_KEY="sk-proj-tBbHRorynUbGV9FtebQhT3BlbkFJVrZzpw6auk20631KEVtn"
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
        print("trust",  bills[0].keys())
        if bills:
            for bill in bills:
                title = bill['title']
                introduced_date = bill['introduced_date']
                
                summary = get_bill_summary(bill)
                print(f"Summary: {summary}")
                if summary == '': 
                    continue
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
    title = bill.get("title", {})
    if not text_info:
        print("no text available")
        return ""

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

def save_bill(bill_id, person_created, translated_document, left_translated=None, right_translated=None):
    doc_ref = db.collection("src").document(bill_id)
    doc_ref.set({"Person": person_created, "document": translated_document, "left": left_translated, "right": right_translated})

@app.route('/api/bills', methods=['GET'])
def bills():
    print("received request")
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
    
    print("sending info to frontend")
    return jsonify(summarized_bills)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    selected_text = data.get('selectedText')
    user_input = data.get('userInput')

    # Handle the incoming data here. For example, you can call OpenAI API
    try:
        response = openai.chat.completions.create(       
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