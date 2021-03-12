import socket
from time import time
from asyncio import sleep, run


async def recvmsg(conn, bytescount, timeout):
    source = b''
    bytes_received = 0
    used_timeout = 0
    started_at = time()

    while (bytes_received < bytescount) and (used_timeout < timeout):
        try:
            if used_timeout:
                used_timeout = 0

            received = conn.recv(bytescount - bytes_received)

            print('almost received:', received)

            if not received:
                print('nooo')
                break

            source += received
            bytes_received += len(received)
        except BlockingIOError:
            # print('temporary unavailable')
            await sleep(.01)
            used_timeout += time() - started_at

    if used_timeout >= timeout:
        return None

    return source


async def main():
    with socket.socket() as sock:
        sock.bind(('localhost', 8000))
        sock.listen(1)

        conn, addr = sock.accept()
        conn.setblocking(False)
        print('new conn from', addr)

        while True:
            received = await recvmsg(conn, 1, .7)
            print('received:', received)

            if received is None:
                print('nothing received, timeout occurred')
                conn.close()
                break


if __name__ == '__main__':
    run(main())
