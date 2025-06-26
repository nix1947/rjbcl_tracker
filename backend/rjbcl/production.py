from .settings import  *
import os
from dotenv import load_dotenv
load_dotenv()  # Load from .env file


DEBUG = False


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE') or 'statement_tracker',               # Database name
        'USER': os.getenv('MYSQL_USERNAME') or 'statement_tracker',               # Database user
        'PASSWORD': os.getenv('MYSQL_PASSWORD') or '',      # From environment variables
        'HOST': 'localhost',                       # MySQL host
        'PORT': '3306',                            # Default MySQL port
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET NAMES 'utf8mb4'",
        },
    }
}