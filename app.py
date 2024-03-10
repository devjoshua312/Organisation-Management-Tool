'''
TODO: Add user group system (admin, developer, regular-user etc.
TODO:
'''

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from num2words import num2words
from pymongo import MongoClient
import os
import platform
import datetime
import dotenv
import boto3
import json
import logging
from scan import verify_receipt_with_scan

dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
grec_sitekey = os.getenv('GREC_SITEKEY')

user_level = ''

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

app.config['MONGO_URI'] = os.getenv('MONGO_URI')

mongo = MongoClient(app.config['MONGO_URI'])
db_name = os.getenv('MONGO_DB_NAME')
db = mongo[db_name]

# These will be the names of the collection in the database
user_collection = db['users']
funds_collection = db['funds']
event_collection = db['events']

LoginManager.session_protection = "strong"

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/add_fund_page')
@login_required
def add_fund_page():
    return render_template('add_fund_page.html')


# I only added a 404 page, you can add more error pages if you want
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


@app.route('/error_info')
def error_info():
    return render_template('error_info.html')


@app.route('/create_account')
def create_account():
    return render_template('create_account.html', grec_sitekey=grec_sitekey)


@app.route('/update_user')
@login_required
def update_user():
    user_data = user_collection.find_one({'username': current_user.id})
    # The page doesn't actually need this, but for some reason it doesn't work without it
    return render_template('update_user_info.html', user_data=user_data)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/verify_receipts')
@login_required
def verify_receipts():
    return render_template('verify_receipts.html')


@app.route('/display_donors')
@login_required
def display_donors():
    try:
        funds = funds_collection.find()

        fund_data = []

        for fund in funds:
            if current_user.id == 'developer':
                fund_data.append(fund)
            else:
                if fund['Name'] == current_user.id:
                    fund_data.append(fund)

        highest_donor = ""
        highest_amount = 0

        for fund in funds:
            if float(fund['AmountNumber']) > highest_amount:
                highest_donor = fund['Name']

        return render_template('display_donors.html', username=current_user.id,
                               highest_donor=highest_donor, funds=fund_data)
    except Exception as e:
        logging.error(e)
        return "The System Encountered An Error. Please Try Again Later."


##### POST REQUESTS #####

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            print(username, password)

            user_data = user_collection.find_one({'username': username})

            if user_data:
                if user_data['password'] == password:
                    user = User(username)
                    login_user(user)

                    return redirect(url_for('home'))
                else:
                    return "Invalid password."
            else:
                return "Username not found or does not exist."

        return render_template('login.html', grec_sitekey=grec_sitekey)
    except Exception as e:
        logging.error(e)
        return "The System Encountered An Error. Please Try Again Later."


@app.route('/add_fund', methods=['POST'])
@login_required
def add_fund():
    try:
        name = request.form['name']
        date = request.form['date']
        contact_number = request.form['contact_number']
        amount_words = num2words(
            float(request.form['amount_number']), lang='en_IN')
        amount_number = request.form['amount_number']
        address = request.form['address']

        try:
            if request.files:

                receipt_extension = request.files['receipt'].filename.split('.')[-1]

                receipt = request.files['receipt']
                if receipt:
                    if receipt_extension.lower() != 'jpeg':
                        return 'Invalid file type. Please upload a jpeg file.'
                    file_key = f'{name}/{name}.jpeg'
                    s3.upload_fileobj(receipt, BUCKET_NAME, file_key)

                    file_url = f'https://{BUCKET_NAME}.s3.amazonaws.com/{file_key}'

                else:
                    pass
            else:
                pass
        except Exception as e:
            logging.error(e)
            return "The System Encountered An Error. Please Try Again Later."

        if not name or not date or not contact_number or not amount_words or not amount_number:
            return jsonify({'error': 'Please enter all fund details.'})

        duplicate_fund = funds_collection.find_one({'Name': name})

        if duplicate_fund:
            existing_amount_number = float(duplicate_fund['AmountNumber'])
            new_amount_number = existing_amount_number + float(amount_number)
            funds_collection.update_one({'Name': name}, {'$set': {'AmountNumber': str(
                new_amount_number), 'AmountWords': num2words(new_amount_number, lang='en_IN')}})

            return render_template('add_fund_page.html')

        else:
            new_fund = {
                "Name": name,
                "Date": date,
                "ContactNumber": contact_number,
                "AmountWords": amount_words,
                "AmountNumber": amount_number,
                "Address": address,
                "type": 'completed transaction',
                "cloud_storage_url": f'{file_url}' if request.files else None
            }

            funds_collection.insert_one(new_fund)

            return render_template('add_fund_page.html')
    except Exception as e:
        logging.error(e)
        return "The System Encountered An Error. Please Try Again Later."



@app.route('/events')
def events():
    return render_template('events.html', events=event_collection.find())


@app.route('/update_info', methods=['POST'])
def update_info():
    if request.method == 'POST':
        try:
            user_data = user_collection.find_one({'username': current_user.id})

            # TODO: membership_number = random.randint(100000000, 999999999)
            # TODO: user_data['membership_number'] = membership_number

            user_data['mem_type'] = request.form['mem_type']
            user_data['membership_duration'] = request.form['membership_duration']
            user_data['marital_status'] = request.form['marital_status']
            user_data['alternate_phone'] = request.form['alternate_phone']

            user_collection.update_one(
                {'username': current_user.id}, {'$set': user_data})

            return redirect(url_for('home'))
        except Exception as e:
            logging.error(e)
            return "The System Encountered An Error. Please Try Again Later."
    else:
        return "Invalid request method"


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        try:
            forbidden_names = []

            f = open("bad_usernames.json")
            data = json.load(f)

            for line in data["usernames"]:
                print("line: ", line)
                forbidden_names.append(line)

            try:
                name = request.form['name']
                username = request.form['username']
                password = request.form['password']
                phone_number = request.form['phone']

                if username in forbidden_names:
                    print('Username is not allowed!')
                    return 'Username is not allowed!'

                existing_user = user_collection.find_one(
                    {'username': username})

                if existing_user:
                    return 'Username already exists!'

                new_user = {
                    'name': name,
                    'username': username,
                    'password': password,
                    'phone': phone_number,
                    'user_group': 'normal user'
                }

                user_collection.insert_one(new_user)

                user = User(username)
                login_user(user)

                return redirect(url_for('update_user'))
            except Exception as e:
                logging.error(e)
                return "The System Encountered An Error. Please Try Again Later."
        except Exception as e:
            logging.error(e)
            return "The System Encountered An Error. Please Try Again Later."
    else:
        return "Invalid request method"


@app.route('/remove_donors', methods=['POST'])
@login_required
def remove_donors():
    if user_level != 'developer':
        return send_file('receipts/511', as_attachment=True)
    elif user_level == '':
        return "You are not allowed to view this page."
    else:
        donor_name = request.form['donor_name']

        users = user_collection.find()
        funds = funds_collection.find()

        for user in users:
            if user['username'] == donor_name:
                user_collection.delete_one({'username': donor_name})

        for fund in funds:
            if fund['Name'] == donor_name:
                if fund['cloud_storage_url'] != 'None':
                    file_key = f'{donor_name}/{donor_name}.jpeg'
                    s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)

                funds_collection.delete_one({'Name': donor_name})

    return render_template('display_donors.html')


@app.route('/download_receipt/<donor_name>', methods=['GET', 'POST'])
@login_required
def download_receipt(donor_name):
    try:
        extension = donor_name.split(".")[-1]
        file_key = f'{donor_name}.jpeg' if extension == 'jpeg' else f'{donor_name}.{extension}'
        file_url = f'https://{BUCKET_NAME}.s3.amazonaws.com/{file_key}'

        if current_user.id != 'developer' or current_user.id != 'admin':
            return send_file('receipts/511.txt', as_attachment=True, attachment_filename='info.txt')
        else:
            receipts = os.listdir('receipts/')
            print(receipts)
            print(donor_name)
            return send_file(file_url, download_name=f'{donor_name}.jpeg', as_attachment=True)
    except Exception as e:
        logging.error(e)
        return "The System Encountered An Error. Please Try Again Later."


@app.route('/verify_receipt', methods=['POST'])
@login_required
def verify_receipt():
    try:
        name = request.json.get('name')
        transaction_id = request.json.get('transactionId')

        result = verify_receipt_with_scan(name, transaction_id)

        return jsonify({'result': result})
    except Exception as e:
        logging.error(e)
        return "The System Encountered An Error. Please Try Again Later."


###### HIGH LEVEL ENDPOINTS ######

@app.route('/add_event_page')
@login_required
def add_event_page():
    if current_user.id == 'developer' or current_user.id == 'admin':
        return render_template('add_event_page.html')
    else:
        return "You are not allowed to view this page."


@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    if user_level == 'developer' or user_level == 'admin':
        try:
            event_name = request.form['event_name']
            event_date = request.form['event_date']
            event_description = request.form['event_description']

            new_event = {
                'event_name': event_name,
                'event_date': event_date,
                'event_description': event_description
            }

            event_collection.insert_one(new_event)

            return render_template('add_event_page.html', user=user_level)
        except Exception as e:
            logging.error(e)
            return "The System Encountered An Error. Please Try Again Later."
    else:
        return "You are not allowed to view this page."


@app.route('/debug')
def debug():
    if current_user.id == 'developer':
        try:
            username = current_user.id
            os_info = platform.system()
            release = platform.release()
            version = platform.version()
            time = datetime.datetime.now()
            currenttime = time.strftime("%I:%M:%S %p")
            funds = funds_collection.find()

            return render_template('debug.html', username=username,
                                   grec_sitekey=grec_sitekey,
                                   current_dir=os.getcwd(),
                                   files=os.listdir(),
                                   os=os_info,
                                   release=release,
                                   version=version,
                                   currenttime=currenttime,
                                   bucket_name=BUCKET_NAME,
                                   s3_files=s3.list_objects(Bucket=BUCKET_NAME),
                                   s3_contents=s3.list_objects(Bucket=BUCKET_NAME)['Contents'] if 'Contents' in s3.list_objects(Bucket=BUCKET_NAME) else None,
                                   s3_names=[file['Key'] for file in s3.list_objects(Bucket=BUCKET_NAME)['Contents']] if 'Contents' in s3.list_objects(Bucket=BUCKET_NAME) else None,
                                   db_name=os.getenv('MONGO_DB_NAME'),
                                   names = [fund['Name'] for fund in funds],
                                   collections=db.list_collection_names())
        except Exception as e:
            logging.error(e)
            return "The System Encountered An Error. Please Try Again Later."
    else:
        return "You are not allowed to view this page."


if __name__ == '__main__':
    # remove debug statement when deploying
    app.run(debug=True)
