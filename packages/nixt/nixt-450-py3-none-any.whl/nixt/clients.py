# This file is placed in the Public Domain.


"handle your own events"


import logging
import queue
import threading
import _thread


from .brokers import add
from .command import command
from .handler import Handler
from .threads import launch


class Client(Handler):

    def __init__(self):
        super().__init__()
        self.olock = threading.RLock()
        self.oqueue = queue.Queue()
        self.silent = True
        add(self)

    def announce(self, text):
        "announce text to all channels."
        if not self.silent:
            self.raw(text)

    def display(self, event):
        "display event results."
        with self.olock:
            for tme in event.result:
                txt = event.result.get(tme)
                self.dosay(event.channel, txt)

    def dosay(self, channel, text):
        "say called by display."
        self.say(channel, text)

    def raw(self, text):
        "raw output."
        raise NotImplementedError("raw")

    def say(self, channel, text):
        "say text in channel."
        self.raw(text)

    def wait(self):
        "wait for output to finish."
        try:
            self.oqueue.join()
        except Exception as ex:
            logging.exception(ex)
            _thread.interrupt_main()


class CLI(Client):

    def __init__(self):
        super().__init__()
        self.register("command", command)


class Output(Client):

    def output(self):
        "output loop."
        while True:
            event = self.oqueue.get()
            if event is None:
                self.oqueue.task_done()
                break
            self.display(event)
            self.oqueue.task_done()

    def start(self):
        "start output loop."
        launch(self.output)
        super().start()

    def stop(self):
        "stop output loop."
        self.oqueue.put(None)
        super().stop()


def __dir__():
    return (
        'CLI',
        'Client',
        'Output'
    )
