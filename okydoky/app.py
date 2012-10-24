""":mod:`okydoky.app` --- Web hook
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import base64
import datetime
import functools
import hashlib
import hmac
import logging
import os
import os.path
import re
import shutil
import subprocess
import sys
import tarfile
import time

from eventlet import spawn_n
from eventlet.green import urllib2
from eventlet.greenpool import GreenPool
from flask import (Flask, abort, current_app, json, make_response, redirect,
                   request, render_template, session, url_for)
from flask.helpers import send_from_directory
from iso8601 import parse_date
from virtualenv import create_environment
from werkzeug.urls import url_decode, url_encode


REQUIRED_CONFIGS = ('REPOSITORY', 'CLIENT_ID', 'CLIENT_SECRET',
                    'SAVE_DIRECTORY', 'SECRET_KEY')
EXPIRES = datetime.timedelta(minutes=5)

app = Flask(__name__)


def open_file(filename, mode='r', config=None):
    config = config or current_app.config
    save_path = config['SAVE_DIRECTORY']
    if not os.path.isdir(save_path):
        os.makedirs(save_path)
    return open(os.path.join(save_path, filename), mode)


def open_token_file(mode='r', config=None):
    return open_file('token.txt', mode, config=config)


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
    return open_file('head.txt', mode, config=config)


def get_head(config=None):
    try:
        with open_head_file(config=config) as f:
            return f.read().strip()
    except IOError:
        pass


def ensure_login():
    logger = logging.getLogger(__name__ + '.ensure_login')
    try:
        login = session['login']
    except KeyError:
        session.pop('access', None)
        back = base64.urlsafe_b64encode(request.url)
        params = {
            'client_id': current_app.config['CLIENT_ID'],
            'redirect_uri': url_for('auth', back=back, _external=True),
            'scope': 'repo'
        }
        return redirect('https://github.com/login/oauth/authorize?' +
                        url_encode(params))
    logger.debug('login = %r', login)
    try:
        auth, ltime = session['access']
    except (KeyError, ValueError):
        auth = False
        ltime = None
    if ltime is None or ltime < datetime.datetime.utcnow() - EXPIRES:
        repo_name = current_app.config['REPOSITORY']
        # user repos
        response = urllib2.urlopen(
            'https://api.github.com/user/repos?access_token=' +
            login
        )
        repo_dicts = json.load(response)
        response.close()
        repos = frozenset(repo['full_name'] for repo in repo_dicts)
        logger.debug('repos = %r', repos)
        auth = repo_name in repos
        # org repos
        if not auth:
            url = 'https://api.github.com/orgs/{0}/repos?access_token={1}'
            try:
                response = urllib2.urlopen(
                    url.format(repo_name.split('/', 1)[0], login)
                )
            except IOError:
                auth = False
            else:
                repo_dicts = json.load(response)
                response.close()
                org_repos = frozenset(repo['full_name'] for repo in repo_dicts)
                logger.debug('org_repos = %r', org_repos)
                auth = repo_name in org_repos
        session['access'] = auth, datetime.datetime.utcnow()
    if not auth:
        abort(403)
    logger.debug('auth = %r', auth)


@app.route('/')
def home():
    token = get_token()
    if token is None:
        return render_template('home.html', login_url=url_for('auth_redirect'))
    redirect = ensure_login()
    if redirect:
        return redirect
    head = get_head()
    if head is None:
        hook_url = url_for('post_receive_hook', _external=True)
        return render_template('empty.html', hook_url=hook_url)
    save_dir = current_app.config['SAVE_DIRECTORY']
    refs = {}
    time_fmt = '%Y-%m-%dT%H:%M:%SZ'
    build_logs = {}
    for name in os.listdir(save_dir):
        if re.match(r'^[A-Fa-f0-9]{40}$', name):
            fullname = os.path.join(save_dir, name)
            stat = os.stat(fullname)
            refs[name] = time.strftime(time_fmt, time.gmtime(stat.st_mtime))
            build_logs[name] = os.path.isfile(
                os.path.join(fullname, 'build.txt')
            )
    return render_template('list.html',
                           head=head, refs=refs, build_logs=build_logs)


@app.route('/<ref>/', defaults={'path': 'index.html'})
@app.route('/<ref>/<path:path>')
def docs(ref, path):
    if ref == 'head':
        ref = get_head()
        if ref is None:
            abort(404)
    elif not re.match(r'^[A-Fa-f0-9]{7,40}$', ref):
        abort(404)
    redirect = ensure_login()
    if redirect:
        return redirect
    save_dir = current_app.config['SAVE_DIRECTORY']
    if len(ref) < 40:
        for candi in os.listdir(save_dir):
            if (os.path.isdir(os.path.join(save_dir, candi)) and
                candi.startswith(ref)):
                return redirect(url_for('docs', ref=candi, path=path))
        abort(404)
    return send_from_directory(save_dir, os.path.join(ref, path))


def get_oauth_state():
    return hmac.new(current_app.secret_key, request.remote_addr, hashlib.sha1)


@app.route('/auth')
def auth_redirect():
    params = {
        'client_id': current_app.config['CLIENT_ID'],
        'redirect_uri': url_for('auth', _external=True),
        'scope': 'repo',
        'state': get_oauth_state()
    }
    return redirect('https://github.com/login/oauth/authorize?' +
                    url_encode(params))


@app.route('/auth/finalize')
def auth():
    try:
        back = request.args['back']
    except KeyError:
        redirect_uri = url_for('auth', _external=True)
        initial = True
    else:
        redirect_uri = url_for('auth', back=back, _external=True)
        initial = False
    params = {
        'client_id': current_app.config['CLIENT_ID'],
        'client_secret': current_app.config['CLIENT_SECRET'],
        'redirect_uri': redirect_uri,
        'code': request.args['code'],
        'state': get_oauth_state()
    }
    response = urllib2.urlopen(
        'https://github.com/login/oauth/access_token',
        url_encode(params)
    )
    auth_data = url_decode(response.read())
    response.close()
    token = auth_data['access_token']
    if initial:
        with open_token_file('w') as f:
            f.write(token)
        current_app.config['ACCESS_TOKEN'] = token
        return_url = url_for('home')
    else:
        return_url = base64.urlsafe_b64decode(str(back))
    session['login'] = token
    return redirect(return_url)


@app.route('/', methods=['POST'])
def post_receive_hook():
    payload = json.loads(request.form['payload'])
    commits = payload['commits']
    commits.sort(key=lambda commit: parse_date(commit['timestamp']))
    ids = [(commit['id'], url_for('docs', ref=commit['id'], _external=True))
           for commit in commits]
    spawn_n(build_main, ids, dict(current_app.config))
    response = make_response('true', 202)
    response.mimetype = 'application/json'
    return response


def build_main(commits, config):
    logger = logging.getLogger(__name__ + '.build_main')
    logger.info('triggered with %d commits', len(commits))
    logger.debug('commits = %r', commits)
    token = get_token(config)
    pool = GreenPool()
    commit_map = dict(commits)
    commit_ids = [commit_id for commit_id, _ in commits]
    results = pool.imap(
        functools.partial(download_archive, token=token, config=config),
        commit_ids
    )
    env = make_virtualenv(config)
    save_dir = config['SAVE_DIRECTORY']
    complete_hook = config.get('COMPLETE_HOOK')
    for commit, filename in results:
        working_dir = extract(filename, save_dir)
        try:
            build = build_sphinx(working_dir, env)
        except Exception:
            permalink = commit_map[commit]
            if not config.get('RECREATE_VIRTUALENV'):
                env = make_virtualenv(config, recreate=True)
                try:
                    build = build_sphinx(working_dir, env)
                except Exception:
                    if callable(complete_hook):
                        complete_hook(commit, permalink, sys.exc_info())
                    continue
            if callable(complete_hook):
                complete_hook(commit, permalink, sys.exc_info())
            continue
        result_dir = os.path.join(save_dir, commit)
        shutil.move(build, result_dir)
        logger.info('build complete: %s' % result_dir)
        if callable(complete_hook):
            complete_hook(commit, commit_map[commit], None)
        shutil.rmtree(working_dir)
        logger.info('working directory %s has removed' % working_dir)
        with open_head_file('w', config=config) as f:
            f.write(commit)
    logger.info('new head: %s', commits[0])


def download_archive(commit, token, config):
    logger = logging.getLogger(__name__ + '.download_archive')
    logger.info('start downloading archive %s', commit)
    url_p = 'https://api.github.com/repos/{0}/tarball/{1}?access_token={2}'
    url = url_p.format(config['REPOSITORY'], commit, token)
    while 1:
        response = urllib2.urlopen(url)
        try:
            url = response.info()['Location']
        except KeyError:
            break
    filename = os.path.join(config['SAVE_DIRECTORY'], commit + '.tar.gz')
    logger.debug('save %s into %s', commit, filename)
    logger.debug('filesize of %s: %s',
                 filename, response.info()['Content-Length'])
    with open(filename, 'wb') as f:
        while 1:
            chunk = response.read(4096)
            if chunk:
                f.write(chunk)
                continue
            break
    logger.info('finish downloading archive %s: %s', commit, filename)
    return commit, filename


def extract(filename, path):
    logger = logging.getLogger(__name__ + '.extract')
    logger.info('extracting %s...', filename)
    tar = tarfile.open(filename)
    logger.debug('tar.getnames() = %r', tar.getnames())
    dirname = tar.getnames()[0]
    tar.extractall(path)
    result_path = os.path.join(path, dirname)
    logger.info('%s has extracted to %s', filename, result_path)
    os.unlink(filename)
    logger.info('%s has removed', filename)
    return result_path


def build_sphinx(path, env):
    logger = logging.getLogger(__name__ + '.build_sphinx')
    logs = []
    def run(cmd, **kwargs):
        command = ' '.join(map(repr, cmd))
        logger.debug(command)
        logs.append('$ ' + command)
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                         **kwargs)
        logs.append(result)
    if sys.platform == 'win32':
        bindir = os.path.join(env, 'Scripts')
    else:
        bindir = os.path.join(env, 'bin')
    python = os.path.join(bindir, 'python')
    env = os.environ.copy()
    env['OKYDOKY'] = '1'
    logger.info('installing dependencies...')
    run([python, 'setup.py', 'develop', '--upgrade'], cwd=path, env=env)
    logger.info('installing Sphinx...')
    run([os.path.join(bindir, 'easy_install'), 'Sphinx'])
    logger.info('building documentation using Sphinx...')
    run([python, 'setup.py', 'build_sphinx'], cwd=path, env=env)
    run([python, 'setup.py', 'develop', '--uninstall'], cwd=path)
    build = os.path.join(path, 'build', 'sphinx', 'html')
    with open(os.path.join(build, 'build.txt'), 'w') as log_file:
        for log_line in logs:
            print >> log_file, log_line
    logger.info('documentation: %s', build)
    return build


def make_virtualenv(config, recreate=False):
    logger = logging.getLogger(__name__ + '.make_virtualenv')
    save_dir = config['SAVE_DIRECTORY']
    envdir = os.path.join(save_dir, '_env')
    if os.path.isdir(envdir):
        if not config.get('RECREATE_VIRTUALENV', recreate):
            logger.info('virtualenv already exists: %s; skip...' % envdir)
            return envdir
        logger.info('virtualenv already exists: %s; remove...' % envdir)
        shutil.rmtree(envdir)
    logger.info('creating new virtualenv: %s' % envdir)
    create_environment(envdir, use_distribute=True)
    logger.info('created virtualenv: %s' % envdir)
    return envdir
