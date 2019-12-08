"""
The stubs here acompany http://www.doxsey.net/blog/go-concurrency-from-the-ground-up
"""
import threading
import typing

from dataclasses import dataclass
from functools import partial

# Scheduling Methods

to_run = []

class ThreadWorker(threading.Thread):
    def __init__(self, callback):
        self.run = callback


def go(callback):
    worker = ThreadWorker(callback)
    to_run.append(worker.run)


def run():
    while to_run:
        command = to_run.pop()
        command()


# Channel Methods
@dataclass
class ChannelSender:
    value: typing.Any
    callback: typing.Callable


@dataclass
class ChannelReceiver:
    callback: typing.Callable[[typing.Any], None]


class Channel:
    def __init__(self):
        self._open = True
        self._waiting_to_send: typing.Iterable[ChannelSender] = []
        self._waiting_to_receive: typing.Iterable[ChannelReceiver] = []
        self._notify_on_success: typing.Iterable[typing.Callable] = []

    def close(self):
        self._open = False

    def send(self, sender: ChannelSender):
        self._waiting_to_send.append(sender)
        self._try_transmit()

    def recv(self, receiver: ChannelReceiver):
        self._waiting_to_receive.append(receiver)
        self._try_transmit()

    def notify(self, callback):
        self._notify_on_success.append(callback)


    def _try_transmit(self):
        if not self._open:
            raise ChannelClosedException()
        if self._waiting_to_send and self._waiting_to_receive:
            sender = self._waiting_to_send.pop()
            receiver = self._waiting_to_receive.pop()
            go(sender.callback)
            ok = True
            go(partial(receiver.callback, sender.value, ok))

            for callback in self._notify_on_success:
                go(callback)


class ChannelClosedException(Exception):
    pass


def make():
    return Channel()


def len(channel):
    return 1


def cap(channel):
    return 1


def send(channel, value, callback):
    assert_channel_is_not_none(channel)
    channel.send(ChannelSender(value, callback))


def recv(channel, callback):
    assert_channel_is_not_none(channel)
    channel.recv(ChannelReceiver(callback))


def close(channel):
    assert_channel_is_not_none(channel)
    channel.close()


def assert_channel_is_not_none(channel):
    if channel is None:
        raise TypeError("Trying to send on None Channel")


# Selection


def select(cases: typing.Iterable[typing.Tuple[typing.Callable, Channel, typing.Callable]],
           callback=None):
    for op, channel, callback in cases:
        channel.notify(callback)
