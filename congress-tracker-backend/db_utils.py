import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account.
import sys

sys.path.append("../")

print(sys.path)
cred = credentials.Certificate("billtrack-a2369-72eca0fdbb6d.json")

app = firebase_admin.initialize_app(cred)

db = firestore.client()
db = db.collection("src")

def document_exists(doc):
    doc_ref = db.document(doc)
    doc = doc_ref.get()
    return doc.exists

def insert_bill(bill, content):
    title = bill.get("title", "").split(":")[0]
    doc_ref = db.document(title)
    doc_ref.set({
        "title": bill.get("title", ""),
        "party": bill.get("party", ""),
        "date": bill.get("introduced_date", ""),
        "content": content
    })

def return_bill_content(bill):
    title = bill.get("title", "").split(":")[0]
    doc_ref = db.document(title)
    return doc_ref["content"]

print(document_exists("bills"))