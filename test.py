import json

from common import get_role, get_user, get_users

# redis_host = 'redis-17268.c15.us-east-1-4.ec2.cloud.redislabs.com'
# redis_pass = 'fVeShZqSdXdw8XytfCJy0Tbt7HU91Wac'
# redis_port = 17268
# redis = redis.Redis(redis_host, redis_port, password=redis_pass, socket_timeout=5, socket_connect_timeout=5)
# print(os.environ.get('ACCOUNT_NAME'))
# print(redis.set('test', str(uuid.uuid1()), 100))
# print(redis.get('test'))
# print(uuid.uuid1())
# users = get_users('linbing01')
# print(json.dumps(users, indent=4))


# _data = get_user('linbing01', '8626e523-1055-4c7f-af7c-453547573a68')
_data = get_users('linbing01')
print(json.dumps(_data, indent=4))
