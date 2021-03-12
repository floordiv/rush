import socket
from asyncio import run

from lib.msgproto import sendmsg, recvmsg
from lib.aepollserver import do_handshake


async def main():
    with socket.socket() as sock:
        sock.connect(('localhost', 8000))
        print('connected to localhost:8000')
        await do_handshake(sock, 'server')
        print('handshake succeeded')
        sendmsg(sock, b'hello!')
        print("sent: b'hello!'")
        response = await recvmsg(sock)
        print('received:', response)


if __name__ == '__main__':
    run(main())
