import select
from re import fullmatch
from asyncio import sleep
from threading import Thread
from socket import socket, timeout, MSG_PEEK

from lib.msgproto import recvbytes, sendmsg, recvmsg

"""
AEpollServer(addr: Tuple[str, int], maxconns: int = 0)

This is a copy of lib.epollserver, but asynchronous
"""

CONNECT = 0
DISCONNECT = 1
RECEIVE = 2
RESPONSE = 3

# constant that being returned by conn handler if connection has been refused
DENY_CONN = 5


class AEpollServer:
    def __init__(self, addr, maxconns=0):
        self.server_sock = socket()
        self.epoll = select.epoll()
        self.handlers = {}  # epoll event: callable

        self.server_sock.bind(addr)
        self.server_sock.listen(maxconns)
        self.server_sock.setblocking(False)
        self.addr = self.server_sock.getsockname()

        self._running = False
        self.conns = {}

    def add_handler(self, handler, on_event=all):
        self.handlers[on_event] = handler

    async def start(self):
        if self._running:
            raise RuntimeError('server already started')

        self._running = True
        self.epoll.register(self.server_sock.fileno(), select.EPOLLIN)

        # _running is also a flag. Server will stop after _running will be set to False
        while self._running:
            events = self.epoll.poll(1)

            for fileno, event in events:
                event_type = self.get_event_type(fileno, event)

                if all in self.handlers:
                    handler = self.handlers[all]
                    await handler(event_type, self.conns[fileno])
                    continue

                handler = self.handlers.get(event_type)

                if handler is None:
                    # no attached handlers registered
                    continue

                if event_type == CONNECT:
                    conn, addr = self.server_sock.accept()

                    if await handler(CONNECT, conn) == DENY_CONN:
                        # connection hasn't been accepted
                        # nothing will happen if we'll close closed socket
                        conn.close()
                        continue

                    conn.setblocking(False)
                    conn_fileno = conn.fileno()
                    self.conns[conn_fileno] = conn
                    self.epoll.register(conn_fileno, select.EPOLLIN)
                elif event_type == DISCONNECT:
                    self.epoll.unregister(fileno)
                    conn = self.conns.pop(fileno)
                    await handler(DISCONNECT, conn)

                    # as I said before, nothing will happen if
                    # we'll close already closed socket
                    conn.close()
                else:
                    await handler(event_type, self.conns[fileno])

    def get_event_type(self, fileno, event):
        if fileno == self.server_sock.fileno():
            return CONNECT
        elif event & select.EPOLLIN:
            try:
                peek_byte = self.conns[fileno].recv(1, MSG_PEEK)
            except ConnectionResetError:
                return DISCONNECT

            if not peek_byte:
                return DISCONNECT

            return RECEIVE
        elif event & select.EPOLLOUT:
            return RESPONSE
        elif event & select.EPOLLHUP:
            return DISCONNECT
        else:
            raise NotImplementedError('unimplemented epoll signal: ' + str(event))

    def handler(self, on_event=all):
        async def decorator(coroutine):
            self.handlers[on_event] = coroutine

            return coroutine

        return decorator

    def stop(self):
        # max server alive-time after stopping is 1 second
        self._running = False
        self.epoll.close()
        self.server_sock.close()

    def __del__(self):
        self.stop()


def handshake(i_am: str):
    """
    simple decorator that implements simple handshake protocol

    this protocol lets us to detect that requesting server is system's node
    by this steps:
        1) client sending to server these bytes: b'\x69\x04\x02\x00'
        2) client receives from server same bytes but reversed
        3) client sends byte \x69 (accepting server)
        4) server responds with it's name (using lib.msgproto.sendmsg)
        5) client sends \x00 if he doesn't connecting, or \x01 if he's connecting

    :param i_am: name of node
    """

    def decorator(handler):
        print('registering coroutine:', handler)

        async def wrapper(event_type, conn: socket):
            if event_type != CONNECT:
                return await handler(event_type, conn)

            try:
                bytesorder = await recvbytes(conn, 4, 1)

                if bytesorder != b'\x69\x04\x02\x00':
                    conn.close()  # first step failed

                    return DENY_CONN

                conn.send(b'\x00\x02\x04\x69')
                client_response = await recvbytes(conn, 1, 1)

                if client_response != b'\x69':
                    conn.close()

                    return DENY_CONN

                sendmsg(conn, i_am.encode())
                is_client_connecting = await recvbytes(conn, 1, 1)

                if not is_client_connecting:
                    conn.close()

                    return DENY_CONN

            except (timeout, BrokenPipeError) as exc:
                conn.close()

                return DENY_CONN

        return wrapper

    return decorator


async def do_handshake(conn, node_name=r'\w+'):
    """
    implements client-side protocol of handshake()

    :param conn: connection to server
    :param node_name: regexp (or just plain text) that contains name of required node
    :return: True if success or False if fail. Conn object is being closed if fail
    """

    try:
        print('sent ')
        conn.send(b'\x69\x04\x02\x00')
        server_response = await recvbytes(conn, 4, 1)
        print('received, lol')

        if server_response != b'\x00\x02\x04\x69':
            conn.close()

            return False

        conn.send(b'\x69')
        server_name = (await recvmsg(conn, timeout=1)).decode()

        if not fullmatch(node_name, server_name):
            conn.send(b'\x00')

            return False

        conn.send(b'\x01')
    except (timeout, BrokenPipeError) as exc:
        conn.close()

        return False

    return True

