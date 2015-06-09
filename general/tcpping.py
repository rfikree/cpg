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

def usage():
	print '''Usage: %s host [port]
Tries to connect to host at the specified TCP port with a timeout of 5 seconds.
If the port is not specifed it defaults to 7 (TCP echo).
''' % os.path.basename(sys.argv[0])

def timeDiff(start):
	return time.time() - start

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

	while True:
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(5)
		try:
			start = time.time()
			s.connect((host, port))
			print '%2.6f - Connected' % (timeDiff(start))
		except (socket.error, socket.timeout), err:
			print '%2.6f - %s' % (timeDiff(start), err)
			pass
		except KeyboardInterrupt:
			print 'KeyboardInterrupt'
			break
		finally:
			s.close()
		time.sleep(1)



if __name__=='__main__':
	main()
