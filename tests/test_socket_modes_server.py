import socket
from time import time
from asyncio import sleep


async def recvmsg(conn, bytescount, timeout):
    source = b''
    bytes_received = 0
    used_timeout = 0
    started_at = time()

    while (bytes_received < bytescount) or (used_timeout < timeout):
        try:
            if used_timeout:
                used_timeout = 0

            received = conn.recv(bytescount - bytes_received)
            source += received
            bytes_received += len(received)
        except BlockingIOError:
            print('temporary unavailable')
            await sleep(.01)
            used_timeout += time() - started_at

    if used_timeout >= timeout:
        return None

    return source


def main():
    with socket.socket() as sock:
        sock.bind(('localhost', 8000))
        sock.listen(1)

        conn, addr = sock.accept()
        conn.setblocking(False)
        print('new conn from', addr)

        while True:
            print(await recvmsg(conn, 1, .7))


if __name__ == '__main__':
    main()
