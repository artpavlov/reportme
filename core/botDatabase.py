import time
import threading
import MySQLdb

from core.singleton import Singleton
from core.botLogger import log_main
from core.botException import BotUnexpected


CHARSET = "utf8mb4"



class Database(metaclass=Singleton):
    '''A thread-safe wrapper for working with a database. Automatically reconnects when the connection is lost.'''

    @staticmethod
    def checkConnection(host, user, password, database):
        '''Check connection to the database'''
        try:
            con = MySQLdb.Connect(host=host, user=user, password=password, db=database, charset=CHARSET)
            con.close()
            return True, 'ok'
        except MySQLdb.OperationalError as e:
            return False, str(e)


    def __init__(self, host=None, user=None, password=None, database=None):
        if host is None or user is None or password is None or database is None:
            log_main.error("Error when initiating the database connection — not all connection parameters were specified")
            raise BotUnexpected

        self.__host = host
        self.__user = user
        self.__password = password
        self.__database = database
        self.__threadLocal = threading.local() # Thread-unique variable, initiated only once
        if self.connect():
            log_main.info("The connection to the database is established")


    def connect(self): #, init=False):
        '''Establish a database connection'''
        log_main.debug('Connecting to the database in the stream "%s"…', threading.current_thread().name)
        try:
            self.__threadLocal.connection = MySQLdb.Connect(host=self.__host, user=self.__user, password=self.__password,
                                                            db=self.__database, charset=CHARSET)
            return True
        except MySQLdb.OperationalError:
            log_main.info("Failed to connect to the database")
            return False
        except Exception: # pylint: disable=broad-except
            log_main.exception("An unexpected error occurred while connecting to the database")
            return False


    def reconnect(self):
        '''(re)Try to establish a connection to the database until the connection is established'''
        attempt = 1
        max_delay = 60
        while True:
            log_main.info("Attempt #%s to connect to the database…", attempt)
            if self.connect():
                break
            timeout = min(attempt, max_delay) # Waiting time increases after every attempt
            log_main.info("Waiting %s sec until the next connection attempt", timeout)
            attempt += 1
            time.sleep(timeout) # Waiting until reconnect
        log_main.info("The connection to the database is established")


    def getConnection(self):
        '''Get the connection for the current thread. If there is no connection yet, create it'''
        try:
            self.__threadLocal.connection
        except AttributeError: # Connection not created yet
            self.reconnect()
            return self.__threadLocal.connection
        except Exception as e: # Some kind of connection error
            log_main.exception("Connection retrieving error")
            raise e
        else: # No errors (connection already exists)
            return self.__threadLocal.connection


    def execute(self, func, *args):
        '''Execute the function passed as a parameter. MySQLdb exception handling and automatic reconnection are performed if required
            Args:
                func(function): The function that performs some actions with the database
            Returns:
                dict:           Dictionary with the operation status ('status') and the result of the function execution ('result')
        '''
        try:
            return {'status': True, 'result': func(*args)}
        except MySQLdb.OperationalError as e: # Connection lost
            errnum, _errmsg = e.args
            # 2006 stands for MySQL has gone away
            # 2013 stands for lost connection to MySQL
            if errnum in (2006, 2013):
                log_main.warning("The database connection is lost.")
                self.reconnect()
                return self.execute(func, *args)

            log_main.exception("Error when executing MySQL")
            return {'status': False, 'result': None}

        except UnboundLocalError as e:
            log_main.exception("Error when executing a block of code for database.")
            log_main.error("Most likely, the exception occurred due to the fact that somewhere in the code block a variable with the same name is used as a global one and the interpreter perceives it as local in this entire block (%s)", e)
            return {'status': False, 'result': None}
        except Exception as e: # pylint: disable=broad-except
            log_main.exception("Error when executing a block of code for database.")
            return {'status': False, 'result': None}
