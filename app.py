from dotenv import load_dotenv
import os, string, secrets
from flask import Flask, request, render_template_string, send_from_directory
from postmarker.core import PostmarkClient
from flask_redis import FlaskRedis

### Setup
load_dotenv()  # This will load the .env file variables into the environment

server_token = os.getenv('POSTMARK_SERVER_TOKEN')
postmark = PostmarkClient(server_token=server_token)

app = Flask(__name__)

redis_client = FlaskRedis(app) # Set REDIS_URL in .env file (Example: redis://localhost:6379/0)

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

## Save OTP on redis
def save_otp(otp, email):
    # Save the OTP
    redis_client.set(email, otp, ex=180)  # Set the OTP to expire in 3 minutes

    return True

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
@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

@app.route('/login', methods=['POST'])
def login():
    # This endpoint expects form data with an "email" field
    email = request.form.get('email')

    # Check if there's also a code field
    code = request.form.get('code')
    app.logger.info({code})
    if code:
        # If there's a code field, check if it's valid
        if redis_client.get(email) == code:
            # If the code is valid, return a success message in HTML
            return render_template_string('<p class="text-sm text-green-500 max-w-sm mb-4">OTP verified successfully.</p>'), 200
        else:
            # If the code is invalid, return an error response in HTML
            return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">Invalid OTP. Reload the page and retry.</p>'), 400
    
    if not email:
        # If no email is provided in the request, return an error response in HTML
        return render_template_string('<p>Email address is required.</p>'), 400

    # Generate the OTP
    otp = generate_otp()

    # Save the OTP with a TTL
    save_otp(otp, email)

    # Send the OTP email
    try:
        send_otp_mail(otp, email)
        # Return a success message in HTML with new button to submit again (try this out)
        return render_template_string('<p class="text-sm text-gray-500 max-w-sm mb-4">OTP sent successfully. Check your email.</p><input type="text" pattern="\d{6}" name="code" placeholder="OTP" required class="px-4 py-2 max-w-sm mb-4 border-2 rounded"></input>'), 200
    except Exception as e:
        # In case of an error sending the email, log it and return an error response in HTML
        app.logger.error({e})
        return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">Failed to send OTP email. Reload the page and retry.</p>'), 500
