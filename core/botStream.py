from enum import IntEnum
import uuid
import baseconv

from core.singleton import Singleton
from core.botDatabase import Database
from core.botException import BotUnexpected
from core.botLogger import log_main

STREAMS_TABLE = 'streams'



class StreamStatus(IntEnum):
    stopped = 0
    active = 1



class Stream:
    '''Message stream class'''
    def __init__(self, id_, user_id, secret, name, status):
        self.id = id_
        self.user_id = str(user_id)
        self.secret = secret
        self.name = name
        self.status = int(status)



class Streams(metaclass=Singleton):
    '''Message streams manager'''
    def __init__(self):
        super().__init__()
        self.__streams = {}

        def loadStreamsSQL():
            '''Get all existing streams from database'''
            with Database().getConnection().cursor() as cursor:
                sql = "SELECT * FROM " + STREAMS_TABLE
                cursor.execute(sql)
                return cursor.fetchall()

        res = Database().execute(loadStreamsSQL)
        if res['status'] is False:
            log_main.error("Failed to load streams")
            raise BotUnexpected

        for rec in res['result']:
            id_, user_id, secret, name, status = rec
            self.__streams[secret] = Stream(id_, user_id, secret, name, status)


    def get(self, secret):
        '''Get stream with selected key (secret)
            Args:
                secret(str):    Stream key
            Returns:
                Stream:         Resulting stream
        '''
        try:
            return self.__streams[secret]
        except KeyError:
            return None


    def getAll(self, user_id):
        '''Get a list of all streams for a given telegram user
            Args:
                user_id(str):   Telegram user ID (chat ID)
            Returns:
                list:           List of resulting streams (Stream)
        '''
        result = []
        for secret in self.__streams:
            if self.__streams[secret].user_id == user_id:
                result.append(self.__streams[secret])
        return result


    def add(self, user_id, name):
        '''Create new stream for given telegram user
            Args:
                user_id(str):   Telegram user ID (chat ID)
                name(str):      The name of the stream
            Returns:
                str:            Stream key (secret)
        '''
        # Generate a unique stream key
        alphabet = "0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
        converter = baseconv.BaseConverter(alphabet)
        codeLength = 32
        secret = converter.encode(uuid.uuid4().int)[0:codeLength]

        # Check the uniqueness
        if secret in self.__streams:
            log_main.error("Uniqueness error when adding a stream: %s", secret)
            return None

        # Add stream
        stream_status = int(StreamStatus.active)
        def addStreamSQL():
            '''Get all existing streams from database'''
            with Database().getConnection().cursor() as cursor:
                sql = "INSERT INTO " + STREAMS_TABLE + " (user_id, secret, name, status) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (user_id, secret, name, stream_status))
                Database().getConnection().commit()
                return Database().getConnection().insert_id()

        res = Database().execute(addStreamSQL)
        if res['status'] is False:
            log_main.error("Error when adding a new stream")
            return None

        # Add to cache
        stream_id = res['result']
        if stream_id is not None:
            stream = Stream(stream_id, user_id, secret, name, stream_status)
            self.__streams[secret] = stream
            log_main.info('Added new stream "%s" for user %s with the key: %s', name, user_id, secret)
            return secret

        # If it was not added
        raise Exception("Couldn't add new stream")


    def delete(self, secret):
        '''Delete stream with specified key
            Args:
                secret(str):    Stream key (secret)
            Returns:
                bool:           Operation result
        '''
        # Удаляем поток даже если в кэше не было
        def deleteStreamSQL():
            with Database().getConnection().cursor() as cursor:
                sql = "DELETE FROM "+STREAMS_TABLE+" WHERE secret=%s"
                cursor.execute(sql, (secret,))
                Database().getConnection().commit()
                return cursor.rowcount > 0

        res = Database().execute(deleteStreamSQL)
        if res['status'] is False:
            log_main.error("Error deleting a stream")
            return None

        # Log operation
        user_id = None
        stream_name = "?"
        if secret in self.__streams:
            user_id = self.__streams[secret].user_id
            stream_name = self.__streams[secret].name
        log_main.info('Deleted stream "%s" for user %s with key: %s', stream_name, user_id, secret)

        # Remove from the cache
        del self.__streams[secret]
        return True


    def setStatus(self, stream, status):
        '''Set the status of a given stream
            Args:
                key(str):       Stream key (secret)
                status(int):    New status
            Returns:
                bool:           Operation result
        '''
        status = int(status)
        if stream.status == status:
            return True # The status has not changed

        if stream.secret not in self.__streams:
            log_main.error("Attempt to change the status of a stream that is not in the cache. Key: %s", stream.secret)
            return False # Uncached stream

        def updateStreamStatusSQL():
            with Database().getConnection().cursor() as cursor:
                sql = "UPDATE "+STREAMS_TABLE+" SET status=%s WHERE secret=%s"
                cursor.execute(sql, (status, stream.secret))
                Database().getConnection().commit()

        res = Database().execute(updateStreamStatusSQL)
        if res['status'] is False:
            log_main.error("Error when changing the stream status")
            return False

        # Update the cache
        self.__streams[stream.secret].status = status
        return True
