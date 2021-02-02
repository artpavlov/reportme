import os
import logging
import datetime


log_level = logging.DEBUG # Default message level



class UseridFilter(logging.Filter):
    '''Default value for the user ID'''
    def filter(self, record):
        if not hasattr(record, 'userid'):
            record.userid = 'Global'
        return True



def setup_logger(name, log_file, level, format_=None):
    '''Get the configured logger object'''
    format_ = format_ or '%(asctime)s;[%(levelname)s];[%(threadName)s];%(message)s'
    formatter = logging.Formatter(format_)

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addFilter(UseridFilter())
    logger.addHandler(handler)

    return logger


timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# Main log
log_main = setup_logger('log_main', os.path.join('log', '%s_main.log' % timestamp), level=log_level)
