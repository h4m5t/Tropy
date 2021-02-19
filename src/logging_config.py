import logging

# formatters
brief_formatter = logging.Formatter('%(levelname)-8s %(name)-10s %(message)s')
timed_formatter = logging.Formatter('%(levelname)-8s %(asctime)s %(name)-10s %(message)s')
detailed_formatter = logging.Formatter(
        f"Level: %(levelname)s\n"
        f"Time: %(asctime)s\n"
        f"Process: %(process)d\n"
        f"Thread: %(threadName)s\n"
        f"Function:%(funcName)s\n"
        f"Logger: %(name)s\n"
        f"Position: %(module)s:%(lineno)d\n"
        f"Message: %(message)s\n"
)

# handlers
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(brief_formatter)

file_handler = logging.FileHandler('tropy.log', mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(timed_formatter)

debug_console_handler = logging.StreamHandler()
debug_console_handler.setLevel(logging.DEBUG)
debug_console_handler.setFormatter(detailed_formatter)

debug_file_handler = logging.FileHandler('tropy.log', mode='w')
debug_file_handler.setLevel(logging.INFO)
debug_file_handler.setFormatter(detailed_formatter)

# loggers
# root = logging.getLogger()
# root.addHandler(console_handler)
# root.setLevel(logging.DEBUG)

server = logging.getLogger('server')
server.addHandler(debug_console_handler)
server.addHandler(debug_file_handler)
server.setLevel(logging.DEBUG)

client = logging.getLogger('client')
client.addHandler(debug_console_handler)
client.setLevel(logging.DEBUG)

trojan = logging.getLogger('trojan')
trojan.addHandler(debug_console_handler)
trojan.setLevel(logging.DEBUG)
