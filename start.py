"""The entry point"""
from core.logger import log_main
# from config import Config
from server import BackendServer


if __name__ == "__main__":
    log_main.info('The server starts directly (local/development mode)')
    is_local = True
else:
    log_main.info('The server starts in uWSGI worker mode (production)')
    is_local = False

server = BackendServer(is_local=is_local)
app = server.get_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443)
