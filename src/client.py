from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from threading import Thread
from time import sleep
import logging
import logging_config


logger = logging.getLogger(__name__)


class Client:
    def __init__(self, server_ip: str, shell_port: int, communication_port: int):
        self.server_ip = server_ip
        self.ports = {
            'shell': shell_port,
            'communication': communication_port,
        }

    def run(self, token: str):
        shell_socket = socket(AF_INET, SOCK_STREAM)
        communication_socket = socket(AF_INET, SOCK_DGRAM)

        communication_socket.bind(('localhost', self.ports['communication']))
        communication_socket.sendto(token.encode(), (self.server_ip, self.ports['communication']))
        print(communication_socket.recv(1024))
        name = input('select a rookie:')
        communication_socket.sendto(name.encode(), (self.server_ip, self.ports['communication']))
        print(communication_socket.recv(1024))


if __name__ == '__main__':
    client = Client(
            server_ip='192.168.19.1',
            shell_port=36558,
            communication_port=36559,
    )
    client.run('123456')
