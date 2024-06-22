import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account.
cred = credentials.Certificate('../billtrack-a2369-72eca0fdbb6d.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()

users_ref = db.collection("src")
docs = users_ref.stream()

'''
Docs only contains "bills" of dict type
'''

for doc in docs:
    print(f"{doc.id} => {doc.to_dict()}")