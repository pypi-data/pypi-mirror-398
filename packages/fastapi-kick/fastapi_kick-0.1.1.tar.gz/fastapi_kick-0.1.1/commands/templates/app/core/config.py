import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC")
DATABASE_URL_ASYNC = os.getenv("DATABASE_URL_ASYNC")