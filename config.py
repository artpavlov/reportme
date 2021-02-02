'''System configuration'''
import os

from core.singleton import Singleton



class Config(metaclass=Singleton):
    '''Configuration object'''
    def __init__(self):
        #* General settings
        # REPORTME_BASE_URL
        self.base_url = os.environ.get("REPORTME_BASE_URL")
        if not self.base_url:
            self.raiseEnvVarError("REPORTME_BASE_URL", "Base URL",
                                  "URL of the site where this bot will be run and processed")
        # REPORTME_WEBHOOK_PATH
        # Relative path for bot webhook
        self.webhook_path = os.environ.get("REPORTME_WEBHOOK_PATH")
        if not self.webhook_path:
            self.webhook_path = ""

        #* Database settings
        # REPORTME_DB_HOST
        self.db_host = os.environ.get("REPORTME_DB_HOST")
        if not self.db_host:
            self.raiseEnvVarError("REPORTME_DB_HOST", "Database host")
        # REPORTME_DB_USER
        self.db_user = os.environ.get("REPORTME_DB_USER")
        if not self.db_user:
            self.raiseEnvVarError("REPORTME_DB_USER", "Database user")
        # REPORTME_DB_PASSWORD
        self.db_password = os.environ.get("REPORTME_DB_PASSWORD")
        if not self.db_password:
            self.db_password = ""
        # REPORTME_DB_DATABASE
        self.db_database = os.environ.get("REPORTME_DB_DATABASE")
        if not self.db_database:
            self.raiseEnvVarError("REPORTME_DB_DATABASE", "Database",
                                  "Name of database")

        #* Bot settings
        # REPORTME_BOT_TOKEN
        self.bot_token = os.environ.get("REPORTME_BOT_TOKEN")
        if not self.bot_token:
            self.raiseEnvVarError("REPORTME_BOT_TOKEN", "Telegram bot token",
                                  "This token can be obtained in the telegram bot @BotFather")


    def raiseEnvVarError(self, name, desc, ext=""):
        '''Raise exception about missing environment variable'''
        raise EnvironmentError(
            "To start this application, you must set environment variable %s (%s)%s" %
            (name, desc if desc else "", ". %s" % ext if ext else "")
        )
