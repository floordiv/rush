import aepollserver

"""
this file is a good example (or even demo) of the work of the aepollserver lib
"""

epoll_server = aepollserver.AEpollServer(('localhost', 8801))


@epoll_server.handler(on_event=aepollserver.CONNECT)
async def handle_conn(_, server):
    conn, addr = server.accept()
    print('new conn from', addr)

    return conn


@epoll_server.handler(aepollserver.RECEIVE)
async def handle_recvmsg(_, conn: aepollserver.socket):
    print(f'received data from {conn.getpeername()}: {conn.recv(10)}')
    conn.send(b'hello!')


@epoll_server.handler(aepollserver.DISCONNECT)
async def handle_disconnect(_, conn):
    print('disconnected:', conn.getpeername())


epoll_server.start()
