import os
from dotenv import load_dotenv
load_dotenv()

secrets={
    "mongo_url":os.getenv('MONGO_URL'),
    "mongo_db":os.getenv('MONGO_DB'),
    "host":os.getenv('HOST'),
    "port":os.getenv('PORT'),
}

# mongo
MONGO_URI=secrets['mongo_url']
MONGO_DB=secrets['mongo_db']

# swagger
HOST=secrets['host']
PORT=secrets['port']