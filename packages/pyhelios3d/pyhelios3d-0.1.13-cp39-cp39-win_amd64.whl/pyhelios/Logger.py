import os

from .wrappers import ULoggerWrapper as logger_wrapper

class Logger:
    def __init__(self, log_file_name:str='pyhelios.log',  log_file_location:str=None):
        if log_file_location is None:
            log_file_location = os.path.dirname(os.path.realpath(__file__))
        self.logger = logger_wrapper.createLogger(log_file_name, log_file_location)


    def __del__(self):
        if self.logger:
            logger_wrapper.destroyLogger(self.logger)

    def write_log(self, label:str, message:str):
        logger_wrapper.writeLog(self.logger, label, message)
