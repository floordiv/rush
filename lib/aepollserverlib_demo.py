from asyncio import run

from lib import aepollserver
from lib.msgproto import recvmsg, sendmsg

"""
this file is a good example (or even demo) of the work of the aepollserver lib
"""

epoll_server = aepollserver.AEpollServer(('0.0.0.0', 8000))


@epoll_server.handler(on_event=aepollserver.CONNECT)
@aepollserver.handshake('server')
async def handle_conn(_, server):
    conn, addr = server.accept()
    print('new conn from', addr)

    return conn


@epoll_server.handler(aepollserver.RECEIVE)
async def handle_recvmsg(_, conn: aepollserver.socket):
    print(f'received data from {conn.getpeername()}: {await recvmsg(conn)}')
    sendmsg(conn, b'hello!')


@epoll_server.handler(aepollserver.DISCONNECT)
async def handle_disconnect(_, conn):
    print('disconnected:', conn.getpeername())


run(epoll_server.start())
