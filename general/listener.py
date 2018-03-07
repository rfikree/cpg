#!/usr/bin/python
# This is listener.py file 			-*- tab-width:4 -*-

# It is a minimal http listener for port testing
# It will respond with its message and
#	read until a blank line, a timeout or the connection is closed
# This makes it suitable for testing with telnet as well as wget.
# It handles only one response at a time


import socket
import datetime
import getopt, sys
import re
from socket import error as socket_error


class listener:

    def __init__(self, statusMessage="200 OK", sock=None, timeout=5):
        self.statusMessage = "HTTP/1.0 " + statusMessage + "\r\n"
        socket.setdefaulttimeout(timeout)

        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock = sock

    def simpleServer(self, address=socket.gethostname(), port=12345,
                                    cert=None, key=None, oneTime=False):
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
            # Treat bind error as failure, logging condition
            print 'Failed to bind to', address, port
            print sock_err
            sys.exit(1)

        self.sock.listen(2)

        while True:
            try:
                connsocket = self.acceptRequest(self.sock)
                if connsocket:
                    if cert:
                        connsocket = self.tlsWrap(connsocket, cert, key)
                    self.serveResponse(connsocket, message)
                    connsocket.shutdown(socket.SHUT_RDWR)
                    connsocket.close()				# Close the connectionclass mysocket:
                    print "Connection closed"
            except socket_error as sock_err:
                # Ignore socket errors - occurs on LDAP servers under load
                # Don't log timeouts
                if str(sock_err) != 'timed out':
                    print 'socket_error occurred at', \
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ")
                    print sock_err
                continue

            if oneTime:
                break

        self.sock.close()

    def bind(self, host, port):
        self.sock.bind((host, port))

    def acceptRequest(self, sock):
        # Establish connection with client.
        connsocket, addr = sock.accept()
        print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S "),
        print 'Got connection from', addr
        return connsocket

    def wrapConnection(self, connsocket, cert, key):
        try:
            if key:
                connsocket = ssl.wrap_socket(connsocket,
                    server_side=True,
                    certfile=cert, keyfile=key,
                    ssl_version=ssl.PROTOCOL_SSLv23)
            else:
                connsocket = ssl.wrap_socket(connsocket,
                    server_side=True,
                    certfile=cert,
                    ssl_version=ssl.PROTOCOL_SSLv23)
        except ssl.SSLError:
            print "SSL Handshake failed. Using unsecure connections"
        return connsocket

    def serveResponse(self, connsocket, message):
        conn = connsocket.makefile()
        self.reply(conn, message)
        self.read(conn)

    def read(self, conn):
        while True:
            try:
                line = conn.readline()
                print "Read: " + line,
                if len(line) <= 2:		# Found CR, LF or EOF
                    return len(line)
            except socket_error, sock_err:
                break

    def reply(self, conn, message):
        print "Sending reply"
        conn.write( self.statusMessage )
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
    print "    --status (-s) - HTML status to return"
    print
    print "    --cert (-c) - Optional, SSL certificate file (can include key before certificate"
    print "    --key (-k) - Optional, SSL key file (omit if key is provided by cert file)"
    print

def getStatusMessage(status, default='200'):
    statusMessages = {
        '100': 'Continue',
        '101': 'Switching Protocols',
        '200': 'OK',
        '201': 'Created',
        '202': 'Accepted',
        '205': 'Reset Content',
        '206': 'Partial Content',
        '400': 'Bad Request',
        '401': 'Unauthorized',
        '402': 'Payment Required',
        '403': 'Forbidden',
        '404': 'Not Found',
        '405': 'Method Not Allowed',
        '406': 'Not Acceptable',
        '407': 'Proxy Authentication Required',
        '408': 'Request Timeout',
        '409': 'Conflict',
        '410': 'Gone',
        '411': 'Length Required',
        '412': 'Precondition Failed',
        '413': 'Payload Too Large',
        '414': 'URi Too Long',
        '415': 'Unsupported Media Type',
        '416': 'Range Not Satisfiable',
        '417': 'Expectation Failed',
        '418': "I'm a teapot",
        '421': 'Misdirected Request',
        '426': 'Upgrade Required',
        '428': 'Precondition Required',
        '429': 'Too Many Requests',
        '431': 'Request Header Fields Too Large',
        '451': 'Unavailable for Legal Reasons',
        '500': 'Internal Server Error',
        '501': 'Not Implemented',
        '502': 'Bad Gateway',
        '503': 'Service Unavailable',
        '504': 'Gateway Timeout',
        '505': 'HTTP Versions Not Supported',
        '506': 'Variant Also Negotiates',
        '510': 'Not Extended',
        '511': 'Network Authentication Required',
        '103': 'Checkpoint',
        '420': 'Method Failure',
        '499': 'Request has been forbidden by antivirus',
        '509': 'Bandwidth Limit Exceeded',
        '530': 'Site is frozen',
        '210': 'Paused',
    }

    if not status in statusMessages:
        print status, 'not found - using', default
        status = default

    return ' '.join((status, statusMessages[status]))

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ha:p:c:k:os:",
                    ["help", "address=", "port=", "cert=", "key=", "status="])
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
    statusMessage = getStatusMessage('200')

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
        elif o in ("-s", "--status"):
            statusMessage = getStatusMessage(a, '418')
        else:
            assert False, "unhandled option"

    if cert == None:
        print "Starting server for http://" + address + ":" + str(port)
    else:
        print "Starting server for https://" + address + ":" + str(port)

    s = listener(statusMessage)
    try:
        s.simpleServer(address, port, cert, key, oneTime)
    except KeyboardInterrupt:
        print 'KeyboardInterrupt received'
        pass
    print "Done"

if __name__ == "__main__":
    main()

# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
