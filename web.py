import os
import time

from flask import Flask, render_template, redirect, url_for, request, jsonify, g
from flask_basicauth import BasicAuth

from config import ADMIN_NAME, ADMIN_PASSWORD, LICENSES_MAP, DEBUG
from one_admin import OneAdmin

theme = 'default'
template_folder = f'themes/{theme}'
app = Flask(__name__, template_folder=template_folder, static_folder=template_folder)
app.secret_key = '8d9845a4-b6b6-11ea-87d2-acbc327cb9c7'
app.config['BASIC_AUTH_USERNAME'] = ADMIN_NAME
app.config['BASIC_AUTH_PASSWORD'] = ADMIN_PASSWORD
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['APP_TITLE'] = 'OneAdmin'
basic_auth = BasicAuth(app)
one_admin = OneAdmin()


@app.route('/')
@basic_auth.required
def index():
    return render_template('/layout.html')


@app.route('/install', methods=['GET', 'POST'])
@app.route('/install/<action>', methods=['POST'])
def install(action=None):
    if action == 'authorize':
        client_id = request.form.get('client_id')
        tenant_id = request.form.get('tenant_id')
        url = one_admin.authorize_url(client_id, tenant_id)
        return jsonify({'url': url})

    if request.method != 'POST':
        return render_template('/install.html')

    org_name = request.form.get('org')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    tenant_id = request.form.get('tenant_id')
    code = request.form.get('code')
    auth_type = request.form.get('auth_type')
    object_id = request.form.get('object_id')
    one_admin.install(org_name=org_name, object_id=object_id, client_id=client_id, client_secret=client_secret,
                      tenant_id=tenant_id,
                      code=code, auth_type=auth_type)
    return redirect('/')


@app.route('/env')
@basic_auth.required
def env():
    return jsonify(dict(os.environ))


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


@app.route('/<org_name>')
@basic_auth.required
def users(org_name):
    subscribed_list = one_admin.get_subscribed(org_name)
    g.one_type = one_admin.one_type
    _users = one_admin.get_users(org_name)
    return render_template('/user.html', users=_users, subscribed_list=subscribed_list, org_name=org_name)


@app.route('/<org_name>/<uid>/<action>', methods=['GET', 'POST'])
@basic_auth.required
def user_action(org_name, uid, action):
    if action == 'detail':
        user = one_admin.get_user(org_name, uid)
        return render_template('/user_detail.html', user=user, org_name=org_name)

    if action == 'disabled':
        return one_admin.enabled_user(org_name, uid, False)

    if action == 'enabled':
        return one_admin.enabled_user(org_name, uid, True)

    if action == 'add' and request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        one_admin.create_user(org_name, username=username, password=password)
        return redirect(url_for('users', org_name=org_name))

    return render_template('/create_user.html', org_name=org_name)


@app.route('/<org_name>/<drive>/<uid>/files')
@basic_auth.required
def files(org_name, uid, drive):
    site = drive == 'site'
    g.path = ['files']
    if site:
        g.path = ['sites', 'files']
    folder = request.args.get('folder', '').strip('/')
    _files = one_admin.file_list(org_name, uid, site=site, folder=folder, app_token=True)
    return render_template('/files.html', folder=folder, uid=uid, files=_files, org_name=org_name, drive=drive)


@app.route('/<org_name>/<drive>/<uid>/delete')
@basic_auth.required
def delete_file(org_name, uid, drive):
    site = drive == 'site'
    file_id = request.args.get('file_id').strip('/')
    one_admin.delete_file(org_name, uid, file_id, site=site, app_token=True)
    return redirect(url_for('files', uid=uid, drive=drive, org_name=org_name))


@app.route('/<org_name>/sites')
@basic_auth.required
def sites(org_name):
    _sites = one_admin.sites(org_name, app_token=True)
    g.path = ['sites']
    return render_template('/sites.html', sites=_sites, org_name=org_name)


@app.context_processor
def timestamp():
    return dict(t=time.time())


@app.context_processor
def get_org_list():
    return dict(org_list=one_admin.get_org_list())


@app.context_processor
def get_user_licenses():
    def get_licenses(sku_id):
        return LICENSES_MAP.get(sku_id, sku_id)

    return dict(get_licenses=get_licenses)


@app.context_processor
def get_file_size():
    def format_size(num):
        for unit in ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']:
            if abs(num) < 1024.0:
                return "%3.1f %s" % (num, unit)
            num /= 1024.0
        return "%.1f %s" % (num, 'YB')

    return dict(file_size=format_size)


@app.context_processor
def get_folder():
    def get_path(path, name):
        if not path:
            return name
        return f'{path}/{name}'.strip('/')

    return dict(get_folder=get_path)


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.run(host='0.0.0.0', port=8080, debug=DEBUG)
