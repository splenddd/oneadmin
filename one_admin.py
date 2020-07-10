import os
import re
import time
from datetime import datetime, timezone, timedelta

from cloudant import Cloudant

from config import ACCOUNT_NAME, API_KEY, DB_NAME
from one_drive import OneDrive

account_name = os.environ.get('ACCOUNT_NAME', ACCOUNT_NAME)
api_key = os.environ.get('API_KEY', API_KEY)
db_name = os.environ.get('DB_NAME', DB_NAME)


class OneAdmin:
    client = Cloudant.iam(account_name, api_key, connect=True)
    db = client.create_database(db_name)
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

    def __init__(self):
        self.one = OneDrive()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()

    def load(self, org_name, app_token=False):
        _id = f'one_drive_admin_{org_name}_session'
        document = self.db[_id]
        not_time = int(time.time())
        if document['expires_time'] < not_time and document['auth_type'] == 'oauth':
            data = self.one.refresh_token(**document)
            document['access_token'] = data['access_token']
            document['expires_time'] = not_time + 3500
            if data.get('refresh_token'):
                document['refresh_token'] = data['refresh_token']
            document.save()

        if document['app_data']['expires_time'] < not_time:
            app_data = self.one.get_ms_token(**document)
            app_data['expires_time'] = int(time.time()) + 3500
            app_data['update_time'] = self.bj_dt
            document['app_data'] = app_data
            document.save()

        self.one.access_token = document['access_token']
        if app_token or document['auth_type'] != 'oauth':
            self.one.access_token = document['app_data']['access_token']

    @classmethod
    def get_org_list(cls):
        data = []
        for document in cls.db:
            _id = document['_id']
            _org_name = re.search(r'one_drive_admin_([\w]+)_session', _id).group(1)
            data.append(_org_name)
        return data

    def api(self, org_name, api_url):
        self.load(org_name)
        return self.one.api(api_url)

    def enabled_user(self, org_name, user_id, status=True):
        self.load(org_name)
        return self.one.enabled_user(user_id, status)

    def __getattr__(self, item):
        def call_back(*args, **kwargs):
            self.load(args[0], **kwargs)
            func = getattr(self.one, item)
            if kwargs.get('app_token'):
                del kwargs['app_token']
            return func(*args[1:], **kwargs)

        return call_back


if __name__ == '__main__':
    admin = OneAdmin()
    print(admin.get_users('atcaoyufei'))
