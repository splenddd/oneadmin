import re
import time

from cloudant import Cloudant

from config import *
from one_drive import OneDrive

LICENSES_MAP = {
    '94763226-9b3c-4e75-a931-5c89701abe66': 'A1教职',
    '314c4481-f395-4525-be8b-2ec4bb1e9d91': 'A1学生',
    '6fd2c87f-b296-42f0-b197-1e91e994b900': 'Office 365 E3',
    'c42b9cae-ea4f-4ab7-9717-81576235ccac': 'Office 365 E5'
}


one = OneDrive()


class DB:

    def __init__(self):
        self.client = Cloudant.iam(ACCOUNT_NAME, API_KEY, connect=True)
        if DB_NAME in self.client:
            self.db = self.client[DB_NAME]
        else:
            self.db = self.client.create_database(DB_NAME)

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()


def get_accounts():
    data = []
    with DB() as db:
        for document in db:
            _id = document['_id']
            _account = re.search(r'one_drive_admin_([\w]+)_session', _id).group(1)
            data.append(_account)
        return data


def get_users(account):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.get_users()


def get_users_page(account, url):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.api(url)


def get_user(account, user_id):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.get_user(user_id)


def enabled_user(account, user_id, status=True):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.enabled_user(user_id, status)


def get_role(account, user_id):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.get_role(user_id)


def create_user(account, username, password):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.create_user(username=username, password=password)


def delete_user(account, username):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.delete_user(username)


def get_access(account, db):
    _id = f'one_drive_admin_{account}_session'
    document = db[_id]

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
