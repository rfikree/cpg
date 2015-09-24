#!/usr/bin/env python

""" LogMessageStats summarizes log file reporting message counts and
the logfile space utilized by the log file. """


import getopt
import os
import sys
import re

exceptionMatch = ''
exceptionRe = re.compile('^((Caused By: )?\S+Exception:|\s+at\s)')


def usage():
	print """
Usage: %s [OPTIONS] file [file...]

Sumarizes one or more log files reporting counts and size (bytes):
 - log messages
 - stack dumps by cpc classes

Options:
  -h, --help       Print this usage message
""" % ( sys.argv[0], )
	sys.exit(2)

def openLogFile(fileName):
	''' open a log file even if it is compressed
	'''
	if fileName.endswith('.gz'):
		return gzip.open(fileName, 'r')
	else:
		return open(fileName, 'r')

def processLine(line, stats):
	''' parse a line gathering stats
	'''
	match = re.search('(\w+) (ERROR|WARN) \[\[\w+\].*\] (\S+)', line)
	if match is not None:
		key = ' '.join(match.groups())
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(line))
		return

	match = re.search('<(Notice|Info|Warning|Error)>\s<([^>]+)>', line)
	if match is not None:
		key = ' '.join(match.groups())
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(line))
		return

	print 'processLine:', line,

def processException(lines, stats):
	''' parse an exception gathering stats
	'''

	#^(\S+?):(?:.*?\s+at\s.*?\()?([^)]+)?(?:.*?\sat\scom.cpc.*?\(([^)]+))?
	#match = re.search('^(^:]+).*\(((^[\)]+)\)+.*(?:com\.cpc\..*\((^[\)]\+\))?',
	#match = re.search('^(\S+?):(?:.*?\s+at\s.*?\(([^)]+))?(?:.*?\sat\scom.cpc.*?\(([^)]+))?',
	match = re.search('^(\S+?):(?:.*?\s+at\s.*?\(([^)]+))?(?:.*?\s+at\scom\.cpc\..*?\(([^)]+))?',
		lines, re.DOTALL)
	if match is not None:
		#print 'b:', match.groups()
		key = ''
		for group in match.groups():
			if group is not None:
				key = key + group + ' '
		key = key.strip()
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))
		#print key, '-', stats[key]
	else:
		print 'processException', lines,

def processFile(fileName, stats):
	''' process the lines in a file
	'''
	global exceptionMatch

	for line in openLogFile(fileName):
		#print 'Z', line,

		if not line.startswith('##'):
			#print 'Y', line,
			exceptionMatch = exceptionMatch + line
			continue

		if len(exceptionMatch):
			processException(exceptionMatch, stats)
			exceptionMatch = ''

		processLine(line, stats)

def reportStats(stats):
	#print stats

	details = []
	for item in stats:
		count, size = stats[item]
		details.append((count, size, item))

	details.sort(reverse=True)

	print
	print
	print '     Count    Log Bytes  Message Summary'
	print '==========  ===========  ==============================================='

	for detailLine in details:
		print '%10d %12d  %s' % detailLine
	print

def main():
	stats = dict()


	try:
		opts, args = getopt.getopt(sys.argv[1:], 'f:hl:p:u:v',
			['file=', 'help', 'logfile=', 'password=', 'user=', 'verify'])
	except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like 'option -a not recognized
		usage()

	for o, a in opts:
		if o in ('-h', '--help'):
			usage()


	if len(args) == 0:
		usage()

	for fileName in args:
		processFile(fileName, stats)

	reportStats(stats)

if __name__ == '__main__':
	main()

# EOF
