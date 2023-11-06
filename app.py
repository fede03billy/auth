from dotenv import load_dotenv
import os, string, secrets
from flask import Flask
from postmarker.core import PostmarkClient

load_dotenv()  # This will load the .env file variables into the environment
server_token = os.getenv('POSTMARK_SERVER_TOKEN')

postmark = PostmarkClient(server_token=server_token)


### Functions
## Generate OTP
def generate_otp():
    # Fetch the length from an environment variable; default to 6 if not set
    length = int(os.getenv('CODE_LENGTH', 6))
    length = max(length, 6)  # Ensure a minimum length of 6
    length = min(length, 24) # Ensure a maximum length of 24

    characters = string.digits

    # Generate the OTP
    return ''.join(secrets.choice(characters) for i in range(length))

## Send OTP Mail
def send_otp_mail(otp, email):
    # Fetch the sender email from an environment variable
    sender = f'otp@{os.getenv("DOMAIN_NAME", "example.com")}'

    # Send the OTP email
    response = postmark.emails.send(
        From=sender,
        To=email,
        Subject=f'Your OTP is {otp}',
        TextBody=f'Your OTP is {otp}, valid for 3 minutes. If you did not request this, please ignore this email.'
    )

    return response

### Flask App
app = Flask(__name__)

@app.route('/')
def hello_world():
    return generate_otp()