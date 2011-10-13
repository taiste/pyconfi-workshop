import sys
import socket

sock = socket.create_connection(('localhost', 9999))

num_bytes = sock.send(' '.join(sys.argv[1:]) + '\n')

print 'sent:', ' '.join(sys.argv[1:])

print 'received:', sock.recv(num_bytes)
sock.close()
