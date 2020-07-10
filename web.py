import os
import time

from flask import Flask, render_template
from flask_basicauth import BasicAuth

from config import *
from one_admin import OneAdmin

theme = 'default'
template_folder = f'themes/{theme}'
app = Flask(__name__, template_folder=template_folder, static_folder=template_folder)
app.secret_key = '8d9845a4-b6b6-11ea-87d2-acbc327cb9c7'
app.config['BASIC_AUTH_USERNAME'] = os.environ.get('ADMIN_NAME', ADMIN_NAME)
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', ADMIN_PASSWORD)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['APP_TITLE'] = 'OneAdmin'
basic_auth = BasicAuth(app)


@app.route('/')
@basic_auth.required
def index():
    return render_template('/layout.html')


@app.route('/<org_name>')
@basic_auth.required
def user(org_name):
    one_admin = OneAdmin()
    subscribed_list = one_admin.get_subscribed(org_name)
    users = one_admin.get_users(org_name)
    return render_template('/user.html', users=users, subscribed_list=subscribed_list, org_name=org_name)


@app.route('/<org_name>/<uid>/files')
@basic_auth.required
def file(org_name, uid):
    one_admin = OneAdmin()
    files = one_admin.file_list(org_name, uid, app_token=True)
    return render_template('/files.html', files=files, org_name=org_name)


@app.context_processor
def timestamp():
    return dict(t=time.time())


@app.context_processor
def get_org_list():
    return dict(org_list=OneAdmin.get_org_list())


@app.context_processor
def get_user_licenses():
    def get_licenses(sku_id):
        return LICENSES_MAP.get(sku_id, sku_id)

    return dict(get_licenses=get_licenses)


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.run(host='0.0.0.0', port=8080, debug=os.environ.get('DEBUG', DEBUG))
