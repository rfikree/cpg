#!/bin/env wlst.sh

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])))

from components import getArtifacts

pageHeader = '''<!DOCTYPE html>
<HTML>
<HEAD>
<link rel="stylesheet" type="text/css" href="/build-info/style1.css">
<script src="/build-info/sorttable.js" type="text/javascript"></script>
<!--[if lt IE 9]>
<script src="/build-info/IE9.js"></script>
<![endif]-->
</HEAD>
<title>WiPro Staging Artifacts</title>'''

tableHeader = '''
<h1 style="text-align: center; color: black"> %s  Artifacts Information</h1>
<body>
<h3 align=center>Server:%s  Port:%s </h3>
<table class="sortable" align=center>
<tr><th>Application</th><th>Build Number</th><th>State</th><th>TargetName</th></tr>
'''

tableRow = '<tr><td> %s </td><td> %s </td><td> %s </td><td> %s </td></tr>'

tableFooter = '''
</table>
<br>
'''

pageFooter = '''</body>
</HTML>'''


def genBody(userid, server, port, artifacts):
	print tableHeader % (userid, server, port)
	for artifact in artifacts:
		print tableRow % artifact
	print tableFooter

def genReport(contents):
	#print contents
	print pageHeader

	for (adminurl, artifacts) in contents:
		(protocol, server, port) = adminurl.split(':')
		server = server.lstrip('/')
		userid = server.split('-')[0] + port[:2]
		genBody(userid, server, port, artifacts)

	print pageFooter


def _testReport():
	if len(sys.argv) not in [2, 4]:
		print
		print 'usage: wlst.sh', sys.argv[0], 'adminurl'
		print 'usage: wlst.sh', sys.argv[0], 'adminurl user password'
		print
		exit('', 1)

	adminurl = sys.argv[1]

	if len(sys.argv) == 2:
		#print adminurl
		artifacts = getArtifacts(adminurl, 'Deployment Monitor', 'yIHj6oSGoRpl66muev5S')
	else:
		user = sys.argv[2]
		passwd = sys.argv[3]
		#print adminurl, user, passwd
		artifacts = getArtifacts(adminurl, user, passwd)

	if artifacts:
		#print 'calling genReport'
		genReport([(adminurl, artifacts)])

if __name__ == "main":
	_testReport()
