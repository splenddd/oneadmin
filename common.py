import os
import re
import time

from cloudant import Cloudant

from one_drive import OneDrive

LICENSES_MAP = {
    '94763226-9b3c-4e75-a931-5c89701abe66': 'A1教职',
    '314c4481-f395-4525-be8b-2ec4bb1e9d91': 'A1学生',
    '6fd2c87f-b296-42f0-b197-1e91e994b900': 'Office365E3'
}

account_name = os.environ.get('ACCOUNT_NAME')
api_key = os.environ.get('API_KEY')
db_name = os.environ.get('DB_NAME')
client = Cloudant.iam(account_name, api_key, connect=True)
if db_name in client:
    db = client[db_name]
else:
    db = client.create_database(db_name)
one = OneDrive()


def get_accounts():
    data = []
    for document in db:
        _id = document['_id']
        _account = re.search(r'one_drive_admin_([\w]+)_session', _id).group(1)
        data.append(_account)
    return data


def get_users(account):
    _id = f'one_drive_admin_{account}_session'
    document = db[_id]
    one._drive_access = check(document)
    return one.get_users()


def check(document):
    not_time = int(time.time())
    if document['expires_time'] < not_time:
        data = one.refresh_token(**document)
        document['access_token'] = data['access_token']
        document['auth_type'] = 'oauth'
        document['expires_time'] = not_time + 3500
        if data['refresh_token']:
            document['refresh_token'] = data['refresh_token']
        document.save()
    return document
