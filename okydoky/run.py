""":mod:`okydoky.run` --- Main script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import absolute_import

import logging
import optparse
import os.path

from eventlet import listen
from eventlet.wsgi import server
from werkzeug.contrib.fixers import ProxyFix

from .app import REQUIRED_CONFIGS, app


parser = optparse.OptionParser()
parser.add_option('-H', '--host', default='0.0.0.0',
                  help='hostname to listen [%default]')
parser.add_option('-p', '--port', type='int', default=8080,
                  help='port to listen [%default]')
parser.add_option('--proxy-fix', action='store_true', default=False,
                  help='forward X-Forwared-* headers to support HTTP '
                       'reverse proxies e.g. nginx, lighttpd')
parser.add_option('--force-https', action='store_true', default=False,
                  help='redirect all HTTP requests to HTTPS locations')
parser.add_option('-d', '--debug', action='store_true',
                  help='debug mode')
parser.add_option('-q', '--quiet', action='store_const', const=logging.ERROR,
                  dest='verbosity', help='suppress output')
parser.add_option('-v', '--verbose', action='store_const', const=logging.INFO,
                  dest='verbosity', help='enable additional output')
parser.add_option('--noisy', action='store_const', const=logging.DEBUG,
                  dest='verbosity', help='be noisy')


def main(*args, **kwargs):
    options, args = parser.parse_args(*args, **kwargs)
    if not args:
        parser.error('missing config file')
    elif len(args) > 1:
        parser.error('too many arguments')
    elif not os.path.isfile(args[0]):
        parser.error(args[0] + ' does not exist')
    config_file = os.path.abspath(args[0])
    debug = options.debug
    level = options.verbosity or (logging.DEBUG if debug else logging.WARNING)
    logging.basicConfig(level=level)
    app.debug = debug
    app.config.from_pyfile(config_file)
    for conf in REQUIRED_CONFIGS:
        if conf not in app.config:
            parser.error('missing config: ' + conf)
    if options.force_https:
        app.wsgi_app = ForcingHTTPSMiddleware(app.wsgi_app)
    if options.proxy_fix:
        app.wsgi_app = ProxyFix(app.wsgi_app)
    server(listen((options.host, options.port)), app)


class ForcingHTTPSMiddleware(object):
    """It redirects all non-HTTPS requests to HTTPS locations."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ['wsgi.url_scheme'] != 'https':
            qs = environ.get('QUERY_STRING', '')
            url = 'https://{0}{1}{2}'.format(
                environ['HTTP_HOST'],
                environ['PATH_INFO'],
                qs and '?' + qs
            )
            start_response('301 Moved Permanently', [
                ('Location', url),
                ('Content-Type', 'text/plain; charset=utf-8')
            ])
            return ['Redirecting to ', url, '...']
        return self.app(environ, start_response)


if __name__ == '__main__':
    main()
