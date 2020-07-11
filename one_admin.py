import json
import re
import time
from datetime import datetime, timezone, timedelta

from cloudant import Cloudant

from config import ACCOUNT_NAME, API_KEY, DB_NAME
from one_drive import OneDrive


class OneAdmin:
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

    def __init__(self):
        self.one = OneDrive()
        self.client = Cloudant.iam(ACCOUNT_NAME, API_KEY, connect=True)
        self.db = self.client.create_database(DB_NAME)
        self.one_type = None

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
        self.one_type = document['auth_type']

    def get_org_list(self):
        data = []
        for document in self.db:
            _id = document['_id']
            _org_name = re.search(r'one_drive_admin_([\w]+)_session', _id).group(1)
            data.append(_org_name)
        return data

    def install(self, **kwargs):
        app_data = self.one.get_ms_token(**kwargs)
        app_data['expires_time'] = int(time.time()) + 3500
        app_data['update_time'] = self.bj_dt

        if kwargs.get('auth_type') == 'oauth':
            data = self.one.fetch_token(**kwargs)
        else:
            data = app_data

        kwargs.update(data)
        kwargs['_id'] = f'one_drive_admin_{kwargs.get("org_name")}_session'
        kwargs['expires_time'] = int(time.time()) + 3500
        kwargs['update_time'] = self.bj_dt
        kwargs['app_data'] = app_data
        del kwargs['code']
        self.db.create_document(kwargs)

    def __getattr__(self, item):
        def call_back(*args, **kwargs):
            self.load(args[0], kwargs.get('app_token', False))
            func = getattr(self.one, item)
            if kwargs.get('app_token'):
                del kwargs['app_token']
            return func(*args[1:], **kwargs)

        return call_back


if __name__ == '__main__':
    admin = OneAdmin()
    uid = 'linbing01.sharepoint.com,b049b5fc-c8ea-440e-b49a-39cfa0eab7e3%2C9043205e-d8d9-443e-a033-d6dfdde78ee1'
    file_id = 'XIAOYU/DCC56843DDD3A722/0008.jpg'
    # print(admin.delete_file('linbing01', uid, file_id, site=True, app_token=True))
    data = admin.file_list('linbing01', uid, site=True, app_token=True, folder='taotu_image')
    print(json.dumps(data, indent=4))
