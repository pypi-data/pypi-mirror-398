import argparse
import logging
import logging.config
import os
import sys
from multiprocessing import Lock

CONTAINER_ENV = os.environ.get("CONTAINER_ENV", "DEFAULT")


class Argument:
    __log_init = False
    if CONTAINER_ENV == "WSL_DOCKER":
        __init_lock = None
    else:
        __init_lock = Lock()

    def __init__(self, instance):
        self.__parser = argparse.ArgumentParser()
        Argument.__current = instance

    def param(self, name, default=None, help=None, action=None):
        self.__parser.add_argument("-" + name, default=default, help=help, action=action)
        return self

    def parse(self, args=sys.argv[1:]):
        self.__args = self.__parser.parse_args(args)
        self.__parameters = vars(self.__args)
        return self

    def get(self, name):
        return self.__parameters.get(name)

    def __str__(self):
        return str(self.__parameters)

    def usage(self):
        self.__parser.print_help()

    @classmethod
    def current(cls):
        return Argument.__current

    @classmethod
    def set_log_config(cls, config_file, create_logs_dir=True):
        Argument.__config_file = config_file
        Argument.__create_logs_dir = create_logs_dir

    @classmethod
    def logger(cls, tag):
        if not Argument.__log_init:
            if Argument.__init_lock is not None:
                Argument.__init_lock.acquire()
            if not Argument.__log_init:
                config_file = os.getenv("KOSMOS_LOG_CONFIG", default="log.conf")
                create_log_dir = os.environ.get("KOSMOS_LOG_DIR", default=".log")
                os.makedirs(create_log_dir, exist_ok=True)
                logging.config.fileConfig(config_file)
                Argument.__log_init = True
            else:
                return logging.getLogger(tag)
            if Argument.__init_lock is not None:
                Argument.__init_lock.release()
        return logging.getLogger(tag)
