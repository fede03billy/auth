from dotenv import load_dotenv
import os, string, secrets 
from flask import Flask, request, render_template_string, send_from_directory, make_response
from postmarker.core import PostmarkClient
import redis

### Setup
load_dotenv()  # This will load the .env file variables into the environment

server_token = os.getenv('POSTMARK_SERVER_TOKEN')
postmark = PostmarkClient(server_token=server_token)

app = Flask(__name__)

# Configuration for Redis OTP client using database 0
redis_otp_client = redis.from_url(os.getenv('REDIS_URL_OTP'))

# Configuration for Redis Auth Token client using database 1
redis_auth_client = redis.from_url(os.getenv('REDIS_URL_AUTH'))
# Code lengths
otp_length = int(os.getenv('OTP_CODE_LENGTH', 6))
otp_duration = int(os.getenv('OTP_CODE_EXPIRY', 300)) # 5 minutes in seconds
token_length = int(os.getenv('AUTH_TOKEN_LENGTH', 32))
token_duration = int(os.getenv('AUTH_TOKEN_EXPIRY', 604800))  # 7 days in seconds
token_name = os.getenv('AUTH_TOKEN_COOKIE_NAME', 'auth_token')

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
    # Save the email as Key for the OTP
    redis_otp_client.set(email, otp, ex=otp_duration) 

    return True

## Save Auth Token on redis
def save_auth_token(token, email):
    # Save the Auth Token as Key for the email
    redis_auth_client.set(token, email, ex=token_duration)  # Set the Auth Token to expire in 7 days

    return True

## Send OTP Mail
def send_otp_mail(otp, email):
    # Fetch the sender email from an environment variable
    sender = f'otp@{os.getenv("DOMAIN_NAME")}'

    # Send the OTP email
    response = postmark.emails.send(
        From=sender,
        To=email,
        Subject=f'Your OTP is {otp}',
        TextBody=f'Your OTP is {otp}, valid for {otp_duration / 60} minutes. If you did not request this, please ignore this email.'
    )

    return response

## Verify Auth Token
def verify_auth_token(token):
    # Check if the token is valid
    email = redis_auth_client.get(token) or None

    if email:
        # If the token is valid, return the email
        return email.decode('utf-8')
    else:
        # If the token is invalid, return None
        return None

## Refresh Auth Token
def refresh_auth_token(token):
    # Check if the token is valid
    email = redis_auth_client.get(token) or None

    if email:
        email = email.decode('utf-8')
        # If the token is valid, generate a new token and save it
        new_token = generate_auth_token()
        save_auth_token(new_token, email)

        # Delete the old token
        redis_auth_client.delete(token)

        # Return the new token
        return new_token
    else:
        # If the token is invalid, return None
        return None


### Flask App
## Root route
## Handles the check for existing auth token cookie and serves the login form if not logged in
@app.route('/')
def root():
    # Check for existing auth token cookie
    auth_token = request.cookies.get(token_name) or None

    if auth_token:
        email = verify_auth_token(auth_token)
        if email:
            # If the auth token is valid, return a success message in HTML
            return render_template_string(f'You are already logged in as {email}'), 200
        else:
            # If the auth token is invalid, remove the old cookie and send the login pagin in HTML
            response = make_response(send_from_directory('static', 'index.html'))
            response.set_cookie(token_name, '', expires=0)
            return response, 200

    return send_from_directory('static', 'index.html')

## Login route
## Handles the login form submission and sends the OTP email
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
            f'<input type="text" pattern="\\d{"{"+str(otp_length)+"}"}" name="code" required placeholder="OTP (Check your email)" class="px-4 py-2 max-w-sm mb-4 border-2 rounded">'
            f'<button type="submit" class="text-white bg-black rounded px-4 py-2 max-w-sm">Login</button>'
            f'</form>'
        ), 200
    except Exception as e:
        # In case of an error sending the email, log it and return an error response in HTML
        app.logger.error({e})
        return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">Failed to send OTP email. Reload the page and retry.</p>'), 200

## Login OTP route
## Handles the OTP form submission and sets the auth token cookie
@app.route('/login-otp', methods=['POST'])
def login_otp():
    email = request.form.get('email') or None
    code = request.form.get('code') or None

    redis_otp = redis_otp_client.get(email) or None # Data has this format: {b'952619'}

    if not redis_otp:
        # If there's no OTP saved, return an error response in HTML
        return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">OTP is wrong or expired. Reload the page and retry.</p>'), 200
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
            response.set_cookie(token_name, auth_token, max_age=token_duration)
            return response, 200
        else:
            # If the code is invalid, return an error response in HTML
            return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">Invalid OTP. Reload the page and retry.</p>'), 200
    else:
        # If there's no code field, return an error response in HTML
        return render_template_string('<p class="text-sm text-red-300 max-w-sm mb-4">OTP is required. Reload the page and retry.</p>'), 200
    
## Auth Tokens route
## Handles the request for all the auth tokens in the database to allow third party apps to check for valid tokens
@app.route('/auth-tokens', methods=['GET'])
def auth_tokens():
    # Get the AUTH_SECRET_KEY from the token bearer in the request headers
    auth_secret_key = request.headers.get('Authorization') or None

    # Parse the secret key from the token bearer
    if auth_secret_key:
        auth_secret_key = auth_secret_key.split(' ')[1] or None

    if auth_secret_key == os.getenv('AUTH_SECRET_KEY'):
        # If the secret key is valid, return all the auth tokens in a JSON response
        auth_tokens = redis_auth_client.keys('*') or None # Output is [... , b'ElRUVOlmLFHuzGEN55rFueaHyey7A8J9', b'vr0dvx8tRLy8WEQsD4XAV6PSVYR7GgeY']
        # Decode bytes for each entry in the array
        if auth_tokens:
            auth_tokens = [token.decode('utf-8') for token in auth_tokens]
            return auth_tokens, 200
        else:
            return [], 200
    else:
        # If the secret key is invalid, return a 403 error
        return 'Forbidden', 403

## Check Auth route
## Handles the request to check if an auth token is valid and refresh it, for third party apps as middleware
## This expects to receive the auth token in the request  Authorization header or in the cookie, split it from the token bearer, and get back the new auth token in a JSON response
@app.route('/check-auth', methods=['GET'])
def check_auth():
    # Get the auth token from the request headers
    auth_token = request.headers.get('Authorization') or None

    if not auth_token:
        # Look for the auth token in the cookies
        auth_token = request.cookies.get(token_name) or None

    # Parse the auth token from the token bearer
    if auth_token:
        auth_token = auth_token.split(' ')[1] or None
    else:
        # If there's no auth token, return a 403 error
        return 'Forbidden', 403

    # Check if the auth token is valid
    email = redis_auth_client.get(auth_token) or None

    if email:
        # If the auth token is valid, refresh it
        new_auth_token = refresh_auth_token(auth_token)

        # Set the new auth token as a cookie
        response = make_response({'auth_token': new_auth_token})
        response.set_cookie(token_name, new_auth_token, max_age=token_duration)

        # Return the new auth token in a JSON response and as a cookie
        return response, 200
    else:
        # If the auth token is invalid, return a 403 error
        return 'Forbidden', 403