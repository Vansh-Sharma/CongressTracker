import requests
import datetime
import openai

# Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
OPENAI_API_KEY = 'sk-proj-tBbHRorynUbGV9FtebQhT3BlbkFJVrZzpw6auk20631KEVtn'

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

def get_bills_introduced_last_year():
    # Calculate the date range for the last year
    today = datetime.datetime.now()
    last = today - datetime.timedelta(days=7)
    today_str = today.strftime('%Y-%m-%d')
    last_str = last.strftime('%Y-%m-%d')
    
    # Construct the API endpoint
    url = f"https://www.govtrack.us/api/v2/bill?congress=118&introduced_date__gte={last_str}&introduced_date__lte={today_str}&sort=-introduced_date"
    
    # Make the request
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        bills = data.get('objects', [])
        
        # Print the bills introduced in the last year
        if bills:
            print(f"Bills introduced from {last_str} to {today_str}:")
            for bill in bills:
                title = bill['title']
                introduced_date = bill['introduced_date']
                
                # Print bill details
                print(f"Title: {title}")
                print(f"Introduced Date: {introduced_date}")
                
                # Get the full text of the bill and summarize it
                summary = get_bill_summary(bill)
                print(f"Summary: {summary}")
                print('-' * 40)
                
        else:
            print(f"No bills introduced from {last_str} to {today_str}.")
    else:
        print(f"Failed to retrieve data: {response.status_code}")

def get_bill_summary(bill):
    text_info = bill.get('text_info', {})
    if not text_info:
        reason = "No text as of now. \n Bills are generally sent to the Library of Congress from GPO, the Government Publishing Office, a day or two after they are introduced on the floor of the House or Senate. Delays can occur when there are a large number of bills to prepare or when a very large bill has to be printed."
        return reason

    gpo_pdf_url = text_info.get('gpo_pdf_url', '')
    if not gpo_pdf_url:
        return "No bill text URL available."

    # Use OpenAI to summarize the bill
    summary = summarize_text(gpo_pdf_url)
    return summary

def summarize_text(url):
    try:
        response = openai.chat.completions.create(       
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following information: {url}",
                }
            ],
            model="gpt-4",
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Failed to summarize text: {str(e)}"

if __name__ == "__main__":
    get_bills_introduced_last_year()
