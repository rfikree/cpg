#!/usr/bin/env python
'''
Download OWS application files from Teamcity into a versioned directory.
Intended to provide equivelant functionality to what is provided for
WebLogic applications.

Created: 2018-03-29
@author: Bill Thorsteinson
'''

from optparse import OptionParser
import os
import urllib2
import urllib
import xml.etree.ElementTree
from collections import namedtuple


#### Update defaults here
parser = OptionParser(version="20180329-beta")
parser.set_defaults(
    server='http://tcity.cpggpc.ca:8111',
    urlpath='/guestAuth/app/rest/builds/id:%(id)s/artifacts/',
    directory='.',
    verbose=False)


#### Application starts here.

def getSources(options, data=None):
    '''Get the list of sources from the artifacts metadata as
    tuples (name, size, href).  href is converted from metadata to file'''

    sources = []
    url = ''.join((options.server, options.urlpath))
    if hasattr(options, 'id'):
        url = url % {'id': options.id}
    if options.verbose:
        print 'url:', url, '\n'

    page = urllib2.urlopen(url, data, timeout=10)
    content = page.read()

    root = xml.etree.ElementTree.fromstring(content)
    for content in root.findall('file'):
        name = content.get('name')
        size = content.get('size')
        href = content.get('href').split('/')
        href[-2] = 'files'
        href = '/'.join(href)
        sources.append((name, size, href))

    return sources


def getPath(options, sources):
    '''Get the relative path for this version from the sources list.
    Assumes that anything after the last hyphen is a version in the form
    YYYY,MM.Build.type.  Checks for first occurrence of a known versioned
    format, as not all files have versions in their name'''

    for (name, size, href) in sources:
        for deliminator in ('-deploy-', '-env-', '-war-'):
             if deliminator in name:
                app = name.split(deliminator)[0]
                break

    #print 'name:', name
    release = name.split('-')[-1]
    build = release.split('.')[-2]
    release = '.'.join(release.split('.')[:2])

    path =  '/'.join((options.directory, app, release, build))
    if options.verbose:
        print 'path:', path, '\n'

    return path


def downloadFiles(options, path, sources):
    '''Download all the files from the server creating the destination
    directory if necessary.'''

    try:
        os.makedirs(path, 0755)
    except OSError as e:
        if e.errno == 17:
            pass

    for (name, size, href) in sources:
        dest = '/'.join((path, name))
        url = ''.join((options.server, href))
        if options.verbose:
            print 'fetching:', url, dest, size
        urllib.urlretrieve(url, dest)


def processRequest(options):
    sources = getSources(options)
    path = getPath(options, sources)
    downloadFiles(options, path, sources)


def main(parser):
    '''Parse the command line and perform all the required actions
    to download the files for the specified build.
    '''
    parser.usage='''
Download OWS build artifacts into a release directory.

Usage: %prog [options] [ID]

At least -i or -p options must be set.'''

    parser.add_option('-s', '--server', dest='server',
                      type='string', action='store', metavar='SERVER',
                      help='File server in URL form')
    parser.add_option('-p', '--path', dest='urlpath',
                      type='string', action='store', metavar='URLPATH',
                      help='urlpath for file including %%(id)s where id belongs')
    parser.add_option('-i', '--id', dest='id',
                      type='string', action='store', metavar='ID',
                      help='build id to be substituted into urlpath')
    parser.add_option('-d', '--directory', dest='directory',
                      type='string', action='store', metavar='DIRECTORY',
                      help='directory into which to download files')
    parser.add_option('-v', '--verbose', dest='verbose',
                      action='store_true',
                      help='report actions')

    options, args = parser.parse_args()

    # A single argument can be used instead of the -i option
    # Otherwise fail as no used arguement should be passed.
    # Fails if both -i and a sing arguement are passed.
    if args:
        if len(args) == 1 and not options.id:
            options.id = args[0]
        else:
            print 'args:', args
            parser.print_help()
            exit(-99)

    processRequest(options)



# Mainline - execute the main function

main(parser)


# EOF