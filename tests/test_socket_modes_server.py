import socket

with socket.socket() as sock:
    sock.bind(('localhost', 8000))
    sock.listen(1)

    conn, addr = sock.accept()
    conn.setblocking(False)
    print('new conn from', addr)

    while True:
        print(conn.recv(1))
