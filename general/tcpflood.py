#!/usr/bin/env python
# (c) December 2007 Thomas Guettler http://www.thomas-guettler.de
# tcptraceroute.py
# This script is in the public domain

import os
import re
import sys
import struct
import socket
import time

count = 0

def usage():
    print '''Usage: %s host [port]
Tries to connect to host at the specified TCP port with a timeout of 5 seconds.
If the port is not specifed it defaults to 7 (TCP echo).
''' % os.path.basename(sys.argv[0])

def timeDiff(start):
    return time.time() - start

def reportConnect( start, message ):
    global count
    timeTaken = timeDiff(start)
    #print '%2.6f - %s - %d' % (timeTaken, message, count)
    count += 1
    if timeTaken > 1.0:
        print '%2.6f - %s - %d' % (timeTaken, message, count)
        count = 0
    elif not count % 100:
        print '%2.6f - %s + %d' % (timeTaken, message, count)
        return

def main():
    if not 1 < len(sys.argv) < 4:
        usage()
        sys.exit(1)

    host = sys.argv[1]
    if len(sys.argv) <= 2:
        port = '7'
    else:
        port = sys.argv[2]
    port_int = None
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
                port_int=int(match.group(1))
                break
        if not port_int:
            print 'port %s not in /etc/services' % port
            sys.exit(1)
    port=port_int

    running = True
    while running:
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            start = time.time()
            s.connect((host, port))
            x = reportConnect(start, 'Connected')
        except (socket.error, socket.timeout), err:
            x = reportConnect(start, err)
            pass
        except KeyboardInterrupt:
            print 'KeyboardInterrupt'
            running = False
            pass
        finally:
            s.close()
        time.sleep(0.001)



if __name__=='__main__':
    main()

# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
