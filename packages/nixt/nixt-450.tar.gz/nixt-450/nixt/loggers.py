# This file is placed in the Public Domain.


"log exceptions."


import logging


class Format(logging.Formatter):

    def format(self, record):
        record.module = record.module.upper()
        return logging.Formatter.format(self, record)


class Log:

    datefmt = "%H:%M:%S"
    format = "%(module).3s %(message)s"


def level(loglevel):
    "set log level."
    formatter = Format(Log.format, Log.datefmt)
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logging.basicConfig(
        level=loglevel.upper(),
        handlers=[stream,],
        force=True
    )


def __dir__():
    return (
        'Log',
        'level'
    )
