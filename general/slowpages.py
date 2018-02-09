#!/usr/bin/env python
'''
This program extract slow pages from WebLogic access logs.
Log files should be in the standard CPO format and may be gzipped.

For each slow page the access log line is printed prefixed with the instance from the logname.
The default time is 30.0 seconds.


Options:
    --help:  Print this usage
    --output (-o) <file>: Output report to specified file (default stdout)
    --time (-t) <seconds>:  Report all URL patterns with a hit over this time.
    --contents (-c) <urlSubstring>: Report only URLs containing string
    --regex (-r) <regex>: Report only if URL matches regex

The output file can be reprocessed to filter the result set from a prior run.

'''

from __future__ import print_function
import sys
import re
import math
import getopt
import gzip

def openLogFile(fileName):
    ''' open a log file even if it is compressed
    '''
    if fileName.endswith('.gz'):
        return gzip.open(fileName, 'r')
    else:
        return open(fileName, 'r')


def parseLog(fileName, output, rptTime, urlContents, regex):
    ''' parse a named access log file printing records with response times over the specified limit
    '''
    try:
        #print 'parseLog', fileName, len(data)
        stack = fileName.split('/')[-1][:16]
        for line in openLogFile(fileName):
            #print( 'parseLog', line[:-2] )
            if line[0] == '#':
                continue
            fields = line.split('\t')
            if len(fields) == 9:
                 (ip, aDate, aTime, method, status, bytes,
                    timeTaken, uri, userAgent) = fields
            elif len(fields) == 10:
               (stack, ip, aDate, aTime, method, status, bytes,
                    timeTaken, uri, userAgent) = fields
            else:
                continue
            if float(timeTaken) < rptTime:
                continue
            if urlContents is not None and urlContents not in uri:
                continue
            if regex is not None and not regex.search(uri):
                continue
            print (stack, line, sep='\t', end='', file=output)

    except Exception, e:
        print ('Failed to process', fileName)
        print (e)

def usage(exitStatus=1):
    ''' Simple usage function using __doc__ for log form data
    '''
    print('\nUsage:', sys.argv[0].split('/')[-1], '[options] file...')
    print(__doc__)
    sys.exit(exitStatus)

def main():
    ''' Read options and process file(s)
    '''

    # Option defaults
    hits = 100;
    output = sys.stdout
    outputSet = False
    regex = None
    rptTime = 30.0
    urlContents = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:h:o:r:t:',
            ['help', 'contents=', 'hits=', 'output=', 'regex=', 'time='])

        for opt, arg in opts:
            if opt in ('-c', '--contents'):
                urlContents = arg
            elif opt in ('-h', '-hits'):
                hits = int(arg)
            elif opt in ('-o', '--output'):
                output = open(arg, 'w')
                outputSet = True
            elif opt in ('-r', '--regex'):
                regex = re.compile(arg)
            elif opt in ('-t', '--time'):
                rptTime = float(arg)
            elif opt in ('--help'):
              usage()

    except getopt.GetoptError,e:
        print(e)
        usage(2)
    except Exception, e:
        print (e)
        usage(-1)

    if not args:
        usage()

    for fileName in args:
        parseLog(fileName, output, rptTime, urlContents, regex)


if __name__ == '__main__':
    main()

# EOF
