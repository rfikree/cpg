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
    print "tcpping.py - Minimal TCP/UDP ping client"
    print
    print "Pings a host over TCP or UDP and reports the result"
    print
    print "Options:"
    print "    --help (-h) - print this message and exit"
    print "    --address (-a) - host address to  ping (default localhost)"
    print "    --interval (-i) -inverval between pings (default 1 second)"
    print "    --port (-p) - port to ping (default 7/echo"
    print "    --once (-o) - exit after first ping"
    print "    --tls (-t) - establish a TLS connection"
    print "    --udp (-u) - establish a UDP connection (disables TLS)"
    print
    print "UDP provides timing only, port may not have a listener"
    print
    sys.exit(2)

def timeDiff(start):
    return time.time() - start

def ping(address='localhost', interval=1, port=7, once=False, tls=False, udp=False):
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

    sock_type = socket.SOCK_STREAM
    if udp:
        sock_type = socket.SOCK_DGRAM
        tls = False

    while True:
        s=socket.socket(socket.AF_INET, sock_type)
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
            print 'Keyboard interrupt: Exiting'
            break
        finally:
            s.close()
        if once:
            break;
        time.sleep(interval)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hoa:i:p:tu",
                    ["help", "once", "address=", "interval=", "port=", "tls", "udp"])
        if args:
            usage()
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()

    address = 'localhost'
    interval = 1
    port = 7
    once = False
    tls = False
    udp = False

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
        elif o in ("-u", "--udp"):
            udp = True
        else:
            assert False, "unhandled option"

    if tls:
        print 'Using TLS for',
    if not once:
        print 'Pinging %s:%i every %i seconds' % (address, port, interval)
    else:
        print 'Pinging %s:%i' % (address, port)

    try:
        ping(address, interval, port, once, tls, udp)
    except KeyboardInterrupt:
        print 'Keyboard interrupt: Exiting'


if __name__=='__main__':
    main()
