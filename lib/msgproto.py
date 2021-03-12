import socket
from time import time
from asyncio import sleep

FUTURE_MSG_LEN_BYTES = 4
READ_CHUNK_SIZE = 4096


def sendmsg(sock: socket.socket, data: bytes, msg_len_bytes=FUTURE_MSG_LEN_BYTES):
    packet_len = len(data).to_bytes(msg_len_bytes, 'little')

    return sock.send(packet_len + data)


async def recvmsg(sock: socket.socket, msg_len_bytes=FUTURE_MSG_LEN_BYTES,
                  timeout=None):
    encoded_msg_len = b''

    while len(encoded_msg_len) < msg_len_bytes:
        encoded_msg_len += sock.recv(msg_len_bytes - len(encoded_msg_len))

    msg_len = int.from_bytes(encoded_msg_len, 'little')

    return await recvbytes(sock, msg_len, timeout)


async def recvbytes(sock, bytescount, timeout):
    source = b''
    bytes_received = 0
    used_timeout = 0
    started_at = time()

    while (bytes_received < bytescount) and ((used_timeout < timeout)
          if timeout is not None else True):
        try:
            if used_timeout:
                used_timeout = 0

            received = sock.recv(bytescount - bytes_received)
            source += received
            bytes_received += len(received)
        except BlockingIOError:
            await sleep(.01)

            if used_timeout is not None:
                used_timeout += time() - started_at

    if timeout is not None and used_timeout >= timeout:
        return None

    return source
