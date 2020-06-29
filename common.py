import os
import re
import time
from datetime import datetime, timezone, timedelta

from cloudant import Cloudant

from config import ACCOUNT_NAME, API_KEY, DB_NAME
from one_drive import OneDrive

LICENSES_MAP = {
    '94763226-9b3c-4e75-a931-5c89701abe66': 'A1教职',
    '314c4481-f395-4525-be8b-2ec4bb1e9d91': 'A1学生',
    '6fd2c87f-b296-42f0-b197-1e91e994b900': 'Office 365 E3',
    'c42b9cae-ea4f-4ab7-9717-81576235ccac': 'Office 365 E5'
}

account_name = os.environ.get('ACCOUNT_NAME', ACCOUNT_NAME)
api_key = os.environ.get('API_KEY', API_KEY)
db_name = os.environ.get('DB_NAME', DB_NAME)
one = OneDrive()


class DB:

    def __init__(self):
        self.client = Cloudant.iam(account_name, api_key, connect=True)
        if db_name in self.client:
            self.db = self.client[db_name]
        else:
            self.db = self.client.create_database(db_name)

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


def get_subscribed(account):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.get_subscribed()


def create_user(account, username, password):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.create_user(username=username, password=password)


def delete_user(account, username):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.delete_user(username)


def get_files(account, user):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.file_list(user)


def delete_file(account, user, file_id):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.delete_file(user, file_id)


def get_file(account, user, file_id):
    with DB() as db:
        one._drive_access = get_access(account, db)
        return one.get_file(user, file_id)


def authorize_url(client_id, tenant_id):
    return one.authorize_url(client_id=client_id, tenant_id=tenant_id)


def install_admin(org, **kwargs):
    if kwargs.get('auth_type') == 'oauth':
        data = one.fetch_token(**kwargs)
    else:
        data = one.get_ms_token(**kwargs)
    kwargs.update(data)
    kwargs['_id'] = f'one_drive_admin_{org}_session'
    kwargs['expires_time'] = int(time.time()) + 3500
    del kwargs['code']
    with DB() as db:
        return db.create_document(kwargs)


def get_access(account, db):
    _id = f'one_drive_admin_{account}_session'
    document = db[_id]
    not_time = int(time.time())
    if document['expires_time'] < not_time:
        if document['auth_type'] == 'oauth':
            data = one.refresh_token(**document)
        else:
            data = one.get_ms_token(**document)

        document['access_token'] = data['access_token']
        document['expires_time'] = not_time + 3500
        if data.get('refresh_token'):
            document['refresh_token'] = data['refresh_token']
        document.save()
    return document


def update():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

    with DB() as db:
        for document in db:
            if document['auth_type'] == 'oauth':
                data = one.refresh_token(**document)
            else:
                data = one.get_ms_token(**document)

            document['access_token'] = data['access_token']
            document['expires_time'] = int(time.time()) + 3500
            document['update_time'] = bj_dt
            if data.get('refresh_token'):
                document['refresh_token'] = data['refresh_token']
            document.save()
