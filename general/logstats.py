#!/usr/bin/env python
'''
This program generates statistics from WebLogic access logs.
Log files should be in the standard CPO format and may be gzipped.
Parameters are removed from the URL and URLs are summarized by pattern.

After each file is parsed a line with the name of the parsed file
and the current number of url patterns is printed.

URLS are shortened to remove parameters, and session ids.  Further shortening
is done to reduce the output list size.

Options:
	--help:  Print this usage
	--output (-o) <file>: Output report to specified file (default stdout)
	--hits (-h) <hits> : Min hits to report line (default 100)
	--time (-t) <seconds>:  Report all URL patterns with a hit over this time.
	--contents (-c) <urlSubstring>: Report only URLs containing string

Output includes
  - count: number of hits for the specified pattern
  - mean response time with standard devation
  - response times (min, avg, 90%, and max)
  - the pattern the preceeding statistics apply to

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


def parseLog(fileName, data, contents):
	''' parse a named access log file updating
		statistics dictionary "data" is updated for each row
	'''
	try:
		#print 'parseLog', fileName, len(data)
		for line in openLogFile(fileName):
			#print( 'parseLog', line[:-2] )
			if line[0] == '#':
				continue
			fields = line.split('\t')
			if len(fields) != 9:
				continue
			(ip, aDate, aTime, method, status, bytes,
				timeTaken, uri, userAgent) = fields
			if contents is not None and contents not in uri:
				continue
			key = parseURI(uri)
			timeTaken = float(timeTaken)
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

def parseURI(uri):
	''' parse a URI converting to standard format.
		returning a key (URL pattern)
	'''
	allUpperCase = re.compile('[-A-Z0-9._@]+$')
	fileExt = re.compile('[^.]+\.(?!page)\w+$')
	urlChanged = False

	#print( 'parseLine', timeTaken, uri )
	key = uri.split('?')[0].split(';')[0]
	parts = key.split('/')

	# Replace numeric or uppercase URL componentss (/rs)
	for i in range(1, len(parts)):
		#if allDigits.match(parts[i]) or allUpperCase.match(parts[i]):
		if allUpperCase.match(parts[i]):
			parts[i] = '*'
			urlChanged = True
		#elif upperCaseExt.match(parts[i]):
		#	parts[i] = parts[i].split('.')[0] + '.*'
		#	urlChanged = True

	#  Replace filename like component at end of URL
	if fileExt.match(parts[-1]):
		parts[-1] = '*.' + parts[-1].split('.')[-1]
		urlChanged = True

	if urlChanged:
		key = '/'.join(parts)
	return key

def reportData(data, output, hits, rptTime):
	''' Report the access data to the specified ouput file.
		Only report data if count exceeds hits.
		If rptTime is specified, report the data if a hit exceeds the hit time.
		Data dictionary contains an array of hits for the key
	'''
	print ('%8s%7s%6s%7s%6s%6s%7s  %s' % (
		'Count', 'Mean', 'SDev', '10%', 'Med', '90%', '95%', 'URL Pattern'),
		file=output)
#		'Count', 'Mean', 'SDev', 'Min', 'Med', '95%', 'Max', 'URL Pattern'),
	for key in sorted(data.iterkeys()):
		if  len(data[key]) > hits or rptTime:
			(count, mean, stdDev, minTime, p5, p10, median, p90, p95, maxTime) = \
				genStats(data[key])
		if len(data[key]) > hits \
		or (rptTime and maxTime > rptTime) :
			print ('%8d%7.2f%6.2f%7.2f%6.2f%6.2f%7.2f  %s' % (
				count,  mean, stdDev, p10, median, p90, p95, key),
				file=output)
#				count,  mean, stdDev, minTime, median, p95, maxTime, key),

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
	if (count % 2 = 0):
		median = sortedData[count/2]
	else:
		median = (sortedData[count/2] + sortedData[count)/2 + 1]) / 2
	p5 = sortedData[count/20]
	p10 = sortedData[count/10]
	p90 = sortedData[-count/10]
	p95 = sortedData[-count/20]
	
	return (count, mean, stdDev, minTime, p5, p10, median, p90, p95, maxTime)

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
	hits = 100;
	output = sys.stdout
	outputSet = False
	rptTime = None
	urlContents = None

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'c:o:h:t:',
			['help', 'contents=' 'output=', 'hits=', 'time='])

		for opt, arg in opts:
			if opt in ('-c', '--contents'):
				urlContents = arg
			elif opt in ('-h', '-hits'):
				hits = int(arg)
			elif opt in ('-o', '--output'):
				output = open(arg, 'w')
				outputSet = True
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
		data = parseLog(fileName, data, urlContents)
		if outputSet:
			print ('Parsed:', fileName, len(data), file=output)
		print ('Parsed:', fileName, len(data))

	reportData(data, output, hits, rptTime)

if __name__ == '__main__':
	main()

# EOF
