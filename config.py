import json
import os

ADMIN_NAME = os.environ.get('ADMIN_NAME', 'root')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '123456')
ACCOUNT_NAME = os.environ.get('ACCOUNT_NAME', '633cbc5a-dd68-45c4-8e85-1d9e056c0d8a-bluemix')
API_KEY = os.environ.get('API_KEY', '6hW0XBfz8N52wesCwFRvbars2-6z08qhXuTueGvmKMcG')
DB_NAME = os.environ.get('DB_NAME', 'db-1')
DEBUG = os.environ.get('DEBUG', True)

LICENSES_MAP = {
    '94763226-9b3c-4e75-a931-5c89701abe66': 'A1教职',
    '314c4481-f395-4525-be8b-2ec4bb1e9d91': 'A1学生',
    '6fd2c87f-b296-42f0-b197-1e91e994b900': 'Office 365 E3',
    'c42b9cae-ea4f-4ab7-9717-81576235ccac': 'Office 365 E5'
}

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        API_KEY = creds['apikey']
        ACCOUNT_NAME = creds['username']
