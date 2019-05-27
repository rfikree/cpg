#!/usr/bin/env python
'''
This program generates statistics from WebLogic or other access logs.
Log files should be in the standard CPO format and may be gzipped.
Parameters are removed from the path and paths are summarized by pattern.

After each file is parsed a line with the name of the parsed file
and the current number of path patterns is printed to stderr.

Files can be gzipped.

Paths are shortened to remove parameters and filenames. This
is done to reduce the output list size.

Options:
    --help:  Print this usage
    --output (-o) <file>: Output report to specified file (default stdout)
    --hits (-h) <hits> : Min hits to report line (default: 100)
    --time (-t) <seconds>:  Report only path patterns which exceeded time.
    --contents (-c) <pathSubstring>: Report only paths containing string
    --context: (-a) Report stats by content root (first item in path)
    --regex (-r) <regex>: Report only if path matches regex
    --format (-f) [1,2,3]: Select format to use (default: 1)
    --limits: (-l) Report limits (min, median, 95%, max) for response times

Output includes
  - count: number of hits for the specified pattern
  - mean response time with standard devation
  - response times (10%, median/50%, 90% and 95% percentiles)
  - the pattern the preceeding statistics apply to

Format values:
  1 - WebLogic
  2 - Nginx reverse proxy
  3 - WebSeal

'''
#  - response times (min, avg, 90%, and max)

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


def parseLog(fileName, data, contents, regex, format, context):
    ''' parse a named access log file updating
        statistics dictionary "data" is updated for each row
    '''

    divisor = 1
    if format == 1:
        pattern = r'\s(?P<time>\d+\.\d+)\s[^/]*?(?<=\s)(?P<path>/[^ \t?;]*)[ \t?;]'
    elif format == 2:
        pattern = r'\s(?P<path>/[^ \t?;]*)[ \t?;].*?\s(?P<time>\d+\.\d+)\s'
    elif format == 3:
        pattern = r'//[^/]*(?P<path>/[^ \t?;]*)[ \t?;].*\s(<time>\d{9}|range)\s'
        divisor = 1000000
    else:
        print('Invalid format specified - Exiting')
        sys.exit(-1)

    statsFeilds = re.compile(pattern)
    try:
        #print 'parseLog', fileName, len(data)
        for line in openLogFile(fileName):
            #print( 'parseLog', line[:-2] )
            if line[0] == '#':
                continue
            fields = statsFeilds.search(line)
            if not fields:
                continue
            timeTaken = fields.group('time')
            path = fields.group('path')
            #print( 'parseLog', timeTaken, path)
            if contents is not None and contents not in path:
                continue
            if regex is not None and not regex.search(path):
                continue
            key = parsePath(path, context)
            try:
              timeTaken = float(timeTaken) / divisor
            except ValueError:
                timeTaken = 120.0
            #print( 'parseLog', timeTaken, key )
            if key in data:
                data[key].extend((timeTaken,))
            else:
                data[key] = [ timeTaken, ]
            #print( 'parseLog', data[key] )
    except Exception, e:
        print ('Failed to process', fileName)
        print (e)
        return data

    return data

def parsePath(path, context=False):
    ''' parse a path converting to standard format.
        returning a normalized path (pattern)
    '''
    allUpperCase = re.compile('[-A-Z0-9._@]+$')
    fileExt = re.compile('[^.]+\.(?!page|jsf)\w+$')
    pathChanged = False

    if context:
        parts = path.split('/', 2)
        if len(parts):
            return = '/'.join(parts[:-1])
        else:
           return = path

    parts = path.split('/')


    # Replace numeric or uppercase path components (rest services, etc.)
    for i in range(1, len(parts)):
         if allUpperCase.match(parts[i]):
            parts[i] = '*'
            pathChanged = True

    #  Replace filename like component at end of path
    if fileExt.match(parts[-1]):
        parts[-1] = '*.' + parts[-1].split('.')[-1]
        pathChanged = True

    if pathChanged:
        path = '/'.join(parts)
    return path

def reportData(data, output, hits, rptTime, limits):
    ''' Report the access data to the specified ouput file.
        Only report data if count exceeds hits.
        If rptTime is specified, only report the data if a hit exceeds the limit.
        Data dictionary contains an array of hits for the key
    '''
    if limits:
        hdr = ('Count', 'Mean', 'SDev', 'Min', 'Med', '95%', 'Max', 'Path Pattern')
    else:
        hdr = ('Count', 'Mean', 'SDev', '10%', 'Med', '90%', '95%', 'Path Pattern')
    print ('%8s%7s%6s%7s%6s%6s%7s  %s' % hdr, file=output)

    for key in sorted(data.iterkeys()):
        if  len(data[key]) > hits or rptTime:
            (count, mean, stdDev, minTime, p5, p10, median, p90, p95, maxTime) = \
                genStats(data[key])
        if len(data[key]) > hits \
        and (not rptTime or maxTime > rptTime):
            if limits:
                cols = (count, mean, stdDev, minTime, median, p95, maxTime, key)
            else:
                cols = (count, mean, stdDev, p10,     median, p90, p95,     key)
            print ('%8d%7.2f%6.2f%7.2f%6.2f%6.2f%7.2f  %s' % cols, file=output)

def genStats(timeData):
    ''' Generate statistics from a series of time values
        Returns all statistics being reported.
    '''
    sum = 0.0
    count = len(timeData)
    #print( 'genStats', timeData )
    mean = math.fsum(timeData) / count
    d = [ (x - mean) ** 2 for x in timeData]
    stdDev = math.sqrt(math.fsum(d) / len(d))
    sortedData = sorted(timeData)
    #print( 'genStats', sortedData )
    minTime = sortedData[0]
    maxTime = sortedData[-1]
    if (count % 2 == 0) or count == 1:
        median = sortedData[count/2]
    else:
        median = (sortedData[count/2] + sortedData[count/2 + 1]) / 2
    p5 = sortedData[count/20]
    p10 = sortedData[count/10]
    p90 = sortedData[-count/10]
    p95 = sortedData[-count/20]
    #p99 = sortedData[-count/100]

    return (count, mean, stdDev, minTime, p5, p10, median, p90, p95, maxTime)

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
    format = 1
    hits = 100;
    limits = False
    output = sys.stdout
    outputSet = False
    regex = None
    rptTime = None
    pathContents = None
    context = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ac:f:h:lo:r:t:',
            ['contents=', 'context', 'format=', 'hits=', 'limits',
             'output=', 'regex=', 'time=', 'help'])

        for opt, arg in opts:
            if opt in ('-c', '--contents'):
                pathContents = arg
            elif opt in ('-a', '--context'):
                context = True
            elif opt in ('-f', '--format'):
                format = int(arg)
                if 1 > format or format > 3:
                    print ('format', format, 'out of range - setting to 1')
                    format = 1
            elif opt in ('-h', '--hits'):
                hits = int(arg)
            elif opt in ('-l', '--limits'):
                limits = True
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

    data = {}
    for fileName in args:
        data = parseLog(fileName, data, pathContents, regex, format, context)
        #if outputSet:
        #    print ('Parsed:', fileName, len(data), file=output)
        print ('Parsed:', fileName, len(data), file=sys.stderr)

    reportData(data, output, hits, rptTime, limits)

if __name__ == '__main__':
    main()

# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
