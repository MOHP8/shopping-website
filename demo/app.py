import logging
from app.routes.socket_io import socket_io_bp, socketio
from app import create_app

app = create_app()

if __name__ == '__main__':
    # app.logger.setLevel(logging.DEBUG)
    # app.run(debug=True)
    # app.run(debug=True, ssl_context=("nginx.crt", "nginx.key"))

    socketio.run(app, debug=True)