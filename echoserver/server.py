import errno
import socket
import select

from collections import defaultdict


class EventLoop(object):
    def __init__(self):
        self.callbacks = []
        self.sources = set()
        self.handlers = {}

    def add_handler(self, socket, callback):
        self.handlers[socket] = callback
        self.sources.add(socket)

    def close(self, socket):
        self.sources.discard(socket)

    def start(self):
        poll_timeout = 0.2

        while True:
            readable, writable, errors = select.select(
                self.sources, self.sources, [], poll_timeout)
            for sock in readable:
                if sock in self.handlers:
                    self.handlers[sock](sock, 'READ')
            for sock in writable:
                if sock in self.handlers:
                    self.handlers[sock](sock, 'WRITE')


class EchoServer(object):
    def __init__(self, eventloop):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.setblocking(0)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('localhost', 9999))
        self.socket.listen(2)
        self.eventloop = eventloop
        self.connection_pool = {}

        self.read_buffer = defaultdict(str)
        self.write_buffer = defaultdict(str)

    def start(self):
        self.eventloop.add_handler(self.socket, self.handle_new_connection)

    def handle_new_connection(self, sock, event):
        assert sock == self.socket

        try:
            conn, addr = self.socket.accept()
            print 'New connection from %s:%s' % addr
            self.eventloop.add_handler(conn, self.handle_event)
            self.connection_pool[conn.fileno()] = conn
        except socket.error, e:
            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                return
            raise

    def handle_event(self, conn, event):
        try:
            if event == 'READ':
                self.handle_read(conn)
            elif event == 'WRITE':
                self.handle_write(conn)
        except socket.error, e:
            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                return
            print 'Socket %d closed.' % conn.fileno()

    def handle_read(self, conn):
        self.read_buffer[conn] += conn.recv(4096)
        self.do_echo(conn)

    def handle_write(self, conn):
        if self.write_buffer[conn]:
            conn.send(self.write_buffer[conn].upper())
            self.write_buffer[conn] = ''
            # We've written enuff, close the connection
            self.close(conn)

    def do_echo(self, conn):
        rbuffer = self.read_buffer[conn]
        self.write_buffer[conn] += rbuffer
        self.read_buffer[conn] = ''

    def close(self, conn):
        self.eventloop.close(conn)
        print 'Closed connection %d' % conn.fileno()


if __name__ == '__main__':
    loop = EventLoop()
    server = EchoServer(loop)
    server.start()
    loop.start()
