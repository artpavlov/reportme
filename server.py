import sys
import telebot
import flask

from config import Config

from core.botLogger import log_main
from core.botStream import Streams, StreamStatus
from core.botDatabase import Database


class BackendServer:
    '''Backend server'''
    def __init__(self, base_url, is_local=None):
        self.__base_url = base_url
        self.__webhook_path = Config().webhook_path
        self.__webhook_url = "%s%s" % (base_url, self.__webhook_path)
        self.__is_local = is_local
        self.__bot_token = Config().bot_token

        log_main.info("Starting BackendServer…")
        # Some debug info (for local dev mode )
        if is_local:
            print("Base URL: %s" % self.__base_url)
            print("Webhook URL: %s" % self.__webhook_url)
            print("Bot token: %s" % self.__bot_token)

        # Initializing Flask
        self.init_flask()

        # Checking and initializing the database connection
        status, description = Database.checkConnection(Config().db_host, Config().db_user, Config().db_password, Config().db_database)
        if not status:
            msg = "Database connect failed\n%s" % description
            self._flask_app.logger.error(msg) # pylint: disable=no-member
            log_main.error(msg)
            sys.exit()
        Database(Config().db_host, Config().db_user, Config().db_password, Config().db_database)

        # Init streams
        log_main.info("Loading streams…")
        Streams()
        log_main.info("Streams loaded")

        # Init telebot
        self.init_telebot()


    def getApp(self):
        '''Get Flask application'''
        return self._flask_app


    def init_flask(self):
        '''Init URL handling'''
        self._flask_app = flask.Flask(__name__)#, template_folder=os.path.join("server", "templates"), static_folder=os.path.join("server", "static"))

        reporter = flask.Blueprint('reporter', __name__)

        @reporter.route('/', methods=['POST'])
        def _webhook(): # pylint: disable=inconsistent-return-statements
            if flask.request.headers.get('content-type') == 'application/json':
                json_string = flask.request.get_data().decode('utf-8')
                log_main.debug("Recieved JSON;%s", json_string)
                return self._processWebhook(json_string)
            log_main.warning('Content type "application/json" expected')
            flask.abort(403)

        @reporter.route('/send/<secret>/<message>', methods=['GET'])
        def _handle_send_get(secret, message):
            stream = Streams().get(secret)
            if stream is not None:
                fullname = "%s (%s)" % (secret, stream.name) if stream.name else secret
                if stream.status == StreamStatus.active:
                    name = "%s: " % stream.name if stream.name else ""
                    self._bot.send_message(stream.user_id, "%s%s" % (name, message))
                    log_main.info("SEND to %s: %s", fullname, message)
                elif stream.status == StreamStatus.stopped:
                    log_main.info("IGNORED (stopped) to %s: %s", fullname, message)
                else:
                    log_main.info("IGNORED (unknown) to %s: %s", fullname, message)
            else:
                log_main.info("Attempt to send to a nonexistent stream: %s", secret)
            return 'ok' # Always return ok

        @reporter.route('/send/', methods=['POST'])
        def _handle_send_post():
            secret = flask.request.form.get('secret', '')
            message = flask.request.form.get('message', '')
            return _handle_send_get(secret, message)

        # Register blueprint decorator if path specified
        if self.__webhook_path:
            self._flask_app.register_blueprint(reporter, url_prefix=self.__webhook_path)
        else:
            self._flask_app.register_blueprint(reporter)


    def init_telebot(self):
        '''Setup telebot handlers'''
        self._bot = telebot.TeleBot(self.__bot_token, threaded=False)
        if self._bot is None:
            log_main.warning("Bot start failed")

        self.__setWebhook()

        @self._bot.message_handler(commands=['start', 'help'])
        def _handle_start(tmessage):
            self.handle_start(tmessage)

        @self._bot.message_handler(commands=['add'])
        def _handle_add(tmessage):
            self.handle_add(tmessage)

        @self._bot.message_handler(commands=['del'])
        def _handle_del(tmessage):
            self.handle_del(tmessage)

        @self._bot.message_handler(commands=['list'])
        def _handle_list(tmessage):
            self.handle_list(tmessage)

        @self._bot.message_handler(commands=['info'])
        def _handle_info(tmessage):
            self.handle_info(tmessage)

        @self._bot.message_handler(commands=['run'])
        def _handle_run(tmessage):
            self.handle_run(tmessage)

        @self._bot.message_handler(commands=['stop'])
        def _handle_stop(tmessage):
            self.handle_stop(tmessage)


    def __setWebhook(self):
        '''Set webhook for telebot'''
        try:
            # Remove old webhook
            self._bot.remove_webhook()
            # Set new webhook
            if self._bot.set_webhook(url=self.__webhook_url):
                log_main.debug("Webhook for telegram bot is set: %s", self.__webhook_url)
                return True
            log_main.error("Error when installing webhook for telegram bot")
            return False
        except telebot.apihelper.ApiException as e:
            log_main.warning("Exception when installing webhook for telegram bot: %s", e)
            return False


    def _processWebhook(self, json_string):
        '''Handle webhook messages from telegram bot
            Args:
                json_string(str):   A string containing JSON data
        '''
        try:
            update = telebot.types.Update.de_json(json_string)
            self._bot.process_new_updates([update])
        except telebot.apihelper.ApiException as e:
            log_main.warning('Exception when processing webhook: %s', e)
        return 'ok'


    def __getStreamLink(self, secret):
        return flask.url_for("reporter._handle_send_get", secret=secret, message="your-custom-message", _external=True)


    def handle_start(self, tmessage):
        '''Handle /start command.
            If this is the first request of a person to the bot, then create new user
        '''
        user_id = str(tmessage.from_user.id)
        log_main.debug("/start for user %s", user_id)

        message = "This bot provide you a simple way to produce reasonably insecure notifications. You can notify yourself by making custom HTTP request with the KEY and message provided:"
        message += "\n1) Add new notification stream (/add)"
        message += "\n2) Copy your personal Link (/info)"
        message += "\n3) Use this Link with your message"

        message += "\n\n*Commands List:*"
        message += "\n`/add NAME` _Add stream_"
        message += "\n`/del KEY` _Delete stream_"
        message += "\n`/list` _List all your streams_"
        message += "\n`/info KEY` _Info about stream_"
        message += "\n`/run KEY` _Run stream_"
        message += "\n`/stop KEY` _Stop stream_"

        self._bot.send_message(user_id, message, parse_mode="Markdown")


    def handle_add(self, tmessage):
        '''Handle /add command'''
        user_id = str(tmessage.from_user.id)
        stream_name = tmessage.text[4:].strip()

        if len(stream_name) == 0:
            self._bot.send_message(user_id, "Enter stream name in command: `/add NAME`", parse_mode="Markdown")

        secret = Streams().add(user_id, stream_name)

        if not secret:
            self._bot.send_message(user_id, "*Failed to add new stream!*\nPlease, try again later…", parse_mode="Markdown")
            return

        link = self.__getStreamLink(secret)
        message = "*New stream has been created:* %s\n*Key:* %s\n*Link:* %s" % (stream_name, secret, link)
        self._bot.send_message(user_id, message, parse_mode="Markdown", disable_web_page_preview=True)


    def handle_del(self, tmessage):
        '''Handle /del command'''
        user_id = str(tmessage.from_user.id)
        secret = tmessage.text[4:].strip()

        # Get a stream for selected user
        stream = self.__getStreamByKey(user_id, secret, "/del")
        if stream is None:
            return

        result = Streams().delete(secret)
        if not result:
            self._bot.send_message(user_id, "*Failed to delete stream!* Try again later…", parse_mode="Markdown")
        self._bot.send_message(user_id, "*Stream has been deleted.*\n%s" % secret, parse_mode="Markdown")


    def handle_list(self, tmessage):
        '''Handle /list command'''
        user_id = str(tmessage.from_user.id)
        #print("user_id: %s (%s)" % (user_id, type(user_id)))
        streams = Streams().getAll(user_id)

        if len(streams) > 0:
            message = "Your streams list:"
            for stream in streams:
                status = "⚪️"
                if stream.status == StreamStatus.active:
                    status = "🟢"
                elif stream.status == StreamStatus.stopped:
                    status = "🔴"
                message += "\n " + status + " *" + stream.name + ":* " + stream.secret
        else:
            message = "*You have no streams yet\.*"

        message += "\n\n`/add NAME` _Add stream_"
        message += "\n`/del KEY` _Delete stream_"
        message += "\n`/info KEY` _Info about stream_"
        message += "\n`/run KEY` _Run stream_"
        message += "\n`/stop KEY` _Stop stream_"

        self._bot.send_message(user_id, message, parse_mode="MarkdownV2")


    def handle_info(self, tmessage):
        '''Handle /info command'''
        user_id = str(tmessage.from_user.id)
        secret = tmessage.text[5:].strip()
        # Getting a stream for user
        stream = self.__getStreamByKey(user_id, secret, "/info")
        if stream is None:
            return
        # Prepare and show info for the stream
        link = self.__getStreamLink(secret)
        status = "🟢 active" if stream.status == StreamStatus.active else "🔴 stopped" if stream.status == StreamStatus.stopped else "⚪️ unknown"
        message = '*Stream:* %s\n*Status:* %s\n*Key:* %s\n*Link:* %s' % (stream.name, status, secret, link)
        self._bot.send_message(user_id, message, parse_mode="Markdown", disable_web_page_preview=True)


    def handle_run(self, tmessage):
        '''Handle /run command'''
        user_id = str(tmessage.from_user.id)
        secret = tmessage.text[5:].strip()
        # Getting a stream for user
        stream = self.__getStreamByKey(user_id, secret, "/run")
        if stream is None:
            return
        # Checking that the stream is not running yet
        if stream.status == StreamStatus.active:
            self._bot.send_message(user_id, "*Stream is already active*.\n%s" % secret, parse_mode="Markdown")
            return
        # Run and send the result to user
        if Streams().setStatus(stream, StreamStatus.active):
            self._bot.send_message(user_id, "*Stream has been activated*.\n%s" % secret, parse_mode="Markdown")
        else:
            self._bot.send_message(user_id, "*Failed to activate stream!* Try again later…", parse_mode="Markdown")


    def handle_stop(self, tmessage):
        '''Handle /stop command'''
        user_id = str(tmessage.from_user.id)
        secret = tmessage.text[5:].strip()
        # Getting a stream for user
        stream = self.__getStreamByKey(user_id, secret, "/stop")
        if stream is None:
            return
        # Checking that the stream has not been stopped yet
        if stream.status == StreamStatus.stopped:
            self._bot.send_message(user_id, "*Stream is already stopped*.\n%s" % secret, parse_mode="Markdown")
            return
        # Stop and send the result to user
        if Streams().setStatus(stream, StreamStatus.stopped):
            self._bot.send_message(user_id, "*Stream has been stopped*.\n%s" % secret, parse_mode="Markdown")
        else:
            self._bot.send_message(user_id, "*Failed to stop stream!* Try again later…", parse_mode="Markdown")


    def __getStreamByKey(self, user_id, secret, action):
        '''Get stream for user by key(secret)
            Args:
                user_id(str):   Telegram user ID (chat ID)
                secret(str):    Stream key (secret)
                action(str):    Context action
        '''
        # Checking that the stream key is set
        if len(secret) == 0:
            self._bot.send_message(user_id, "Enter stream key in command: `%s KEY`" % action, parse_mode="Markdown")
            return None
        # Getting a stream
        stream = Streams().get(secret)
        # Checking that stream exists
        if stream is None:
            self._bot.send_message(user_id, "*Stream was not found.*\n%s" % secret, parse_mode="Markdown")
            return None
        # Returning the stream
        if user_id != stream.user_id:
            log_main.warning("Attempt to access someone else's stream (%s). User ID: %s. Owner ID: %s", action, user_id, stream.user_id)
            # Display message as if there is no stream (it is not available for the current user)
            self._bot.send_message(user_id, "*Stream was not found.*\n%s" % secret, parse_mode="Markdown")
            return None
        return stream
