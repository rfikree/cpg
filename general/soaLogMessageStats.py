#!/usr/bin/env python

""" LogMessageStats summarizes log file reporting message counts and
the logfile space utilized by the log file. """

from optparse import OptionParser
import fileinput
import sys
import re


missedLinePattern = ' (ERROR|WARN|INFO|DEBUG|SEVERE|FATAL)'
missedLineRegex = re.compile(missedLinePattern)
stdIOLinePattern = '^[^>]+> <Notice> (<Std\w+>) .+ <([^>]+)>'
stdIOLineRegex = re.compile(stdIOLinePattern)


# Patterns with no match groups will be ignored; ue (?:...) for non-capture
# Patterns with optional match groups will crash the program.

linePatterns = [
	# SOA Patterns
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?BEA-000000> <\s?(\S+(?: [^0-9 >{[]+){,4})",
	"^[^>]+> <(Warning|Error)> <(Coherence)> .+?BEA-000000> .+ (Experienced a) .* (communication delay)",
	"^[^>]+> <(Warning|Error)> <(Connector|Diagnostics|EJB|J2EE|Munger|RJVM|SDF|Security|Socket|Store|oracle\.\S+)> .+?((?:BEA|JMX|OWS|SDP)-\d+)> <\s?(\S+(?: [^0-9 >[]+){,4})",
	"^[^>]+> <(Warning|Error)> <(oracle\.adf\S+?)> .+?(ADF_FACES-\d+)> <\s?(\S+(?: [^0-9 >]+){,4})",
	"^[^>]+> <(Warning|Error)> <(oracle\.a\S+?)> .+?(JMS-\d+)> <\s?(\S+(?: [^0-9 >]+){,4})",
	"^[^>]+> <(Warning)> <(EclipseLink)> .+?(BEA-2005000)> .+?--((?:\w+ ){2,9})",
	"^[^>]+> <(Warning)> <(JNDI)> .+?(BEA-050001)> <(WLContext.close\(\) was called in a different thread)",

	# WebLog logging messages
	"^\S+ <Notice> <Stdout> .+?BEA-000000> .+<LoggingService>",

	# Stdout messages - By format
	# Date Application Level Thread Message (CPO)
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S{10} \S+ ([a-z]\S+) (ERROR|WARN|INFO) \[\[\w+\].+?\] ([^> ]+(?: -)?(?: [^-0-9@:>=' []+){,4})",
	# Date Level Thread Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\S+ (ERROR|WARN|INFO) \[\[\w+\].+?\] ([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",
	# Date Level ?? Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\S+ (ERROR|WARN|INFO) +\[\S+\] ([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",
	# Date Thread Level Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\S+ \[\[\w+\].+?\] (ERROR|WARN|INFO) +([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",
	# Date Application Level Message (CPO WebServices)
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\d{4}\S{6} \S+ ([a-z]\S+) (ERROR|WARN|INFO) ([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",

	# WebLogic Info messages
	'^[^>]+> <Info> ',
	'^[^>]+> <Notice> <(?:Cluster|Log Management|Security|Server|WebLogicServer)>',
]


# Match multiline first to get usable details.  Then match single line message
exceptionPatterns = [
	# SOA Patterns
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?BEA-000000> (?ms)<(JMSAdapter[^:](?: [^0-9 >{[]+){,4}).*?$\s(\w\S+[^0-9>\n\([]*)",
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?BEA-000000> (?ms).+?$\s(\w\S+[^0-9>\n[]*)",
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?(SOA-\d+)> (?ms).+?$\s(\w+[^0-9>\n[]*)",
	"^[^>]+> <(Warning|Error)> <(Connector|Diagnostics|EJB|JMX)> .+?(BEA-\d+)> (?ms).+?$\s(\w[^0-9>\n\([]*)",
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?BEA-000000> <\s?(\S+(?: [^0-9 >{[]+){,4})",
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?(OWS-\d+)> <\s?(\S+(?: [^0-9 >{[]+){,4})",
	"^[^>]+> <(Warning|Error)> <(Default)> .+?(JMX-\d+)> (?ms).+?$.*?^(\w.*?)$",
	"^[^>]+> <(Error)> <(WebLogicServer)> .+?(BEA-000337)> <\[(STUCK)",
	"^[^>]+> <Notice> <Diagnostics> .*?BEA-320068> <Watch 'StuckThread' with severity 'Notice'",

	# Startup notices
	'^\S+ <Notice> <Security> .+? Loading trusted certificates',
	'^\S+ <Notice> <Security> .+? Using default',
	'^\S+ <Notice> <StdErr> .+? INFO: Registering Spring bean,',

]



lineRegexes = []
for pattern in linePatterns:
	try:
		lineRegexes.append(re.compile(pattern))
	except Exception:
		print >> sys.stderr, 'Invalid regex:', pattern

exceptionRegexes = []
for pattern in exceptionPatterns:
	try:
		exceptionRegexes.append(re.compile(pattern))
	except Exception:
		print >> sys.stderr, 'Invalid regex:', pattern


def processLine(line, stats):
	''' parse a line gathering stats
	'''
	#return
	for regex in lineRegexes:
		match = regex.search(line)
		if match is not None:
			break

	if match is not None:
		if not match.groups():
			return
		try:
			key = ' '.join(match.groups())
		except:
			print 'Key Failure:', str(match.groups())
			print regex.pattern
			print line
			return
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(line))

		#if 'Stdout WARN XSS' in key:
		#	print 'WAT key', key
		#	print 'WAT pattern', regex.pattern
		#	print line

	else:
		missed = missedLineRegex.search(line)
		stdIO = stdIOLineRegex.search(line)
		if stdIO is not None and not missed:
			if stdIO.group(2).startswith('at '):
				message = ('%s     %s') % stdIO.groups()
			else:
				message = ('%s %s') % stdIO.groups()
			print >> sys.stderr, ':'.join((fileName, str(messageLineNo))), \
				message
		else:
			print >> sys.stderr, ':'.join((fileName, str(messageLineNo))), \
				'Unhandled:', line


def processException(lines, stats):
	''' parse an exception gathering stats
	'''
	#return
	key = ''
	allLines= ''.join(lines)
	if len(allLines) == 250:
		print allLines

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

		#if '\n' in key:
		#if 'StdErr' == key:
		#	print 'WAT key', key
		#	print 'WAT pattern', regex.pattern
		#	print  ' ** '.join(match.groups())
		#	print allLines

	else:
		print >> sys.stderr, ':'.join((fileName, str(messageLineNo))), \
			'Unmatched:', allLines


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

	usage= '''%prog [options] file [file...]

Sumarizes one or more log files reporting counts and size (bytes):
 - log messages
 - stack dumps by cpc classes'''

	parser = OptionParser(usage=usage)
	(options, args) = parser.parse_args()

	if args:
		stats = dict()
		processFiles(args, stats)
	else:
		print "FATAL: no files specified"
		parser.print_help()
		exit()

	if stats:
		reportStats(stats)

if __name__ == '__main__':
	main()

# EOF
