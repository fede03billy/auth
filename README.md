# Authentication Service
This service provides an authentication system using one-time passwords (OTP) sent via email and auth tokens stored in the client as cookie.

The server is written in Python using Flask and the client is plain HTML with the help of HTMX. Auth codes and tokens are stored in Redis.

## Getting Started
These instructions will cover usage information and for the docker container.

## Prerequisities
In order to run this container you'll need docker and docker-compose installed.

# Environment Variables
To run this project, you will need to add the following environment variables to your .env file

| Var Name                | Required | Default Value           | Explanation                                         |
|-------------------------|----------|-------------------------|-----------------------------------------------------|
| POSTMARK_SERVER_TOKEN   | Yes      | N/A                     | Your Postmark server token for sending emails.      |
| REDIS_URL_OTP           | No       | `redis://localhost:6379/0` | The Redis server URL for storing OTPs.             |
| REDIS_URL_AUTH          | No       | `redis://localhost:6379/1` | The Redis server URL for storing auth tokens.       |
| CODE_LENGTH             | No       | `6`                     | The length of the OTP code.                         |
| TOKEN_LENGTH            | No       | `32`                    | The length of the auth token.                       |
| DOMAIN_NAME             | Yes      | `example.com`           | Your domain name for the sender email address.      |
| AUTH_SECRET_KEY         | Yes      | N/A                     | A secret key required to retrieve all auth tokens.  |

### Optional
You can also set the following optional variables:

- **DEBUG** - Set to True to enable Flask debug mode.

🚧 WIP