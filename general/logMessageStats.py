#!/usr/bin/env python

""" LogMessageStats summarizes log file reporting message counts and
the logfile space utilized by the log file. """

from optparse import OptionParser
import fileinput
import sys
import re


linePatterns = [
	' ([^<0-9]\S+) (ERROR) .+ (MissingProperty.+)>',
	' ([^<0-9]\S+) (ERROR|WARN):? \[\[\w+\].+\] (\S.+?)(?: ?[-:\n(\?])',
	' (ERROR) \S+ (\S+) .+?(File not found:.+?)>',
	'^\S+ <(Error)> <(CpgIdentityJAASAsserterLogger)>.+(Failed to lookup customer profile)',
	'^\S+ <(.+?)> <(.+?)>.+<(.?)>',
]

# Patterns with no match groups will be ignored; use (?:...) for non-capture
# Patterns with optional match groups will crash the program.
exceptionPatterns = [
	# Captured StdErr Messages
	r'^\S+ <Notice> <(StdErr)> .+? (com\.hazelcast\..*)',
	r'^\S+ <Notice> <(StdErr)> (?ms).+?(^SEVERE): \w+: (.+?)[>\n]',
	r"^\S+ <Notice> <(StdErr)> (?ms).+?^(INFO|WARNING): .+? '(\w+\w+.+?)['@]",
	r"^\S+ <Notice> <(StdErr)> (?ms).+?(^WARNING): .+? serviceName='(.+?)'",

	# Single line matches
	r'^\S+ <Notice> <.+? (INFO) \[\[\w+\].+?\] (\S+ (?:In|Out).+)',
	r'^\S+ <Notice> <.+? (INFO) (\S+ - (?:In|Out)\S+ \S+)',
	r'^\S+ <Notice> <.+? {svc=\w+, result=OK,',
	r'^\S+ <Notice> <.+? c.q.l.core.rolling.DefaultTimeBasedFileNamingAndTriggeringPolicy',
	r'^\S+ <Notice> <.+? (ERROR) .* (bad SQL grammar.+?\])',
	r'^\S+ <Notice> <.+? (ERROR|WARN|INFO) \[\[\w+\].+?\] (.+?) \w+:',

	# ui-cpo ERROR ...
	r'^\S+ <Notice> <.+ ([^<0-9]\S+) (ERROR|WARN) (?ms).+?(^\S+).+?at (com\.(?:cpc|pur)\S+)',
	r'^\S+ <Notice> <.+ ([^<0-9]\S+) (ERROR) \[\[\w+\].+?\] (com\S+)',
	r'^\S+ <Notice> <.+ ([^<0-9]\S+) (ERROR) (?ms).+?(^\S.+?)[-\n(\?]',
	r'^\S+ <(N)otice> <.+ ([^<0-9]\S+) (INFO) (?ms).+?(^\S+).+?at (com\.(?:cpc|pur)\S+)',
	r'^\S+ <(No)tice> <.+ ([^<0-9]\S+) (WARN|INFO) \[\[\w+\].+?\] (com\S+)',
	r'^\S+ <(Not)ice> <.+ ([^<0-9]\S+) (WARN|INFO) (?ms).+?(^\S.+?)[-:\n(\?]',

	# Multiline matches ...
	r'^\S+ <Notice> <.+? (ERROR) (?ms).*?(^\w\S+).+?at (com\.(?:cpc|pur)\S+)',
	#r'^\S+ <(N)otice> <.+? (WARN|INFO) (?ms).*?(^\w\S+).+?at (com\.(?:cpc|pur)\S+)',
	r'^\S+ <Notice> <.+? (ERROR) \S+ \S+ (site not (?ms)valid:).+?^uri :\[(\S+?)\]',
	#r'^\S+ <(Not)ice> <.+ (WARN|INFO) (?ms).+?(^\w\S+).+?^uri :\[(\S*?)\]',

	# Last ditch notice handlers
	r'^\S+ <Notice> <.+ (ERROR) (?ms).+?^ExceptionMessage{.+?(^\w\S.+?)[-:\n(\?]',
	#r'^\S+ <(Noti)ce> <.+ (WARN|INFO) (?ms).+?^ExceptionMessage{.+?(^\w\S.+?)[-\n(\?]',
	r'^\S+ <Notice> <.+ (ERROR|WARN|INFO) (?ms).+?(^\w\S.+?)[-:\n(\?]',

	# Error messages reported by WebLogic
	r'^\S+ <(Error)> .+?path:/(\S+) (?ms).+?(^\S+).+?at (com\.(?:cpc|pur)\.\S+)',
	r'^\S+ <(Error)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <(WebLogicServer)> .+? <\[(STUCK)\] (?ms).+?(^\w.+?)[-:\n(\?]',
	r'^\S+ <(Warning)> <(JDBC)> .+? <(Forcibly releasing) inactive/harvested (connection) ".+?" .+? (".+?")',
	r'^\S+ <Info> <JDBC>',

	# Stray XML
	r'^\s*(<.+?>)',
]

lineRegexes = []
for pattern in linePatterns:
	lineRegexes.append(re.compile(pattern))

exceptionRegexes = []
for pattern in exceptionPatterns:
	#print pattern
	exceptionRegexes.append(re.compile(pattern))


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
	re = None
#	match = exceptionRe1.search(allLines)
#	if match is not None:
#		match = exceptionRe2.search(allLines)

	for regex in exceptionRegexes:
		match = regex.search(allLines)
		if match is not None:
			re = regex
			break

	if match is not None:
		if not match.groups():
			return

		key = ' '.join(match.groups())
		#if 'WARN' in  key:
		#	print 'WAT key', key
		#	print 'WAT pattern', regex.pattern
		#	print

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
