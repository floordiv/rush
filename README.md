# Rush
Rush is a powerfull python web-server, focused on maximal horizontal expandability. Using microservices-like architecture

This branch is an attempt to make lib.epollserver asynchronous

Reason: synchronous requests/connections handling. Simple time.sleep() (or undelivered packet) can freeze the whole server. For example, if handshake from lib.epollserver failes, server is being freezed for 1 second (socket.timeout raises)

Effects: almost the whole webserver has to be rewritten as asynchronous
