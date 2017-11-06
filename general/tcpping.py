#!/usr/bin/env python
# (c) December 2007 Thomas Guettler http://www.thomas-guettler.de
# tcptraceroute.py
# This script is in the public domain
import getopt
import os
import re
import ssl
import sys
import struct
import socket
import time

def usage():
    print "tcpping.py - Minimal TCP ping client"
    print
    print "Pings a host over TCP and reports the result"
    print
    print "Options:"
    print "    --help (-h) - print this message and exit"
    print "    --address (-a) - host address to  ping (default localhost)"
    print "    --interval (-i) -inverval between pings (default 1 second)"
    print "    --port (-p) - port to ping (default 7/echo"
    print "    --once (-o) - exit after first ping"
    print "    --tls (-t) - establish a TLS connection"
    print

def timeDiff(start):
    return time.time() - start

def ping(address='localhost', interval=1, port=7, once=False, tls=False):
    try:
        port_int=int(port)
    except ValueError:
        if not os.path.exists('/etc/services'):
            print 'port needs to be an integer if /etc/services does not exist.'
            sys.exit(1)
        fd=open('/etc/services')
        for line in fd:
            match=re.match(r'^%s\s+(\d+)/tcp.*$' % port, line)
            if match:
                port_int = int(match.group(1))
                break
        if not port_int:
            print 'port %s not in /etc/services' % port
            sys.exit(1)
    port=port_int

    running = True

    while running:
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        if tls:
            s = ssl.wrap_socket(s,
                ssl_version=ssl.PROTOCOL_SSLv23)
        try:
            start = time.time()
            s.connect((address, port))
            print '%2.6f - Connected' % (timeDiff(start))
        except (socket.error, socket.timeout), err:
            print '%2.6f - %s' % (timeDiff(start), err)
            pass
        except KeyboardInterrupt:
            print 'KeyboardInterrupt'
            break
        finally:
            s.close()
        time.sleep(interval)
        if once:
            running = False

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hoa:i:p:t",
                    ["help", "once", "address=", "interval=", "port=", "tls"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    address='localhost'
    interval=1
    port=7
    once=False
    tls=False

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-a", "--address"):
            address = a
        elif o in ("-", "--port"):
            port = int(a)
        elif o in ("-i", "--interval"):
            interval = int(a)
        elif o in ("-p", "--port"):
            port = int(a)
        elif o in ("-o", "--once"):
            once = True
        elif o in ("-t", "--tls"):
            tls = True
        else:
            assert False, "unhandled option"

    if not once:
        print 'Pinging %s:%i every %i seconds' % (address, port, interval)
    else:
        print 'Pinging %s:%i' % (address, port)
    if tls:
        print 'Using TLS'
    ping(address, interval, port, once, tls)

if __name__=='__main__':
    main()
