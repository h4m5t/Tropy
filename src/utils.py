import logging
from functools import update_wrapper, partial

logging.basicConfig(level=logging.DEBUG)


class Header:
    control = '[C]'
    shell = '[S]'
    heartbeat = '[H]'


def parse(data: bytes):
    data = data.decode()
    if len(data) < 3:
        return '', ''
    else:
        return data[:3], data[3:]


def recv_with_header(socket, target_header):
    while True:
        data = socket.recv(1024)
        header, msg = parse(data)
        if header == target_header:
            return msg


def send_with_header(socket, header, msg):
    while len(msg) > 1021:
        part = msg[:1021]
        data = (header + part).encode()
        socket.send(data)
        msg = msg[1021:]
    data = (header + msg).encode()
    socket.send(data)


# ignore socket error
class IgnoreSE:
    def __init__(self, func):
        self.func = func
        update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        try:
            return self.func(*args, **kwargs)
        except (ConnectionError, OSError):
            logging.debug(f'{self.func.__name__} terminated due to SE')
            pass

    def __get__(self, instance, owner):
        return partial(self, instance)
