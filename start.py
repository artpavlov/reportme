"""The entry point"""
from core.botLogger import log_main
from config import Config
from server import BackendServer

url = Config().base_url
if __name__ == "__main__":
    log_main.info('The server starts directly (local/development mode)')
    is_local = True
else:
    log_main.info('The server starts in uWSGI worker mode (production)')
    is_local = False

server = BackendServer(url, is_local=is_local)
app = server.getApp()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443)
