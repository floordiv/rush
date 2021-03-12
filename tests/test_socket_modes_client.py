import socket
from time import sleep

with socket.socket() as sock:
    sock.connect(('localhost', 8000))
    sock.send(b'\x01')
    print('sent 1 byte')
    sock.send(b'\x02')
    print('send 2 byte')
    sleep(1)
    print('slept')
    sock.send(b'\x03')
    print('sent 3 byte')

print('finished')
