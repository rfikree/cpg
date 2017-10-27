#!/usr/bin/env python
# (c) December 2007 Thomas Guettler http://www.thomas-guettler.de
# tcptraceroute.py
# This script is in the public domain
import getopt                  
import os
import re
import sys
import struct
import socket
import time

def usage():
	print "tcpping.py - Minimal TCP ping client"
	print
	print "Pings a host over TCP and report result"
	print
	print "Options:"
	print "    --help (-h) - print this message and exit"
	print "    --address (-a) - host address to  ping (default localhost)"
	print "    --port (-p) - port to ping (default 7/echo"
	print "    --once (-o) - exit after first ping"
	print

def timeDiff(start):
	return time.time() - start

def ping(address='localhost', port='7', once=False):
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
		time.sleep(1)                                                      
		if once:
			running = False

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hoa:p:",
					["help", "once", "address=", "port="])
	except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage()
		sys.exit(2)
		
	address='localhost'
	port='7'
	once=False
		
	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-a", "--address"):
			address = a
		elif o in ("-p", "--port"):
			port = int(a)
		elif o in ("-o", "--once"):
			once = True
		else:
			assert False, "unhandled option"

	ping(address, port, once)

if __name__=='__main__':
	main()
