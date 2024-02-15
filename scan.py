from pymongo import MongoClient
from dotenv import load_dotenv
import os
import boto3
import easyocr
import re
import logging

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
mongo_client = MongoClient(mongo_uri)
db_name = os.getenv('MONGO_DB_NAME')
db = mongo_client[db_name]
collection = db['funds']

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')


def extract_text_from_image(object_key):
    try:
        s3_client.download_file(BUCKET_NAME, object_key, f"receipts/{object_key}")

        reader = easyocr.Reader(['en'])
        result = reader.readtext(f"receipts/{object_key}")
        text = ' '.join([item[1] for item in result])

        os.remove(f"receipts/{object_key}")

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
        
        for items in fund:
            if 'cloud_storage_url' in items is None:
                return 'You have not submitted any reciepts.'

        object_key = f"{name}.jpeg"

        extracted_text = extract_text_from_image(object_key)

        if 'Error' in extracted_text:
            logging.error(extracted_text)
            return extracted_text

        elif transaction_id in extracted_text or name in extracted_text:
            return 'match'
        else:
            return 'no_match'
    except Exception as e:
        print('Error during receipt verification:', e)
        return 'Could not finish verification process. Please try again later.'