from __future__ import absolute_import

import logging

from eventlet import listen
from eventlet.wsgi import server

from . import app


logging.basicConfig(level=logging.DEBUG)
server(listen(('', 8080)), app)
