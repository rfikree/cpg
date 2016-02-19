#!/usr/bin/python
# This is listener.py file 			-*- tab-width:4 -*-

# It is a minimal http listener for port testing
# It will respond with its message on the first blank line it encounters
# This makes it suitable for testing with telnet as well as wget.
# It handles only one response at a time


import socket
import datetime
import getopt, sys
from socket import error as socket_error


class listener:

	def __init__(self, sock=None):
		if sock is None:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock = sock


	def simpleServer(self, address=socket.gethostname(), port=12345, cert=None, key=None, oneTime=False):
		message = "\r\n" + \
				  "Server: " + address + ":" + str(port) + "\r\n" + \
				  "\r\n"

		if cert:
			try:
				import ssl
			except ImportError:
				print "SSL is not available secure connection not possible"
				cert = None

		try:
			self.bind(address, port)
		except socket_error, sock_err:
			# Treat bind error as success, logging condition
			print 'Failed to bind to', address, port
			print sock_err
			sys.exit(0)

		self.sock.listen(5)

		while True:
			# Establish connection with client.
			try:
				connsocket, addr = self.sock.accept()
			except socket_error, sock_err:
				# Ignore socket errors - occurs on LDAP servers under load
				print 'socket_error occured at', \
					datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ")
				print sock_err
				continue

			print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S "),
			print 'Got connection from', addr

			if cert:
				try:
					if key:
						newsocket = ssl.wrap_socket(connsocket,
							server_side=True,
							certfile=cert, keyfile=key,
							ssl_version=ssl.PROTOCOL_SSLv23)
					else:
						newsocket = ssl.wrap_socket(connsocket,
							server_side=True,
							certfile=cert,
							ssl_version=ssl.PROTOCOL_SSLv23)
					connsocket = newsocket
				except ssl.SSLError:
					print "SSL Handshake failed. Using unsecure connections"

			conn = connsocket.makefile()
			if self.read(conn):
				self.reply(conn, message)
				if oneTime:
					break
			#else:
			#	print "Disconnected  reading"

			connsocket.shutdown(socket.SHUT_RDWR)
			connsocket.close()				# Close the connectionclass mysocket:
			print "Connection closed"
		self.sock.close()

	def bind(self, host, port):
		self.sock.bind((host, port))

	def read(self, conn):
		while True:
			line = conn.readline()
			print "Read: " + line,
			if len(line) <= 2:		# Found CR-LF or EOF
				return len(line)

	def reply(self, conn, message):
		print "Sending reply"
		conn.write( "HTTP/1.0 200 OK\r\n" )
		conn.write( "Connection: close\r\n" )
		conn.write( "Content-Type: text/plain\r\n" )
		conn.write( "Content-Length: " + str(len(message)) + "\r\n" )
		conn.write( "\r\n" )
		conn.flush()
		conn.write( message )
		conn.flush()

def usage():
	print "listener.py - Minimal server to listen on a port"
	print
	print "Prints a response on firt empty line and closes port"
	print
	print "Options:"
	print "    --help (-h) - print this message and exit"
	print "    --address (-a) - set the host address to listen on (default hostname)"
	print "    --port (-p) - set the port to listen on (default 12345)"
	print "    --oneTime (-o) - exit after responding to a request"
	print
	print "    --cert (-c) - Optional, SSL certificate file (can include key before certificate"
	print "    --key (-k) - Optional, SSL key file (omit if key is provided by cert file)"
	print

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ha:p:c:k:o",
								["help", "address=", "port=", "cert=", "key="])
	except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage()
		sys.exit(2)

	address = socket.gethostname()
	port = 12345
	cert = None
	key = None
	oneTime = False

	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-a", "--address"):
			address = a
		elif o in ("-p", "--port"):
			port = int(a)
		elif o in ("-c", "--cert"):
			cert = a
		elif o in ("-k", "--key"):
			key = a
		elif o in ("-o", "--oneTime"):
			oneTime = True
		else:
			assert False, "unhandled option"

	if cert == None:
		print "Starting server for http://" + address + ":" + str(port)
	else:
		print "Starting server for https://" + address + ":" + str(port)

	s = listener()
	s.simpleServer(address, port, cert, key, oneTime)
	print "Done"

if __name__ == "__main__":
	main()

# EOF
