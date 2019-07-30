#! /bin/env wlst.sh
'''generateReport.py - Generate a report for the build info functionality
'''

# pylint: disable=duplicate-code

import sys
import time

from components import get_artifacts

PAGE_HEADER = '''<!DOCTYPE html>
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

APPLICATION_HEADER = '''
<h3 align=center>Server:%s  Port:%s </h3>
<table class="sortable" align=center>
<tr><th>Application</th><th>Build Number</th><th>State</th><th>TargetName</th></tr>
'''

LIBRARY_HEADER = '''
<table class="sortable" align=center>
<tr><th>Library</th><th>Build Number</th><th>State</th><th>TargetName</th></tr>
'''

TABLE_ROW = '''<tr><td> %s </td><td> %s </td><td> %s </td><td> %s </td></tr>
'''

TABLE_FOOTER = '''</table>
<br>
'''

PAGE_FOOTER = '''
<p align=center>Generated: %s</p>
</body>
</HTML>'''


def gen_body(server, port, artifacts):
    '''	Generate the body portion for a single url
        - a report may contain multiple bodies (tables)
    '''
    applications, libraries = artifacts

    content = APPLICATION_HEADER % (server, port)
    for artifact in applications:
        content += TABLE_ROW % artifact
    content += TABLE_FOOTER

    if libraries:
        content += LIBRARY_HEADER
        for artifact in libraries:
            content += TABLE_ROW % artifact
        content += TABLE_FOOTER

    return content

def gen_report(report_id, report_components):
    ''' Generate a report with the specified report id
        given a list of of url, artificats '''
    report = PAGE_HEADER % (report_id, report_id)

    for (adminurl, artifacts) in report_components:
        (_protocol, server, port) = adminurl.split(':')
        server = server.lstrip('/')
        body = gen_body(server, port, artifacts)
        report += body

    now = time.localtime()
    now = time.strftime('%Y-%m-%d %H:%M', now)

    report += PAGE_FOOTER % (now,)
    return report

def _test_report():
    if len(sys.argv) not in [2, 4]:
        print
        print 'usage: wlst.sh', sys.argv[0], 'adminurl'
        print 'usage: wlst.sh', sys.argv[0], 'adminurl user password'
        print
        exit('', 1)

    adminurl = sys.argv[1]

    if len(sys.argv) == 2:
        #print adminurl
        artifacts = get_artifacts(adminurl)
    else:
        user = sys.argv[2]
        passwd = sys.argv[3]
        #print adminurl, user, passwd
        artifacts = get_artifacts(adminurl, user, passwd)

    if artifacts:
        (_protocol, server, port) = adminurl.split(':')
        server = server.lstrip('/')
        userid = server.split('-')[0] + port[:2]
        print 'calling gen_report'
        print gen_report(userid, [(adminurl, artifacts)])

if __name__ == "main":
    _test_report()


# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
