from __future__ import absolute_import

from eventlet import listen
from eventlet.wsgi import server

from . import app


server(listen(('', 8080)), app)
