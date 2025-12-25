# This file is placed in the Public Domain.


"configuration"


from .objects import Default


class Config(Default):

    debug = False
    gets = Default()
    ignore = ""
    init = ""
    level = "info"
    name = ""
    opts = ""
    sets = Default()
    version = 0


def __dir__():
    return (
        'Config',
    )
