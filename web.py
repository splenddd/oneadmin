import os
import time

from flask import Flask, render_template, redirect, request, session, jsonify
from flask_basicauth import BasicAuth

from common import get_users, LICENSES_MAP, enabled_user, get_user, create_user, delete_user, get_users_page, \
    get_accounts

theme = 'default'
template_folder = f'themes/{theme}'
app = Flask(__name__, template_folder=template_folder, static_folder=template_folder)
app.secret_key = '8d9845a4-b6b6-11ea-87d2-acbc327cb9c7'
app.config['BASIC_AUTH_USERNAME'] = 'root'
app.config['BASIC_AUTH_PASSWORD'] = 'hack3321'
basic_auth = BasicAuth(app)


@app.route('/install')
def install():
    return render_template('install.html')


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


@app.route('/<account>/<uid>/<action>')
@basic_auth.required
def user_action(account, uid, action):
    if action == 'detail':
        return get_user(account, uid)
    if action == 'delete':
        return delete_user(account, uid)
    if action == 'role':
        return delete_user(account, uid)
    status = True if action == 'enabled' else False
    return enabled_user(account, uid, status)


@app.route('/')
@app.route('/<account>')
@app.route('/<account>/<page>')
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
        return render_template(f'/index.html', users=users, account=account, accounts=accounts)
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
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['APP_TITLE'] = 'OneAdmin'
    app.run(host='0.0.0.0', port=8080)
