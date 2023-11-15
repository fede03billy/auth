# Authentication Service
This service provides an authentication system using one-time passwords (OTP) sent via email and auth tokens stored in the client as cookie.

The server is written in Python using Flask and the client is plain HTML with the help of HTMX. Auth codes and tokens are stored in Redis.

## Getting Started
These instructions will cover usage information and for the docker container. You will need a Postmark account with a validated domain to send emails.

The project is composed of a Python3 Server and a HTML/JS Client. The server is built using Flask and the client is built using HTMX. Redis is used to store OTPs and auth tokens. The server and client are both containerized using Docker and can be run using docker-compose in production.

The logic behind the authentication process is simple: the user submits their email address, an OTP is generated and sent to their email, the user submits the OTP, and an auth token is generated and stored in the client as a cookie. The auth token is then used to verify the user's identity for subsequent requests.

## Prerequisities
In order to run this container you'll need docker and docker-compose installed.

## Environment Variables
To run this project, you will need to add the following environment variables to your `.env` file

| Var Name                | Required | Default Value           | Explanation                                         |
|-------------------------|----------|-------------------------|-----------------------------------------------------|
| PORT                    | Yes      | N/A                     | The port on the container exposes.                  |
| POSTMARK_SERVER_TOKEN   | Yes      | N/A                     | Your Postmark server token for sending emails.      |
| DOMAIN_NAME             | Yes      | N/A                     | Your domain name for the sender email address.      |
| AUTH_SECRET_KEY         | Yes      | N/A                     | A secret key required to retrieve all auth tokens.  |
| REDIS_URL_OTP           | No       | `redis://localhost:6379/0` | The Redis server URL for storing OTPs.             |
| REDIS_URL_AUTH          | No       | `redis://localhost:6379/1` | The Redis server URL for storing auth tokens.       |
| OTP_CODE_LENGTH         | No       | `6`                     | The length of the OTP code.                         |
| OTP_CODE_EXPIRY         | No       | `300`                   | The expiry time of the OTP code in seconds.         |
| AUTH_TOKEN_LENGTH       | No       | `32`                    | The length of the auth token.                       |
| AUTH_TOKEN_EXPIRY       | No       | `604800`                | The expiry time of the auth token in seconds.       |
| AUTH_TOKEN_COOKIE_NAME  | No       | `auth_token`            | The name of the cookie that stores the auth token.  |
| DEBUG                   | No       | `False`                 | Set to True to enable Flask debug mode.             |

## Usage
After cloning the repository and setting up the environment variables in the `.env` file, you can run the following commands to start the server.

```bash
docker compose up -d
```

This will start the main app on port 3000 of your local environment. You can then access it by navigating to http://localhost:3000.

## API Endpoints

This application exposes several endpoints, each serving a specific function within the authentication process:

### 1. Root Route (`/`)
- **Method**: GET
- **Purpose**: Checks for an existing authentication token cookie. If a valid token is present, the user is informed they are already logged in. Otherwise, the login page is served.
- **Response**: HTML content (either a success message or the login page).

### 2. Login Route (`/login`)
- **Method**: POST
- **Purpose**: Handles the login form submission. It generates a One Time Password (OTP), sends it to the user's email, and serves a form for OTP submission.
- **Expected Input**: Email address in form data.
- **Response**: HTML content with instructions or error message.

### 3. Login OTP Route (`/login-otp`)
- **Method**: POST
- **Purpose**: Processes the submitted OTP. If the OTP is valid, it generates an authentication token, sets it as a cookie, and indicates successful verification.
- **Expected Input**: Email and OTP code in form data.
- **Response**: HTML content indicating OTP verification status.

### 4. Auth Tokens Route (`/auth-tokens`)
- **Method**: GET
- **Purpose**: Provides a list of all authentication tokens stored in the database. This is useful for third-party applications to verify token validity.
- **Expected Input**: Authorization header containing a secret key.
- **Response**: JSON array of authentication tokens or a 403 Forbidden error for invalid secret key.

### 5. Check Auth Route (`/check-auth`)
- **Method**: GET
- **Purpose**: Validates an existing authentication token, refreshes it, and returns the new token. This endpoint is useful as middleware for third-party applications.
- **Expected Input**: Authorization header or cookie containing the authentication token.
- **Response**: JSON object containing the new authentication token or a 403 Forbidden error for invalid token.

---

These endpoints are designed to facilitate a secure and efficient authentication process. The use of OTP and token-based authentication ensures enhanced security and a smooth user experience. The `/auth-tokens` and `/check-auth` endpoints are particularly useful for integrating this authentication system with third-party applications, providing a reliable method for token validation and refresh.