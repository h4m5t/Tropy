from socket import socket, gethostname, gethostbyname, AF_INET, SOCK_STREAM, SOCK_DGRAM
from threading import Thread


class Server:
    def __init__(self, main_port: int, sub_port: int):
        self.main_port = main_port
        self.sub_port = sub_port
        self.main_socket = socket(AF_INET, SOCK_STREAM)  # use TCP to transport shell communication
        self.sub_socket = socket(AF_INET, SOCK_DGRAM)  # use UDP to judge whether to transport the shell
        print(
                f'Established server :\n'
                f'\tip: {gethostbyname(gethostname())}\n'
                f'\tmain_port: {self.main_port}\n'
                f'\tsub_port: {self.sub_port}\n'
        )
        self._shell_socket = None

    def activate(self, client_ip):
        self.main_socket.bind((client_ip, self.main_port))
        Thread(target=self._communicate_with_shell).start()
        self.sub_socket.sendto('shell'.encode(), (client_ip, self.sub_port))

    def _communicate_with_shell(self):
        self.main_socket.listen(5)
        self._shell_socket, _ = self.main_socket.accept()
        print('shell activated')
        Thread(target=self._recv).start()
        Thread(target=self._send).start()

    def _recv(self):
        while True:
            data = self._shell_socket.recv(1024).decode()
            if len(data) > 0:
                print(data, end='')

    def _send(self):
        while True:
            data = input().encode()
            self._shell_socket.sendall(data)


if __name__ == '__main__':
    server = Server(36555, 36556)
    server.activate('localhost')
