from dotenv import load_dotenv
import os
from flask import Flask
from postmarker.core import PostmarkClient

load_dotenv()  # This will load the .env file variables into the environment
server_token = os.getenv('POSTMARK_SERVER_TOKEN')

postmark = PostmarkClient(server_token=server_token)


### Functions


### Flask App
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'