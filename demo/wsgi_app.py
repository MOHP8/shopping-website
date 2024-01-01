
# cmd-> waitress-serve --host=0.0.0.0 --port=5000 "wsgi_app:app" 
# uwsgi --http :5000 --wsgi-file wsgi.py

import logging
from app.routes.socket_io import socket_io_bp, socketio
from app import create_app
# from waitress import serve

app = create_app()

# serve(app, host='0.0.0.0', port=5000)