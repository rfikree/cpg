#!/usr/bin/env python -u
'''
This program generates statistics from java garbage logs.

After each file is parsed a line with the name of the parsed file
and the current number of url patterns is printed.

Options:
    --help:  Print this usage
    --output (-o) <file>: Output report to specified file (default stdout)

Output includes
  - count: number of occurences for the specified vake
  - mean value with standard devation
  - value (min, avg, 90%, and max)
  - a description for the preceeding statistics

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

def saveValue(data, key, value):
    if key is None:
        retrun

    try:
        value = int(value)
    except ValueError:
        value = float(value)

    if key in data:
        data[key].extend((value,))
    else:
        data[key] = [ value, ]

def saveResults(data, statTypes, match, keys):
    if match(0) in statTypes:
        idx = 1
        statName = statTypes(match(0))
        for key in keys:
            statDesc = key.format(*statNames)
            saveValue(data, statDesc, mattch(idx))
            idx = idx + 1
    else:
        print ('Unknown stat:', match(0))

def patternList():

        patterns = [
        # Application time: 58.2807710 seconds
        ('Application time: (\d+.\d+) seconds', None,
            ['Application Running Time *' ]),

        # Total time for which application threads were stopped:
        # 0.0134156 seconds
        ('Total time for which application threads were stopped: (\d+.\d+) seconds', None, [ 'Application Stopped Time **' ]),

        # DateStamp: 2013-12-17T09:53:16.515-0500:
        ('^[-0-9]+T[-+0-9:.]+: ', None, None),

        # TimeStamp: 1139.048:
        ('^\d+.\d\d\d: ', None, None),


        #### GC Types
        #  [ParNew: 287552K->31936K(287552K), 0.2527411 secs]
        ('\[ParNew: (\d+)K->(\d+)K\((\d+)K\), ([0-9.]+) secs\] ', 'ParNew' ,
            ['Mem YG ParNew Start', 'Mem YG ParNew End', 'Mem Capacity YG',
                'GC ParNew Time']),

        # [ParNew (promotion failed): 306432K->291806K(314560K), 1.1870679 secs]
        ('\[ParNew \(promotion failed\): (\d+)K->(\d+)K\((\d+)K\), ' +
            '([0-9.]+) secs\]', 'ParNew-Failed' ,
            ['Mem YG ParNew-Failed Start', 'Mem YG ParNew-Failed End',
                'Mem Capacity YG', 'GC ParNew-Failed Time']),

        # [YG occupancy: 235110 K (287552 K)], 2.5534417 secs]
        ('\[YG occupancy: (\d+) K \((\d+) K\)\]', 'YG occupancy',
            ['Mem YG occupancy', 'Mem Capacity YG']),

        # [CG 820444K(1013632K), 2.9377772 secs]
        ('\[GC: (\d+)K\((\d+)K\), ([0-9.]+) secs\]', 'GC occupancy',
            ['Mem CG occupancy', 'Mem Capacity CG', 'GC Time']),

        ## Parallel components
        # [PSYoungGen: 1273600K->25651K(1337216K)]
            ('\[PSYoungGen: (\d+)K->(\d+)K\((\d+)K\)\]', 'PSYoungGen',
            ['Mem PSYoungGen Start', 'Mem PSYoungGen End', 'Mem Capacity YG']),


        ## CMS components
        # [1 CMS-initial-mark: 1524140K(2826240K),]
        ('\[1 CMS-initial-mark: (\d+)K\((\d+)K\)\] ', 'CMS-initial-mark',
            ['Mem Tenured CMS-initial-mark', 'Mem Capacity Tenured']),

        # [1 CMS-remark: 1428486K(2826240K), 2.5844709 secs]]_
        ('\[1 CMS-remark: (\d+)K\((\d+)K\)\] ', 'CMS-remark',
            ['Mem Tenured CMS-remark', 'Mem Capacity Tenured']),

        # Labels: [CMS-concurrent-mark-start] etc.
        ('\[[^0-9]+\]', None, []),

        # [CMS-concurrent-mark: 7.809/8.303 secs]
        ('^\[CMS-concurrent-mark: ([0-9.]+)/[0-9.]+ secs\] ',
            'CMS-concurrent-mark', ['cms-initial-mark Time']),

        # [CMS-concurrent-preclean: 1.404/1.495 secs]
        ('\[CMS-concurrent-preclean: ([0-9.]+)/[0-9.]+ secs\] ',
            'CMS-concurrent-preclean', ['cms-initial-preclean Time']),

        # [CMS-concurrent-reset: 0.048/0.048 secs]
        ('\[CMS-concurrent-reset: ([0-9.]+)/[0-9.]+ secs\] ',
            'CMS-concurrent-reset', ['cms-initial-reset Time']),

        # [CMS-concurrent-sweep: 11.260/12.053 secs]
        ('\[CMS-concurrent-sweep: ([0-9.]+)/[0-9.]+ secs\] ',
            'CMS-concurrent-sweep', ['cms-initial-sweep Time']),

        # [CMS-concurrent-abortable-preclean: 7.656/8.582 secs]
        ('\[CMS-concurrent-abortable-preclean: ([0-9.]+)/[0-9.]+ secs\] ',
            'CMS-concurrent-abortable-preclean',
            ['cms-concurrent-abortable-preclean Time']),

        # [CMS Perm : 169050K->168647K(524288K)],
        ('\[CMS Perm : (\d+)K->(\d+)K\((\d+)K\)], ', None,
            ['Mem Perm CMS Start', 'Mem Perm CMS End',
                'Mem Capacity Perm']),

        # (concurrent mode failure): 1758120K->1545471K(2752512K),
        #  69.2610334 secs] 1980887K->1545471K(3106432K), [69.5677090 secs]
        (' \(concurrent mode failure\): (\d+)K->(\d+)K\((\d+)K\), ' +
            '([0-9.]+) secs\] (\d+)K->(\d+)K\((\d+)K\)\, ([0-9.]+) secs\] ',
        'CMS-Failure ***',
        ['Mem Tenured CMS-Failure Start', 'Mem Tenured CMS-Failure End',
            'Mem Capacity Tenured' ,'Time CMS-Failure Tenured',
            'Mem Heap CMS-Failure Start', 'Mem Heap CMS-Failure End',
            'Mem Capacity Heap' ,'Time CMS-Failure']
        ),

        # CMS: abort preclean due to time 2013-12-10T09:13:28.408-0500: 40586.441:
        (' CMS: abort preclean due to time [-+0-9T:.: ]+', None, None),


        ## Sub components
        # 122341.618: [grey object rescan, 0.0771828 secs]
        ('[0-9.]+: \[grey object rescan, ([0-9.]+) secs\]', None,
            ['grey object rescan']),

        # 122341.695: [root rescan, 0.7719949 secs]
        ('[0-9.]+: \[root rescan, ([0-9.]+) secs\]', None,
            ['root rescan']),

        # 122342.468: [weak refs processing, 0.0345054 secs]
        ('[0-9.]+: \[weak refs processing, ([0-9.]+) secs\]', None,
            ['weak refs processing']),

        # 122342.502: [class unloading, 0.4512499 secs]
        ('[0-9.]+: \[class unloading, ([0-9.]+) secs\]', None,
            ['class unloading']),

        # 122342.954: [scrub symbol & string tables, 0.3423001 secs]_
        ('[0-9.]+: \[scrub symbol & string tables, ([0-9.]+) secs\]', None,
            ['scrub symbol & string table']),

        # 122341.618: [Rescan (parallel) , 0.1003176 secs]
        ('[0-9.]+: \[Rescan \(parallel\) , ([0-9.]+) secs\]', None,
            ['rescan (parallel) Time']),

        # 122341.618: [Rescan (non-parallel) , 0.1003176 secs]
        ('[0-9.]+: \[Rescan \(non-parallel\) , ([0-9.]+) secs\]', None,
            ['rescan (non-parallel) Time']),

        # [PSYoungGen: 2797561K->845837K(2797568K)]
        (' \[PSYoungGen: (\d+)K->(\d+)K\((\d+)K\)\] ', None,
            ['Mem Heap PSYoungGen Start', 'Mem Heap PSYoungGen End **',
                'Mem Capacity YG']),

        # [ParOldGen: 2797561K->845837K(2797568K)]
        (' \[ParOldGen: (\d+)K->(\d+)K\((\d+)K\)\] ', None,
            ['Mem OldGen ParOldGen Start', 'Mem OldGen ParOldGen End **',
                'Mem Capacity OldGen']),

        # [PSPermGen: 400363K->400149K(524288K)]
        (' \[PSPermGen: (\d+)K->(\d+)K\((\d+)K\)\]', None,
            ['Mem Perm PSPermGen Start', 'Mem Perm PSPermGen End **',
                'Mem Capacity PermGen']),

        ## Final components
        # [CMS: 609333K->326371K(699072K), 16.9787561 secs]
        ('\CMS: (\d+)K->(\d+)K\((\d+)K\), ([0-9.]+) secs\] ', None,
            ['Mem Tenured CMS Start', 'Mem Tenured CMS End',
                'Mem Capacity Heap', 'GC CMS Time **	']),

        # [GC 1738806K(3113792K), 1.9288938 secs]
        ('\[GC (\d+)K\((\d+)K\), ([0-9.]+) secs\] ', None,
            ['Mem Heap %(t)s', 'Mem Capacity Heap', 'GC %(t)s Time **']),

        # [GC 647623.047: 1417354K->1172813K(3113792K), 0.3229452 secs]
        ('\[GC [0-9.]*: (\d+)K->(\d+)K\((\d+)K\), ([0-9.]+) secs\] ', None,
            ['Mem Heap %(t)s Start', 'Mem Heap %(t)s End **',
                'Mem Capacity Heap', 'GC %(t)s Time **']),

        # [GC 476062.160: 476063.425: [907722K->326371K(1013632K), [18.2455976 secs]
        ('\[GC [0-9.]*: [0-9.]*: \[(\d+)K->(\d+)K\((\d+)K\), \[([0-9.]+) secs\] ',
            None,
            ['Mem Heap %(t)s Start', 'Mem Heap %(t)s End **',
                'Mem Capacity Heap', 'GC %(t)s Time **']),

        # [Full GC 2781629K->1028364K(4134784K), 10.2525252 secs]
        ('\[Full GC (\d+)K->(\d+)K\((\d+)K\), ([0-9.]+) secs\] ', 'Full',
            ['Mem Heap Full Start', 'Mem Heap Full End *', 'Mem Capacity Heap',
            'GC Full Time **']),

        # [Full GC (System) 148407K->75046K(1047424K), 5.3975057 secs]
        ('\[Full GC \(System\) (\d+)K->(\d+)K\((\d+)K\), ([0-9.]+) secs\] ',
            'Full (System)',
            ['Mem Heap Full (System) Start', 'Mem Heap Full (System) End *',
            'Mem Capacity Heap', 'GC Full (System) Time **']),

        # [GC--  2781629K->1028364K(4134784K), 10.2525252 secs]
        ('\[GC--  (\d+)K->(\d+)K\((\d+)K\), ([0-9.]+) secs\] ', 'Full',
            ['Mem Heap -- Start', 'Mem Heap -- End *', 'Mem Capacity Heap',
            'GC -- Time **']),

        # [Times: user=1.80 sys=0.02, real=0.34 secs]
        ('\[Times: user=([0-9.]+) sys=([0-9.]+), real=([0-9.]+) secs\]', None,
            ['Time %(t)s User', 'Time %(t)s Sys', 'Time %(t)s Real *']),

        # [GC 223036.496: 223036.800: [CMS2014-01-17T11:53:18.872-0500: 223047.740:
        ('^\[GC [0-9.: ]+\[CMS[-+0-9T.: ]+', None, None),

        ]


        results = []

        for patternTupple in patterns:
            try:
                (regex, gcType, labels) = patternTupple
            except ValueError, e:
                print('Invalid patternTupple:', str(patternTupple))
                continue
            try:
                regex = re.compile(regex)
            except Exception, e:
                print('Regex compile failed', regex)
                print(e)
            results.append((regex, gcType, labels))

        return results


def savegroups(groups, labels, gcDict, data):
    #print( 'labels', len(labels), labels)
    #print( 'groups', groups)
    if len(groups) != len(labels):
        print( 'ERROR: groups size mismatch', len(groups), len(labels))
        return None

    for i in xrange(len(groups)):
        value = groups[i]
        valueName = labels[i] % gcDict
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                print (valueName, 'Invalid Value:', value)
                continue

        if valueName in data:
            data[valueName].append(value)
        else:
            data[valueName] = [ value, ]


def processLine(line, paterns, data):
    origLine = line
    line = line.rstrip()
    gcDict = {'t':'unknown'}
    #print ('line:', line)
    for (regex, gcType, labels) in paterns:
        match = regex.search(line)
        if match:
            if gcType:
                gcDict = {'t':gcType}
            #print( line[match.start():match.end()], match.groups())
            if match.groups():
                savegroups(match.groups(), labels, gcDict, data)
            line = line[:match.start()] + line[match.end():]
            #print ('line:', line)
            if not len(line):
                break
    if len(line) and origLine.endswith('\n'):
        print( 'Unmatched:"' + line + '"' )
        print( origLine )

def parseLog(fileName, data):

    ''' parse a named access log file updating
        statistics dictionary "data" for each row

        Patterns dictionary entries consist of an array of names for values.
        Use None to exclude a value, and an empty array to exclude a pattern.
    '''

    appTime = 'Application time:'
    linePref = None
    line = None
    patterns = patternList()

    try:
        #print 'parseLog', fileName, len(data)
        for line in openLogFile(fileName):
            #print( line )

            # Handle Application Time injection
            if not line.startswith(appTime) and appTime in line:
                splitLoc = line.find(appTime)
                linePref = line[:splitLoc]
                line = line[splitLoc:]
            elif linePref is not None:
                line = linePref + line
                linePref = None

            processLine(line, patterns, data)

    except Exception, e:
        print ('Failed to process', fileName)
        print ('Line: ', line)
        print (e)
        pass

    return data

def reportData(data, output):
    ''' Report the access data to the specified ouput file.
    '''
    ## Pick limits for lower and upper data
    #(divisor, lLow, lHigh) = (10, '10%', '90%')
    (divisor, lLow, lHigh) = (20, '05%', '95%')
    #(divisor, lLow, lHigh) = (100, '1%', '99%')

    totalAppTime=0.0
    appTimes = dict()

    print ('%8s %8s%7s %8s%8s%8s%8s%9s  %s' % ( 'Count', 'Mean', 'SDev',
        'Min', lLow, 'Med', lHigh, 'Max', 'Metric Description'),
        file=output)

    for key in sorted(data.iterkeys()):
        (count, mean, stdDev, minValue, low, median, high, maxValue) = \
            genStats(data[key], divisor)

        if isinstance(minValue, int):
            format = '%8d %8.0f%7.0f %8d%8d%8d%8d%9d  %s'
        else:
            format = '%8d %8.3f%7.3f %8.3f%8.3f%8.3f%8.3f%9.3f  %s'

        print (format % (
            count, mean, stdDev, minValue, low, median, high, maxValue, key),
            file=output)

        if key.startswith('Application'):
            totalAppTime += mean
            appTimes[key] = mean

    # Include Application time percentages
    print ('', file=output)
    for key in sorted(appTimes.iterkeys()):
        print ('%6.2f%% %s' % (100.0 * appTimes[key] / totalAppTime, key),
            file=output)


def genStats(valueData, divisor):
    ''' Generate statistics from a series of time values
        Returns all statistics being reported.
    '''
    sum = 0.0
    count = len(valueData)
    #print( 'genStats', valueData )
    mean = math.fsum(valueData) / count
    d = [ (x - mean) ** 2 for x in valueData]
    stdDev = math.sqrt(math.fsum(d) / len(d))
    sortedData = sorted(valueData)
    #print( 'genStats', sortedData )
    minValue = sortedData[0]
    maxValue = sortedData[-1]
    median = sortedData[count/2]
    rLow = sortedData[count/divisor]
    rHigh = sortedData[-count/divisor]

    return (count, mean, stdDev, minValue, rLow, median, rHigh, maxValue)

def usage(exitStatus=0):
    ''' Simple usage function using __doc__ for log form data
    '''
    print('\nUsage:', sys.argv[0].split('/')[-1], '[options] file...')
    print(__doc__)
    sys.exit(exitStatus)

def main():
    ''' Read options and process file(s)
    '''

    # Option defaults
    output = sys.stdout
    outputSet = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:',
            ['help', 'output='])

        for opt, arg in opts:
            if opt in ('-o', '-output'):
                output = open(arg, 'w')
                outputSet = True
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
        data = parseLog(fileName, data)
        if outputSet:
            print ('Parsed:', fileName, file=output)
        print ('Parsed:', fileName)

    reportData(data, output)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt, e:
        print ()
        print ('Processing cancelled')
        print ()

# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
