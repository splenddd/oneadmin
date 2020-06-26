import os
import time

from flask import Flask, render_template, redirect, request, session, jsonify
from flask_basicauth import BasicAuth

from common import get_users, LICENSES_MAP, enabled_user, get_user, create_user, delete_user, get_users_page, \
    get_accounts, install_admin, authorize_url, get_subscribed, get_files, delete_file, get_file
from config import ADMIN_NAME, ADMIN_PASSWORD, DEBUG

theme = 'default'
template_folder = f'themes/{theme}'
app = Flask(__name__, template_folder=template_folder, static_folder=template_folder)
app.debug = os.environ.get('DEBUG', DEBUG)
app.secret_key = '8d9845a4-b6b6-11ea-87d2-acbc327cb9c7'
app.config['BASIC_AUTH_USERNAME'] = os.environ.get('ADMIN_NAME', ADMIN_NAME)
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', ADMIN_PASSWORD)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['APP_TITLE'] = 'OneAdmin'
basic_auth = BasicAuth(app)


@app.route('/install/authorize', methods=['POST'])
def run_install_authorize():
    client_id = request.form.get('client_id')
    tenant_id = request.form.get('tenant_id')
    url = authorize_url(client_id, tenant_id)
    return jsonify({'url': url})


@app.route('/install', methods=['GET', 'POST'])
def run_install():
    if request.method.lower() == 'get':
        return render_template('install.html')

    org = request.form.get('org')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    tenant_id = request.form.get('tenant_id')
    code = request.form.get('code')
    auth_type = request.form.get('auth_type')
    object_id = request.form.get('object_id')
    install_admin(org=org, object_id=object_id, client_id=client_id, client_secret=client_secret, tenant_id=tenant_id,
                  code=code, auth_type=auth_type)
    return redirect('/')


@app.route('/debug')
@basic_auth.required
def debug():
    return jsonify(dict(os.environ))


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


@app.route('/<account>/add', methods=['GET', 'POST'])
@basic_auth.required
def add_action(account):
    if request.method.lower() == 'get':
        return render_template('create_user.html', account=account)

    username = request.form.get('username')
    password = request.form.get('password')
    create_user(account, username, password)
    return redirect(f'/{account}')


@app.route('/<account>/<uid>/file/<file_id>/<action>')
@basic_auth.required
def file_action(account, uid, file_id, action):
    if action == 'delete':
        return delete_file(account, uid, file_id)
    if action == 'view':
        return get_file(account, uid, file_id)
    return redirect(f'/{account}')


@app.route('/<account>/<uid>/<action>')
@basic_auth.required
def user_action(account, uid, action):
    if action == 'detail':
        return render_template('user.html', user=get_user(account, uid))
    if action == 'delete':
        return delete_user(account, uid)
    if action == 'role':
        return delete_user(account, uid)
    if action == 'files':
        files = get_files(account, uid)
        print(files)
        return render_template('files.html', account=account, uid=uid, files=files)
    status = True if action == 'enabled' else False
    return enabled_user(account, uid, status)


@app.route('/')
@app.route('/<account>')
@app.route('/<account>/<page>')
@basic_auth.required
def index(account=None, page=None):
    accounts = get_accounts()
    if accounts and len(accounts):
        _account = accounts[0]
        if not account:
            return redirect(f'/{_account}')

        if not page:
            users = get_users(account)
        else:
            users = get_users_page(account, session[f'{account}_next_page'])
        if users and users.get('@odata.nextLink'):
            session[f'{account}_next_page'] = users['@odata.nextLink']

        subscribed_list = get_subscribed(account)
        return render_template(f'/index.html', subscribed_list=subscribed_list, users=users, account=account,
                               accounts=accounts)
    return redirect('/install')


@app.context_processor
def timestamp():
    return dict(t=time.time())


@app.context_processor
def get_user_licenses():
    def get_licenses(sku_id):
        return LICENSES_MAP.get(sku_id, sku_id)

    return dict(get_licenses=get_licenses)


if __name__ == '__main__':
    app.jinja_env.auto_reload = True

    app.run(host='0.0.0.0', port=8080)
