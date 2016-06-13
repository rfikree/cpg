#!/usr/bin/env python

""" LogMessageStats summarizes log file reporting message counts and
the logfile space utilized by the log file. """

from optparse import OptionParser
import fileinput
import sys
import re


exceptionRe = re.compile('^((Caused By: )?\S+Exception:|\s+at\s)')

lineRe1 = re.compile('(\w*-?\w+) (ERROR|WARN):? \[\[\w+\].*\] (\S+)')
lineRe2 = re.compile('<(Debug|Notice|Info|Warning|Error)>\s<(.*?)>.*<(.*)>')

rePatterns = [
	'(\w*-?\w+) (ERROR|WARN).*?(^\S+).*?\s+at\s(com\.cpc\S*)\(([^)]+)?',
	'<(Error)>.*path:/(\S+).*?(^\S+).*?\s+at\s(com\.cpc\..*?\(([^)]+))?',
	'<(Notice)>.*?/(\S+).*(^\S+).*?\s+at\s(com\.cpc\..*?\(([^)]+))?',
	'(\w*-?\w+) (ERROR|WARN):? \[\[\w+\].*\] (\S+).*(\S*)>',
]

exceptionRegexs = []
for pattern in rePatterns:
	exceptionRegexs.append(re.compile(pattern,re.DOTALL + re.MULTILINE))

exceptionRe1 = re.compile('(\w*-?\w+) (ERROR|WARN).*?(^\S+).*?\s+at\s(com\.cpc\S*)\(([^)]+)?',
	re.DOTALL + re.MULTILINE)
exceptionRe2 = re.compile('<(Error)>.*path:/(\S+).*?(^\S+).*?\s+at\s(com\.cpc\..*?\(([^)]+))?',
	re.DOTALL + re.MULTILINE )
#	'^(\S+?):(?:.*?\s+at\s.*?\(([^)]+))?(?:.*?\s+at\scom\.cpc\..*?\(([^)]+))?',

atRe = re.compile('\s+at ([^(]+)')
errorRe = re.compile('<(Error)>.*path=/(\S+)')

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
		if match.group(1) not in ('Info', 'Notice', 'Warning'):
			key = ' '.join(match.groups())
			count, size = stats.get(key, (0, 0))
			stats[key] = (count + 1, size + len(line))
			#print match.group(1), line
		return

	print exceptionLineNo, 'processLine:', line


def processException(lines, stats):
	''' parse an exception gathering stats
	'''
	key = ''
	allLines= ''.join(lines)
#	match = exceptionRe1.search(allLines)
#	if match is not None:
#		match = exceptionRe2.search(allLines)

	for regex in exceptionRegexs:
		match = regex.search(allLines)
		if match is not None:
			break

	if match is not None:
		#print 'b:', match.groups()
		for group in match.groups():
			if group is not None:
				key += group + ' '
		key = key.rstrip()
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))

	elif lines[1].startswith("Couldn't get price of SKUs") \
	or   lines[1].startswith("  Status Message Code: NoRateFoundPSID"):
		key = "Couldn't get price of SKU(s)"
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))

	elif lines[1].startswith('java.lang.IllegalStateException'):
		key = errorRe.findall(lines[0])
		print key
		key.append(lines[1].rstrip())
		key = (' ').join(key)
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))

	elif lines[1].startswith('Error code:'):
		key = (' ').join(lines[1].split(None, 4)[:4])
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))

	elif lines[1].startswith('org.springframework.'):
		key = ' '.join(('springframework', lines[1].split(': ')[1]))
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))

	elif len(lines) > 2 and  lines[2].startswith('java.lang'):
		key = lines[2].rstrip() + ' '
		key += atRe.findall(lines[3])[0]
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))



#	else:
#		match = exceptionRe2.search(allLines)
#		if match:
#			print ### Matched re2
#			print ''.join(lines[:5])
#			for group in match.groups():
#				if group is not None:
#					key += group + ' '
#				key = key.strip()
#			count, size = stats.get(key, (0, 0))
#			stats[key] = (count + 1, size + len(lines))
	else:
		key = "Unhandled case:" + lines[1]
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(lines))
		print exceptionLineNo, 'Unmatched Case:', allLines
		print

def processFiles(fileNames, stats):
	''' Process the lines in the files gathering summary data.
		Gathers multiple message lines for summarization.
	'''
	global exceptionMatch
	global exceptionLineNo
	exceptionMatch = []
	exceptionLineNo = -2

	for line in fileinput.input(fileNames):

		if fileinput.isfirstline():
			if exceptionMatch:
				processException(''.join(exceptionMatch), stats)
				exceptionMatch = []
				exceptionLineNo = -1

		if not(line.startswith('##') and line.rstrip().endswith('>')):
			if not exceptionMatch:
				exceptionLineNo = fileinput.filelineno()
			exceptionMatch.append(line)
			continue

		if exceptionMatch:
			processException(exceptionMatch, stats)
			exceptionMatch = []

		processLine(line, stats)

	fileinput.close()

def reportStats(stats):

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

	usage= '''
usage: %prog [options] file [file...]

Sumarizes one or more log files reporting counts and size (bytes):
 - log messages
 - stack dumps by cpc classes
'''

	parser = OptionParser(usage=usage)
	(options, args) = parser.parse_args()

	if args:
		stats = dict()
		processFiles(args, stats)
	else:
		print "FATAL: no files specified"
		parser.print_help()


	reportStats(stats)

if __name__ == '__main__':
	main()

# EOF
