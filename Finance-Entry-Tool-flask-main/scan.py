from pymongo import MongoClient
from dotenv import load_dotenv
import os
import easyocr
import re

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
mongo_client = MongoClient(mongo_uri)
db_name = os.getenv('MONGO_DB_NAME')
db = mongo_client[db_name]
collection = db['funds']

def extract_text_from_image(image_path):
    try:
        reader = easyocr.Reader(['en'])
        result = reader.readtext(image_path)
        text = ' '.join([item[1] for item in result])
        return text
    except Exception as e:
        return f"Error during text extraction: {e}"

def extract_transaction_id(text):
    transaction_id_patterns = [
        re.compile(r'TXN ID:\s*(\S+)', re.DOTALL),
        re.compile(r'Transaction ID\n\n(\S+)', re.DOTALL),
    ]

    for pattern in transaction_id_patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()

    return None

def verify_receipt_with_scan(name, transaction_id):
    try:
        fund = collection.find_one({'Name': name})

        if not fund:
            return 'You have not added a donation, nor submitted any reciepts.'

        extracted_text = extract_text_from_image(f"receipts/{name}.jpeg")

        if 'Error' in extracted_text:
            if 'file' in extracted_text:
                return 'File Does Not Exist'
            else:
                print(extracted_text)
                return 'Error'

        elif transaction_id in extracted_text or name in extracted_text:
            collection.update_one({'Name': name}, {'$set': {'recStatus': 'verified'}})
            return 'match'
        else:
            return 'no_match'
    except Exception as e:
        print('Error during receipt verification:', e)
        return 'error'
