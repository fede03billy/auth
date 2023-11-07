from dotenv import load_dotenv
import os, string, secrets 
from flask import Flask, request, render_template_string, send_from_directory, make_response
from postmarker.core import PostmarkClient
from flask_redis import FlaskRedis

### Setup
load_dotenv()  # This will load the .env file variables into the environment

server_token = os.getenv('POSTMARK_SERVER_TOKEN')
postmark = PostmarkClient(server_token=server_token)

app = Flask(__name__)

# Configuration for Redis OTP client using database 0
app.config['REDIS_URL_OTP'] = os.getenv('REDIS_URL_OTP', 'redis://localhost:6379/0')
redis_otp_client = FlaskRedis(app, config_prefix='REDIS_URL_OTP')

# Configuration for Redis Auth Token client using database 1
app.config['REDIS_URL_AUTH'] = os.getenv('REDIS_URL_AUTH', 'redis://localhost:6379/1')
redis_auth_client = FlaskRedis(app, config_prefix='REDIS_URL_AUTH')

# Code lengths
otp_length = int(os.getenv('CODE_LENGTH', 6))
token_length = int(os.getenv('TOKEN_LENGTH', 32))

### Functions
## Generate OTP
def generate_otp():
    # Fetch the length from an environment variable; default to 6 if not set
    length = otp_length
    length = max(length, 6)  # Ensure a minimum length of 6
    length = min(length, 24) # Ensure a maximum length of 24

    characters = string.digits

    # Generate the OTP
    return ''.join(secrets.choice(characters) for i in range(length))

## Generate Auth Token
def generate_auth_token():
    # Fetch the length from an environment variable; default to 32 if not set
    length = token_length
    length = max(length, 12)  # Ensure a minimum length of 12
    length = min(length, 64) # Ensure a maximum length of 64

    characters = string.ascii_letters + string.digits

    # Generate the OTP
    return ''.join(secrets.choice(characters) for i in range(length))

## Save OTP on redis
def save_otp(otp, email):
    # Save the OTP
    redis_otp_client.set(email, otp, ex=180)  # Set the OTP to expire in 3 minutes

    return True

## Save Auth Token on redis
def save_auth_token(token, email):
    # Save the Auth Token
    redis_auth_client.set(email, token, ex=60*60*24*7)  # Set the Auth Token to expire in 7 days

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
    email = request.form.get('email') or None

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
        return render_template_string(
            f'<form hx-post="/login-otp" hx-swap="outerHTML" class="flex flex-col">'
            f'<p class="text-sm text-gray-500 max-w-sm mb-4">Input your email address to receive a One Time Password (OTP) to login.</p>'
            f'<input type="email" name="email" placeholder="Email" required value={email} class="px-4 py-2 max-w-sm mb-4 border-2 rounded">'
            f'<input type="text" pattern="\d{"{"+str(otp_length)+"}"}" name="code" required placeholder="OTP" class="px-4 py-2 max-w-sm mb-4 border-2 rounded">'
            f'<button type="submit" class="text-white bg-black rounded px-4 py-2 max-w-sm">Login</button>'
            f'</form>'
        ), 200
    except Exception as e:
        # In case of an error sending the email, log it and return an error response in HTML
        app.logger.error({e})
        return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">Failed to send OTP email. Reload the page and retry.</p>'), 500

@app.route('/login-otp', methods=['POST'])
def login_otp():
    email = request.form.get('email') or None
    code = request.form.get('code') or None

    redis_otp = redis_otp_client.get(email) or None # Data has this format: {b'952619'}

    if not redis_otp:
        # If there's no OTP saved, return an error response in HTML
        return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">OTP expired. Reload the page and retry.</p>'), 400
    else:
        # Decode bytes to string if necessary
        if isinstance(redis_otp, bytes):
            redis_otp = redis_otp.decode('utf-8')

    if code and email:
        # If there's a code field, check if it's valid
        if redis_otp == code:
            auth_token = generate_auth_token()
            save_auth_token(auth_token, email)

            # Create a response and set the auth token as a cookie
            response = make_response(render_template_string('<p class="text-sm text-green-500 max-w-sm mb-4">OTP verified successfully.</p>'))
            response.set_cookie('auth_token', auth_token, max_age=60*60*24*7)  # Cookie will expire in 7 days
            return response, 200
        else:
            # If the code is invalid, return an error response in HTML
            return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">Invalid OTP. Reload the page and retry.</p>'), 200