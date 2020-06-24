import json
import logging
import random
import string
from urllib.parse import urlencode

import requests


class OneDrive:

    def __init__(self):
        self._api_base_url = 'https://graph.microsoft.com/v1.0/'
        self.http = requests.session()
        self._auth_url = 'https://login.microsoftonline.com/{}/oauth2/v2.0/authorize'
        self._token_url = 'https://login.microsoftonline.com/{}/oauth2/v2.0/token'
        self._drive_access = {}
        self._redirect_uri = 'https://py-index.github.io'
        self._auth_type = 'oauth'
        self._scope = 'offline_access Sites.ReadWrite.All Directory.ReadWrite.All Directory.AccessAsUser.All'
        self.logger = logging.getLogger(self.__class__.__name__)

    def api(self, api_sub_url, params=None, data=None, method=None, **kwargs):
        self.http.headers['Authorization'] = "Bearer {}".format(self._drive_access.get('access_token'))

        if api_sub_url.find('http') == -1:
            url = '{}/{}'.format(self._api_base_url.strip('/'), api_sub_url.strip('/'))
        else:
            url = api_sub_url
        response = self.fetch(url, data=data, method=method, params=params, **kwargs)
        if len(response.content) > 1:
            return response.json()
        return {'status_code': response.status_code}

    def api_debug(self, api_sub_url, params=None, data=None, method=None, **kwargs):
        return json.dumps(self.api(api_sub_url, params, data, method, **kwargs), indent=4)

    def enabled_user(self, user, password=None):
        post_data = {
            'accountEnabled': True,
            'usageLocation': 'HK',
        }
        if self._auth_type == 'oauth':
            if not password:
                password = random.choices(string.ascii_letters + string.digits + '!#$%&()*+-/:;<=>?@', k=10)
            post_data['passwordProfile'] = {
                'password': password,
                'forceChangePasswordNextSignIn': False
            }
            post_data['passwordPolicies'] = 'DisablePasswordExpiration, DisableStrongPassword'

        return self.api(f'/users/{user}', json=post_data, method='PATCH')

    def create_user(self, **kwargs):
        _subscribed = random.choice(self.get_subscribed())
        domain = self.get_default_domain()
        password = kwargs.get('password', ''.join(
            random.choices(string.ascii_letters + string.digits + '!#$%&()*+-/:;<=>?@', k=10)))
        user_name = kwargs.get('user_name', ''.join(random.choices(string.ascii_letters, k=6)))
        user_email = f'{user_name}@{domain}'
        post_data = {
            'accountEnabled': True,
            'displayName': user_name,
            'mailNickname': user_name,
            'passwordPolicies': 'DisablePasswordExpiration, DisableStrongPassword',
            'passwordProfile': {
                'password': password,
                'forceChangePasswordNextSignIn': False
            },
            'userPrincipalName': user_email,
            'usageLocation': 'HK'
        }
        data = self.api('/users', json=post_data, method='POST')
        print(f'{user_email}: {password} 创建完成.')
        if _subscribed and _subscribed.get('sku_id'):
            self._assign_license(user_email, _subscribed['sku_id'])
            print(f'{user_email}: 分配订阅完成.')
        return data

    def _assign_license(self, user_email, sku_id, **kwargs):
        api = f'/users/{user_email}/assignLicense'
        post_data = {
            'addLicenses': [
                {
                    'disabledPlans': [],
                    'skuId': sku_id
                }
            ],
            'removeLicenses': []
        }
        return self.api(api, json=post_data)

    def get_default_domain(self, **kwargs):
        data = self.api('/domains')
        for item in data['value']:
            if item.get('isDefault'):
                return item.get('id')
        return None

    def get_domains(self, **kwargs):
        return self.api('/domains')

    def get_subscribed(self):
        subscribed_list = self.api('/subscribedSkus')
        result = []
        for i in subscribed_list['value']:
            result.append({'status': i['capabilityStatus'], 'sku_id': i['skuId'],
                           'units': f'{i["consumedUnits"]}/{i["prepaidUnits"]["enabled"]}'})
        return result

    def get_users(self, **kwargs):
        params = {'$select': 'id,displayName,accountEnabled,userPrincipalName,assignedLicenses'}
        params.update(kwargs)
        return self.api('/users', params=params)

    def delete_user(self, user):
        return self.api(f'/users/{user}', method='DELETE')

    def get_disabled_users(self):
        return self.get_users(filter='accountEnabled eq false')

    def get_ms_token(self, **kwargs):
        tenant_id = kwargs.get('tenant_id')
        url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
        post_data = {
            'grant_type': 'client_credentials',
            'client_id': kwargs.get('client_id'),
            'client_secret': kwargs.get('client_secret'),
            'scope': 'https://graph.microsoft.com/.default'
        }
        return self.fetch(url, data=post_data).json()

    def authorize_url(self, **kwargs):
        default_params = {
            'client_id': kwargs.get('client_id'),
            'redirect_uri': self._redirect_uri,
            'response_type': 'code',
            'state': 'debug',
            'scope': self._scope,
            'prompt': 'consent'
        }
        return '{}?{}'.format(self._auth_url.format(kwargs.get('tenant_id')), urlencode(default_params, doseq=True))

    def fetch_token(self, **kwargs) -> dict:
        default_params = {
            'client_id': kwargs.get('client_id'),
            'redirect_uri': self._redirect_uri,
            'client_secret': kwargs.get('client_secret'),
            'grant_type': 'authorization_code',
            'scope': self._scope,
            'code': kwargs.get('code'),
        }
        return self.fetch(self._token_url.format(kwargs.get('tenant_id')), default_params).json()

    def refresh_token(self, **kwargs) -> dict:
        default_params = {
            'client_id': kwargs.get('client_id'),
            'redirect_uri': kwargs.get('redirect_uri'),
            'client_secret': kwargs.get('client_secret'),
            'grant_type': 'refresh_token',
            'scope': kwargs.get('scope'),
            'refresh_token': kwargs.get('refresh_token'),
        }
        return self.fetch(self._token_url.format(kwargs.get('tenant_id')), default_params).json()

    def fetch(self, url, data=None, method=None, **kwargs):
        kwargs.setdefault('timeout', 30)
        if (data or kwargs.get('json')) and method is None:
            method = 'POST'

        if method is None:
            method = 'GET'
        response = self.http.request(method, url, data=data, **kwargs)
        if response.ok:
            return response

        result = response.json()
        raise Exception(response.url, response.status_code, result['error']['message'])


if __name__ == '__main__':
    main()
