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
        socket.close()

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


class SimpleStream(object):
    def __init__(self, socket, eventloop):
        self.socket = socket
        self.eventloop = eventloop

        self.read_buffer = ''
        self.write_buffer = ''
        self.chunk_size = 4096

        self._byte_treshold = None
        self._read_callback = None
        self._write_callback = None

        self.eventloop.add_handler(socket, self._handle_events)

    def _handle_events(self, conn, event):
        assert conn == self.socket
        try:
            if event == 'READ':
                self._handle_read()
            if event == 'WRITE':
                self._handle_write()
        except socket.error, e:
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return
            print 'Connection closed for %d' % self.socket.fileno()
            self.eventloop.close(self.socket)

    def _handle_read(self):
        self.read_buffer += self.socket.recv(self.chunk_size)

        if self._read_callback is not None:
            cb = self._read_callback
            self._read_callback = None
            num_bytes = self._byte_treshold
            self._byte_treshold = None
            self.read(num_bytes, cb)

    def _handle_write(self):
        if not self.write_buffer:
            return

        sent_bytes = self.socket.send(self.write_buffer)
        self.write_buffer = ''
        cb = self._write_callback
        self._write_callback = None
        cb(sent_bytes)

    def read(self, num_bytes, callback):
        if self.read_buffer:
            data = self.read_buffer[:num_bytes]
            self.read_buffer = self.read_buffer[num_bytes:]
            callback(data)
        else:
            self._byte_treshold = num_bytes
            self._read_callback = callback

    def write(self, data, callback):
        self.write_buffer += data
        self._write_callback = callback

    def close(self):
        self.eventloop.close(self.socket)


class EchoServer(object):
    def __init__(self, eventloop):
        self.eventloop = eventloop

    def listen(self, addr, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.setblocking(0)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((addr, port))
        self.socket.listen(2)

        self.eventloop.add_handler(self.socket, self.handle_new_connection)

    def handle_new_connection(self, sock, event):
        assert sock == self.socket

        try:
            conn, addr = self.socket.accept()
            print 'New connection from %s:%s' % addr

            self.stream = SimpleStream(conn, self.eventloop)
            self.stream.read(4096, self._read_done)
        except socket.error, e:
            if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                return
            raise

    def _read_done(self, data):
        self.stream.write(data.upper(), self._write_done)

    def _write_done(self, sent_bytes):
        print 'Wrote %d bytes!' % sent_bytes
        self.stream.close()


if __name__ == '__main__':
    loop = EventLoop()
    server = EchoServer(loop)
    server.listen('localhost', 9999)
    loop.start()
