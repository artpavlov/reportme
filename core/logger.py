# -*- coding: utf-8 -*-
'''Simple logging support'''
from typing import Optional
import os
import sys
import logging
import logging.handlers
import datetime


DEFAULT_LOG_LEVEL = logging.DEBUG # Default message level

USER_CONTEXT_NONE = 'None'
BOT_CONTEXT_GLOBAL = 'Global'



class UseridFilter(logging.Filter):
    '''Default value for the user ID'''
    def filter(self, record):
        if not hasattr(record, 'userid'):
            record.userid = USER_CONTEXT_NONE
        return True



def setup_logger(name: str, log_file: str, level: Optional[int] = None,
                 format_: Optional[str] = None, stdout: bool = False, time_rotate: bool = False) -> logging.Logger:
    '''Get the configured logger object'''
    # File handler
    format_file = format_ or '%(asctime)s;[%(levelname)s];[%(threadName)s];%(message)s'
    formatter_file = logging.Formatter(format_file)
    if time_rotate:
        handler_file = logging.handlers.TimedRotatingFileHandler(log_file, when='D', interval=1, encoding="utf-8") # Rotate daily
    else:
        handler_file = logging.FileHandler(log_file, encoding="utf-8")
    handler_file.setFormatter(formatter_file)
    # Stdout handler
    format_stdout = "%(message)s"
    formatter_stdout = logging.Formatter(format_stdout)
    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(formatter_stdout)

    # Logger configuration
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    logger.addFilter(UseridFilter())
    # logger.addFilter(BotidFilter())
    logger.addHandler(handler_file)
    if stdout:
        logger.addHandler(handler_stdout)

    return logger


timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# Main log
log_main_file = os.path.join('log', f'{timestamp}_main.log')
log_main = setup_logger('log_main', log_main_file, level=DEFAULT_LOG_LEVEL, stdout=True)
