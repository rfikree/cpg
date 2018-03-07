#! /bin/env wlst.sh
#

import os
import sys
import time
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
<title> %s Artifacts Information</title>
<body>
<h1 style="text-align: center; color: black"> %s Artifacts Information</h1>
'''

applicationHeader = '''
<h3 align=center>Server:%s  Port:%s </h3>
<table class="sortable" align=center>
<tr><th>Application</th><th>Build Number</th><th>State</th><th>TargetName</th></tr>
'''

libraryHeader = '''
<table class="sortable" align=center>
<tr><th>Library</th><th>Build Number</th><th>State</th><th>TargetName</th></tr>
'''

tableRow = '''<tr><td> %s </td><td> %s </td><td> %s </td><td> %s </td></tr>
'''

tableFooter = '''</table>
<br>
'''

pageFooter = '''
<p align=center>Generated: %s</p>
</body>
</HTML>'''


def genBody(server, port, artifacts):
    '''	Generate the body portion for a single url
        - a report may contain multiple bodies (tables)
    '''
    applications, libraries = artifacts

    content = applicationHeader % (server, port)
    for artifact in applications:
        content += tableRow % artifact
    content += tableFooter

    if libraries:
        content += libraryHeader
        for artifact in libraries:
            content += tableRow % artifact
        content += tableFooter

    return content

def genReport(reportid, reportComponents):
    ''' Generate a report with the specified report id
        given a list of of url, artificats '''
    report = pageHeader % (reportid, reportid)

    for (adminurl, artifacts) in reportComponents:
        (protocol, server, port) = adminurl.split(':')
        server = server.lstrip('/')
        body = genBody(server, port, artifacts)
        report += body

    now = time.localtime()
    now = time.strftime('%Y-%m-%d %H:%M', now)

    report += pageFooter % (now,)
    return report

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
        artifacts = getArtifacts(adminurl)
    else:
        user = sys.argv[2]
        passwd = sys.argv[3]
        #print adminurl, user, passwd
        artifacts = getArtifacts(adminurl, user, passwd)

    if artifacts:
        (protocol, server, port) = adminurl.split(':')
        server = server.lstrip('/')
        userid = server.split('-')[0] + port[:2]
        print 'calling genReport'
        print genReport(userid, [(adminurl, artifacts)])

if __name__ == "main":
    _testReport()


# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
