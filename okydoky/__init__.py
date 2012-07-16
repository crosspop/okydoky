""":mod:`okydoky` --- Okydoky docs builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import os.path

from eventlet.green import urllib2
from flask import (Flask, current_app, redirect, request, render_template,
                   url_for)
from werkzeug.urls import url_decode, url_encode


app = Flask(__name__)


def open_file(filename, mode='r', config=None):
    config = config or current_app.config
    save_path = config['SAVE_DIRECTORY']
    if not os.path.isdir(save_path):
        os.makedirs(save_path)
    return open(os.path.join(save_path, filename), mode)


def open_token_file(mode='r', config=None):
    return open_file('token.txt', mode)


def get_token(config=None):
    config = config or current_app.config
    try:
        token = config['ACCESS_TOKEN']
    except KeyError:
        try:
            with open_token_file(config=config) as f:
                token = f.read().strip()
        except IOError:
            return None
        config['ACCESS_TOKEN'] = token
    return token


def open_head_file(mode='r', config=None):
    return open_file('head.txt', mode)


def get_head(config=None):
    try:
        with open_head_file(config=config) as f:
            return f.read().strip()
    except IOError:
        pass


@app.route('/')
def home():
    token = get_token()
    if token is None:
        return render_template('home.html', login_url=url_for('auth_redirect'))
    head = get_head()
    if head is None:
        hook_url = url_for('post_receive_hook', _external=True)
        return render_template('empty.html', hook_url=hook_url)
    return token + '\n' + token


@app.route('/auth/1')
def auth_redirect():
    params = {
        'client_id': current_app.config['CLIENT_ID'],
        'redirect_uri': url_for('auth', _external=True),
        'scope': 'repo'
    }
    return redirect('https://github.com/login/oauth/authorize?' +
                    url_encode(params))


@app.route('/auth/2')
def auth():
    params = {
        'client_id': current_app.config['CLIENT_ID'],
        'client_secret': current_app.config['CLIENT_SECRET'],
        'redirect_uri': url_for('auth', _external=True),
        'code': request.args['code'],
        'state': request.args['state']
    }
    response = urllib2.urlopen(
        'https://github.com/login/oauth/access_token',
        url_encode(params)
    )
    auth_data = url_decode(response.read())
    response.close()
    token = auth_data['access_token']
    with open_token_file('w') as f:
        f.write(token)
    current_app.config['ACCESS_TOKEN'] = token
    return redirect(url_for('home'))
