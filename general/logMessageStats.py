#!/usr/bin/env python

""" LogMessageStats summarizes log file reporting message counts and
the logfile space utilized by the log file. """


import getopt
import os
import sys
import re

exceptionMatch = ''
exceptionRe = re.compile('^((Caused By: )?\S+Exception:|\s+at\s)')

lineRe1 = re.compile('(\w+) (ERROR|WARN) \[\[\w+\].*\] (\S+)')
lineRe2 = re.compile('<(Debug|Notice|Info|Warning|Error)>\s<([^>]+)>')

exceptionRe = re.compile(
	'^(\S+?):(?:.*?\s+at\s.*?\(([^)]+))?(?:.*?\s+at\scom\.cpc\..*?\(([^)]+))?',
	re.DOTALL)


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
	match = lineRe1.search(line)
	if match is not None:
		key = ' '.join(match.groups())
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(line))
		return

	match = lineRe2.search(line)
	if match is not None:
		key = ' '.join(match.groups())
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(line))
		return

	print 'processLine:', line,

def processException(lines, stats):
	''' parse an exception gathering stats
	'''
	match = exceptionRe.search(lines)
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
	elif lines.startswith("Couldn't get price of SKUs") \
	or   lines.startswith("  Status Message Code: NoRateFoundPSID"):
		key = "Couldn't get price of SKU(s)"
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))
	elif lines.startswith('Error Code: '):
		key = (' ').join(lines.split(None, 4)[:4])
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))
	else:
		key = "Unhandled case:" + lines.split(None, 2)[0]
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))
		print 'Unmatched Case:', lines,

def processFile(fileName, stats):
	''' Process the lines in a file gathering summary data.
		Gathers multiple message lines for summarization.
	'''
	global exceptionMatch

	for line in openLogFile(fileName):
		#print 'Z', line,

		if not line.startswith('##'):
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
