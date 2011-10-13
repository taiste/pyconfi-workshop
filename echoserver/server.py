import errno
import socket
import select

from collections import defaultdict


class EventLoop(object):
    def __init__(self):
        self.callbacks = []
        self.sources = set()
        self.handlers = {}

    def add_handler(self, fd, callback):
        self.handlers[fd] = callback
        self.sources.add(fd)

    def close(self, fd):
        self.sources.discard(fd)

    def start(self):
        poll_timeout = 0.2

        while True:
            r, w, _ = select.select(self.sources, self.sources, [],
                                    poll_timeout)
            for fd in r:
                if fd in self.handlers:
                    self.handlers[fd](fd, 'READ')
            for fd in w:
                if fd in self.handlers:
                    self.handlers[fd](fd, 'WRITE')


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
        self.eventloop.add_handler(self.socket.fileno(),
                                   self.handle_new_connection)

    def handle_new_connection(self, fd, event):
        assert fd == self.socket.fileno()

        try:
            conn, addr = self.socket.accept()
            print 'New connection from %s:%s' % addr
            self.eventloop.add_handler(conn.fileno(), self.handle_event)
            self.connection_pool[conn.fileno()] = conn
        except socket.error, e:
            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                return
            raise

    def handle_event(self, fd, event):
        conn = self.connection_pool[fd]
        try:
            if event == 'READ':
                self.handle_read(conn)
            elif event == 'WRITE':
                self.handle_write(conn)
        except socket.error, e:
            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                return
            print 'Socket %d closed.' % fd

    def handle_read(self, conn):
        fd = conn.fileno()
        self.read_buffer[fd] += conn.recv(4096)
        self.do_echo(fd)

    def handle_write(self, conn):
        fd = conn.fileno()
        if self.write_buffer[fd]:
            conn.send(self.write_buffer[fd].upper())
            self.write_buffer[fd] = ''
            # We've written enuff, close the connection
            self.close(fd)

    def do_echo(self, fd):
        rbuffer = self.read_buffer[fd]
        self.write_buffer[fd] += rbuffer
        self.read_buffer[fd] = ''

    def close(self, fd):
        self.eventloop.close(fd)
        print 'Closed connection %d' % fd


if __name__ == '__main__':
    loop = EventLoop()
    server = EchoServer(loop)
    server.start()
    loop.start()
