from socket import socket, AF_INET, SOCK_STREAM
import logging
from threading import Thread
from utils import *

logging.basicConfig(level=logging.DEBUG)


class Client:
    def __init__(self, token, server_ip, server_port):
        self.token = token
        self.server_addr = (server_ip, server_port)
        self.skt = socket(AF_INET, SOCK_STREAM)
        self._in_shell = False
        logging.debug(f'client info\n'
                      f'token: {self.token}\n'
                      f'server ip: {server_ip}\n'
                      f'server port: {server_port}')

    def run(self):
        self.skt.connect(self.server_addr)
        send_with_header(self.skt, Header.control, self.token)
        Thread(target=self._recv).start()
        Thread(target=self._send).start()

    def _recv(self):
        while True:
            data = self.skt.recv(1024)
            header, _ = parse(data)
            if header == Header.shell:
                self._in_shell = True
            if len(data) > 0:
                print(data.decode(), end='')

    def _send(self):
        while True:
            msg = input()
            header = Header.shell if self._in_shell else Header.control
            send_with_header(self.skt, header, msg)


if __name__ == '__main__':
    client = Client(
            token='100109',
            server_ip='localhost',
            server_port=36555
    )
    client.run()
