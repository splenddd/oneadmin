import time
from datetime import timedelta

from flask import Flask, render_template

from common import get_accounts, get_users, LICENSES_MAP

theme = 'default'
template_folder = f'themes/{theme}'
app = Flask(__name__, template_folder=template_folder, static_folder=template_folder)


# data = one.refresh_token(**access)
# access['access_token'] = data['access_token']
# access['expires_time'] = int(time.time()) + 3500
# if data['refresh_token']:
#     access['refresh_token'] = data['refresh_token']
# access.save()


@app.route('/')
@app.route('/<account>')
def index(account=None):
    accounts = get_accounts()
    users = None
    if account:
        users = get_users(account)
    t = time.time()
    return render_template('index.html', accounts=accounts, account=account, users=users, t=t)


@app.context_processor
def get_user_licenses():
    def get_licenses(sku_id):
        return LICENSES_MAP.get(sku_id, sku_id)

    return dict(get_licenses=get_licenses)


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='127.0.0.1', port=8080, debug=True)
