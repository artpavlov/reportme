# -*- coding: utf-8 -*-
'''Working with the database (MySQL)'''
from typing import Tuple, Callable, Any, Optional

import time
import threading
import MySQLdb

from core.logger import log_main
from core.singleton import Singleton
from core.exception import BotUnexpected

CHARSET = "utf8mb4"



class Database(metaclass=Singleton):
    '''(Singleton) A thread-safe wrapper for working with a database.
    Automatically reconnects when the connection is lost.'''

    @staticmethod
    def check_connection(host: str, user: str, password: str, database: str) -> Tuple[bool, str]:
        '''Check connection to the database'''
        try:
            con = MySQLdb.Connect(host=host, user=user, password=password, db=database, charset=CHARSET)
            con.close()
            return True, 'ok'
        except MySQLdb.OperationalError as e:
            return False, str(e)


    def __init__(self, host: Optional[str] = None, user: Optional[str] = None,
                 password: Optional[str] = None, database: Optional[str] = None) -> None:
        if host is None or user is None or password is None or database is None:
            log_main.error("Error when initiating the database connection — not all connection parameters were specified")
            raise BotUnexpected

        self.__host = host
        self.__user = user
        self.__password = password
        self.__database = database
        # Thread-unique variable for connection, initiated only once
        # It's prohibited to have universal connection object (leads to exceptions)
        self.__thread_local = threading.local()
        if self.connect():
            log_main.debug("Connection to the database is established")


    def connect(self) -> bool:
        '''Establish a database connection'''
        log_main.debug('Connecting to the database in the thread "%s"…', threading.current_thread().name)
        try:
            self.__thread_local.connection = MySQLdb.Connect(host=self.__host, user=self.__user, password=self.__password,
                                                             db=self.__database, charset=CHARSET)
            return True
        except MySQLdb.OperationalError:
            log_main.debug("Failed to connect to the database")
            return False
        except Exception: # pylint: disable=broad-except
            log_main.exception("Unexpected error when connecting to the database")
            return False


    def reconnect(self) -> None:
        '''(re)Try to establish a connection to the database until the connection is established'''
        attempt = 1
        max_delay = 60
        while True:
            if self.connect():
                break
            timeout = min(attempt, max_delay) # Waiting time increases after every attempt
            log_main.debug("Waiting %s sec until the next connection attempt", timeout)
            attempt += 1
            time.sleep(timeout) # Waiting until reconnect
            log_main.debug("Attempt #%s to connect to the database…", attempt)
        log_main.debug("The connection to the database is established")


    def get_connection(self) -> 'MySQLdb.Connection':
        '''Get the connection for the current thread. If there is no connection yet, create it'''
        try:
            self.__thread_local.connection
        except AttributeError: # Connection not created yet
            self.reconnect()
            return self.__thread_local.connection
        except Exception as e: # Some kind of connection error
            log_main.exception("Connection getting error")
            raise e
        else: # No errors (connection already exists)
            return self.__thread_local.connection


    def get_cursor(self) -> 'MySQLdb.cursors.Cursor':
        '''Get connection cursor for the current thread. If there is no connection yet, create it'''
        return self.get_connection().cursor()


    def execute(self, func: Callable[..., Any], *args) -> dict:
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
            # 4031 stands for disconnected by the server because of inactivity
            if errnum in (2006, 2013):
                log_main.warning("Connection to the database is lost")
                self.reconnect()
                return self.execute(func, *args)
            if errnum in (4031,):
                log_main.warning("The client was disconnected by the server because of inactivity")
                self.reconnect()
                return self.execute(func, *args)

            log_main.exception("Error when executing MySQL statement")
            return {'status': False, 'result': None}

        except UnboundLocalError as e:
            log_main.exception("Error when executing a block of code for working with the database")
            log_main.error("Most likely, the exception occurred due to the fact that a variable with the same name as global "
                           "was used somewhere in the code block, and the interpreter perceives it as local throughout this block (%s)", e)
            return {'status': False, 'result': None}
        except Exception as e: # pylint: disable=broad-except
            log_main.exception("Error when executing a block of code for working with the database")
            return {'status': False, 'result': None}


    def commit(self) -> None:
        '''Commit transaction to the database using current connection'''
        self.get_connection().commit()

    def rollback(self) -> None:
        '''Rollback transaction to the database using current connection'''
        self.get_connection().rollback()
