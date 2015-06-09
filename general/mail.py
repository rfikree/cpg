#!/usr/bin/env python
# This is the mail.py file 			-*- tab-width:4 -*-

import smtplib
import email.utils
from email.mime.text import MIMEText
import getpass
import sys, getopt
import socket

sourceServer = socket.getfqdn(socket.gethostname())
from_email = getpass.getuser() + '@' + sourceServer
to_email = None
servername = 'smtp.mailposte.ca'
verbose = False

# Usage function
def usage():
	print "mail.py - Test email client"
	print
	print "Sends a short email identify this server to specified address"
	print
	print "Options:"
	print "	--name (-n) - Name of this server in message"
	print "	--to (-t) - Address to send message to"
	print "	--server (-s) - SMTP server to use (default ", servername, ")"
	print "	--verbose (-v) - turn on verbose"
	sys.exit(2)


# Parse the options
try:
	opts, args = getopt.getopt(sys.argv[1:], "hn:t:s:v", 
						["help", "name=", "to=", "server=", "verbose"])
except getopt.GetoptError, err:
	# print help information and exit:
	print str(err) # will print something like "option -a not recognized"
	usage()

for o, a in opts:
	if o in ("-h", "--help"):
		usage()
		sys.exit()
	elif o in ("-n", "--name"):
		sourceServer = a
	elif o in ("-t", "--to"):
		to_email = a
	elif o in ("-s", "--server"):
		servername = a
	elif o in ("-v", "--verbose"):
		verbose = True

# Verify require parameter(s) are set
if not to_email:
	print "Option --to is required"
	print
	usage()


# Create the message
msg = MIMEText('Test message from ' + sourceServer +
	' via ' + servername)	
msg['To'] = email.utils.formataddr(('Recipient', to_email))
msg['From'] = email.utils.formataddr(('Mail Client Test ' + sourceServer, from_email))
msg['Subject'] = 'Test from ' + sourceServer


# Send the message 
server = smtplib.SMTP(servername)
try:
	server.set_debuglevel(verbose)
	server.sendmail(from_email, [to_email], msg.as_string())
finally:
	server.quit()

# EOF
