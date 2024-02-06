# Organization Management Tool

A Flask application for managing funds, donor information, adding new users and more.

## Overview

A Flask app to simulate functionality for managing funds, generating receipts, displaying donor information, and acting as a dashboard for your community. It is designed to be a simple and effective tool for tracking your user base. The program connects to a MongoDB DataBase for storing information and an AWS Cloud Server for storing the reciepts.

## Features

- User authentication using Flask-Login
- Add funds with details like name, date, contact number, and receipt
- Display a list of donors with contribution details
- Scan the reciept given by donor to see if the names match
- Uses a reliable data storing/retrieval system
- Cloud Storage for downloading reciepts.


## Installation

1. Clone the repository:

   ```
   git clone https://github.com/devjoshua312/Finance-Entry-Tool-flask.git
   ```

2. Change into the project directory:

   ```
   cd project-folder
   ```



# Prerequisites

## Install Packages

Before running the application, ensure you have all the required packages by running;

```
pip install -r requirements.txt
```
  

## Environment Variables

> Create a `.env` file in the project root and set the environment variables:


```
grec_sitekey=your_recaptcha_key
MONGO_URI=your-mongo-uri
MONGO_DB_NAME=the-name-of-your-mongodb
AWS_BUCKET_NAME=the-name-of-your-aws-s3-bucket
AWS_ACCESS_KEY_ID=access-key-id-of-your-iam-user
AWS_SECRET_ACCESS_KEY=secret-key-of-your-iam-user
```


Setting up your program to interact with the MongoDB can be quite painful and confusing, but you only need to change two things in the file:

1) The .env variables
2) The DB name

As for interacting with the AWS CS, this process is a little extensive.
1) Sign up for the AWS Console, and search for S3 in the search bar.
   > Follow the instructions on screen to continue to create a Storage Bucket.
2) Now, search for 'IAM' in the search bar
   > Proceed to create a new user in your organization which can interact with these databases. 
   > When setting permissions, make sure to select 'AmazonS3FullAccess' permission for your user.
3) Finally, copy the relevant data, and update the .env file.


> For information on creating, accessing and viewing your mongo dbs, [Mongo Docs](https://www.mongodb.com/docs/atlas/)

> For information on creating a reCaptcha key, check out [Google reCaptcha](https://www.google.com/recaptcha/about/)

> Info on AWS, [AWS S3 Setup Guide](https://aws.amazon.com/s3/getting-started/)

<hr />

# Usage

Run the Flask application:

There are two ways to do this. One is with the Python Flask service:
```
python app.py
```

And the other is by using Gunicorn

```
gunicorn app:app.py
```

If you want to run gunicorn on a custom server:
```
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
```
-w 4: Specifies the number of worker processes. (typically between 2-4).
-b 0.0.0.0:8000: Binds Gunicorn to all network interfaces.
```

> for more info and help, visit [gunicorn home page](https://docs.gunicorn.org/en/latest/run.html)

>for info on running a node server check out [npm docs](https://docs.npmjs.com/cli/v7/commands/npm-start)

## Endpoints

- `/`: Home page
- `/login`: Login page
- `/logout`: Logout
- `/download_receipt/<donor_name>`: Download receipt for a specific donor (backend)
- `/add_fund`: Add a new fund (backend, cannot access through webpage)
- `/remove_donors`: Remove donors (accessible to admin only)
- `/display_donors`: Display list of donors
- `/verify_receipts`: Page to use the image scanning feature
- `/create_account`: Allows you to create a new user account.
- `/register`: The backend of the create account page
- `/debug`: A brief debug page with the essential tools for debugging like current dir, buttons to test endpoints and such.

<hr>

> ### Note
   > I've begun to use this as a personal project to host a small scale website, so there might be some changes you will need to do such as changing the website `<title>` tags and such; However, rest of the code will remain unchanged, and fully functional.