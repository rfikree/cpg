#!/usr/bin/env python

""" LogMessageStats summarizes log file reporting message counts and
the logfile space utilized by the log file. """

from optparse import OptionParser
import fileinput
import sys
import re


linePatterns = [
	'(\w*-?\w+) (ERROR|WARN):? \[\[\w+\].*\] (\S+)',
	'<(Debug|Notice|Info|Warning|Error)>\s<(.*?)>.*<(.*)>',
]

# Patterns with no match groups will be ignored; use ?(...) for non-grouping
# Patterns with optional match groups will crash the program.
exceptionPatterns = [
	r'^\S+ <[^\n]*> <\S+ \S+ ([^<0-9]\S+) (ERROR|WARN).*?(^\S+).*? at (com\.?(cpc|pur)\S*?)\(([^)]+)',
	r'^\S+ <[^\n]*> <\S+ \S+ ([^<0-9]\S+) (ERROR|WARN) \[\[\w+\].*?\] (\S+).*?(\S*)>',
	r'^\S+ <[^\n]*> <\S+ \S+ ([^<0-9]\S+) (ERROR|WARN).*?(^\S+)',
	r'^\S+ <[^\n]*> (ERROR|WARN).*?(^\S+).*? at (com\.?(cpc|pur)\S*?)\(([^)]+)',
	r'^\S+ <[^\n]*> (ERROR|WARN).*?(^\S+).*?^uri :\[(\S*?)\]',
	r'^\S+ <[^\n]*> (ERROR|WARN).*?(^\S+)',
	r'^\S+ <[^\n]*> <\S+ \S+ \S+ INFO',
	r'^\S+ <[^\n]*? (INFO).*?(^\S*)',
	r'^\S+ <(Error)>.*?path:/(\S+).*?(^\S+).*? at (com\.?(cpc|pur)\..*?\(([^)]+))',
	r'^\S+ <(Error).*?(^\S+).*?\s+at (weblogic\..*?\(([^)]+))',
	r'^\S+ <Notice> <[^\n]*DefaultTimeBasedFileNamingAndTriggeringPolicy',
	r'^\S+ <(Notice)> [^\n]*?(In|Out)bound Message',
	r'^\S+ <(Notice)>.*?(^\S+).*? at (com\.?(cpc|pur)\..*?\(([^)]+))',
	r'^\S+ <(Notice)>.*?/(\S+).*?(^\S+)',
	r'^\S+ <(Notice)>.*?/(\S+).*?(^\S+)',
	r'^\S+ <Notice> <[^\n]*\{svc=\w+, result=OK,',
	r'^\S+ <Info> <JDBC> ',
]


lineRegexes = []
for pattern in linePatterns:
	lineRegexes.append(re.compile(pattern))

exceptionRegexes = []
for pattern in exceptionPatterns:
	exceptionRegexes.append(re.compile(pattern,re.DOTALL + re.MULTILINE))


def processLine(line, stats):
	''' parse a line gathering stats
	'''
	for regex in lineRegexes:
		match = regex.search(line)
		if match is not None:
			break

	if match is not None:
		if match.group(1) not in ('Info', 'Notice', 'Warning'):
			key = ' '.join(match.groups())
			count, size = stats.get(key, (0, 0))
			stats[key] = (count + 1, size + len(line))
	else:
		print >> sys.stderr, ':'.join((fileName, str(messageLineNo))), \
			'processLine:', line


def processException(lines, stats):
	''' parse an exception gathering stats
	'''
	key = ''
	allLines= ''.join(lines)
#	match = exceptionRe1.search(allLines)
#	if match is not None:
#		match = exceptionRe2.search(allLines)

	for regex in exceptionRegexes:
		match = regex.search(allLines)
		if match is not None:
			break

	if match is not None:
		if not match.groups():
			return

		key = ' '.join(match.groups())

		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(allLines))

	else:
		print >> sys.stderr, ':'.join((fileName, str(messageLineNo))), \
			'Unmatched Case:', allLines


def processFiles(fileNames, stats):
	''' Process the lines in the files gathering summary data.
		Gathers multiple message lines for summarization.
	'''
	global exceptionLines
	global fileName
	global messageLineNo
	exceptionLines = []

	for line in fileinput.input(fileNames, openhook=fileinput.hook_compressed):

		if fileinput.isfirstline():
			fileName = fileinput.filename()
			if exceptionLines:
				processException(''.join(exceptionLines), stats)
				exceptionLines = []

		if line.startswith('##') and exceptionLines:
			processException(exceptionLines, stats)
			exceptionLines = []

		if not(line.startswith('##') and line.rstrip().endswith('>')):
			if not exceptionLines:
				messageLineNo = fileinput.filelineno()
			exceptionLines.append(line)
			continue

		messageLineNo = fileinput.filelineno()
		processLine(line, stats)

	if exceptionLines:
		processException(exceptionLines, stats)
		exceptionLines = []

	fileinput.close()


def reportStats(stats):

	details = []
	for item in stats:
		count, size = stats[item]
		details.append((count, size, item))

	details.sort(reverse=True)

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
