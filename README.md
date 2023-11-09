# Authentication Service
This service provides an authentication system using one-time passwords (OTP) sent via email and auth tokens stored in the client as cookie.

The server is written in Python using Flask and the client is plain HTML with the help of HTMX. Auth codes and tokens are stored in Redis.

## Getting Started
These instructions will cover usage information and for the docker container.

## Prerequisities
In order to run this container you'll need docker and docker-compose installed.

# Environment Variables
To run this project, you will need to add the following environment variables to your .env file

- **POSTMARK_SERVER_TOKEN** - Your Postmark server token for sending emails.

- **REDIS_URL_OTP** - The Redis server URL for storing OTPs, default is `redis://localhost:6379/0`.

- **REDIS_URL_AUTH** - The Redis server URL for storing auth tokens, default is `redis://localhost:6379/1`.

- **CODE_LENGTH** - The length of the OTP code, default is `6`.

- **TOKEN_LENGTH** - The length of the auth token, default is `32`.

- **DOMAIN_NAME** - Your domain name for the sender email address, default is `example.com`.

- **AUTH_SECRET_KEY** - A secret key required to retrieve all auth tokens.

### Optional
You can also set the following optional variables:

- **DEBUG** - Set to True to enable Flask debug mode.

🚧 WIP