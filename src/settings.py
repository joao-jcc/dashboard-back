import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do banco principal
DATABASE_CONFIG = {
    'host': 'aws.connect.psdb.cloud',
    'port': 3306,
    'database': 'ei',
    'user': os.getenv('USER_DATABASE_EINSC'),
    'password': os.getenv('PASSWORD_DATABASE_EINSC'),
    'ssl_disabled': False
}

# Configuração do banco espelho/mirror
DATABASE_MIRROR_CONFIG = {
    'host': '5.161.229.26',
    'port': 3306,
    'database': 'espelho',
    'user': os.getenv('USER_DATABASE_EINSC_MIRROR'),
    'password': os.getenv('PASSWORD_DATABASE_EINSC_MIRROR'),
    'ssl_disabled': True
}