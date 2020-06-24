import json

from common import get_accounts, get_users, LICENSES_MAP

users = get_users('linbing01')
print(json.dumps(users, indent=4))
