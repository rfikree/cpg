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


linePatterns = [
	# WebLog logging messages
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> .+<LoggingService>",

	# Stdout messages - By format
	# Date Applicagtion Level Thread Message (CPO)
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S{10} \S+ ([a-z]\S+) (ERROR|WARN|INFO) \[\[\w+\].+?\] ([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",
	# Date  Level Thread Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\S+ (ERROR|WARN|INFO) \[\[\w+\].+?\] ([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",
	# Date  Level ?? Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\S+ (ERROR|WARN|INFO) +\[\S+\] ([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",
	# Date Thread Level Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\S+ \[\[\w+\].+?\] (ERROR|WARN|INFO) +([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",

	# Date Applicagtion Level Message (CPO WebServices)
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\d{4}\S{6} \S+ ([a-z]\S+) (ERROR|WARN|INFO) ([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",

	# Cross site filtering
	'^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S+ (ERROR|WARN ) (\[XSSFilter\] .+?)[,>]',

	# DEBUG Messages
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S+ \[\[\w+\].+?\] (DEBUG) +(\S+)",

	# RWS Logging
	'^\S+ <Notice> <(Stdout)> <\S+> <a[23]\w+-c2.+? {(svc=\w+, result=\w+, operation=\w+),',
	'^\S+ <Notice> <(Stdout)> <\S+> <a[23]\w+-c2.+? (xmlns:env="http://schemas.xmlsoap.org/soap/envelope/")',

	# CMSSS Web Service
	'^\S+ <Notice> <(Stdout)> <\S+> <a3\w3\dd1-c1.+? <(Drawing white:\w+)>',

	# StdErr ouput
	# Thread Level Message
	"^\S+ <Notice> <(StdErr)> .+?BEA-000000> <\[\[\w+\].+?\] (ERROR|WARN|INFO) +([^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",
	# Other messags
	'^\S+ <Notice> <(StdErr)> .+? (\[IntroscopeAgent.\w+\] \w+ \w+ \w+ \w+)',
	'^\S+ <Notice> <(StdErr)> .+? <Exception in thread "Thread-\d+" (.+?)>',
	'^\S+ <Notice> <(StdErr)> .+? <(line \d+:\d+ no viable .+?)>',

	# Unhandled exceptions = ignored
	'^\S+ <Notice> <Std\w+> .+? <log4j: ',

	# WebLogic Error Message
	'^\S+ <(Alert)> <(WebLogicServer)> .+> <(\S+)>',
	'^\S+ <(Error)> <(CpgIdentityJAASAsserterLogger)> .+ <BEA-000000> <(Failed to lookup customer profile)',
	'^\S+ <(Error)> <(CpgIdentityJAASAsserterLogger)> .+ <BEA-000000> <(.+?: \w+)',
	'^\S+ <(Error)> <(HTTP)> .+? <(Malformed Request ".+?")',
	'^\S+ <(Warning)> <(HTTP)> .+? (class loader configuration ignored)',
	'^\S+ <(Warning)> <(JNDI)> .+? (non-versioned global resource "\w+")',

	# WebLogic Info messages - normally ignored
	#'^\S+ <(Info)> <(Common)> .+? <(Created "\d+" resources for pool "\w+")',
	#'^\S+ <(Info)> <(JDBC)> .+? (pool ".+?") has been (closed)',

	# WebLogic Info messages
	'^\S+ <(Info)> <(Common)> .+? <(Reached maximum capacity of pool "\w+")',
	'^\S+ <(Info)> <(Cluster)> .+? <(Lost \d+ unicast message\(s\))',
	'^\S+ <(Info)> <(WorkManager)> .+? M(maximum thread constraint ClusterMessaging is reached)',
	'^[^>]+> <Info> ',
	'^[^>]+> <Notice> <(?:Cluster|Log Management|Security|Server|WebLogicServer)>',

	# WebLogic Warnings                               |
	'^\S+ <(Warning)> <(Socket)> .+? <(Closing socket as no data read)',
	'^\S+ <(Warning)> <(CpgIdentityJAASAsserterLogger)> .+ <BEA-000000> <(.+?: \w+)',
	'^[^>]+> <(Warning)> <(Management)> .+> <(.+)>',

	# Unmatched patterns: - Matching messages will be written to StdErr file.
	#'^\S+ <Notice> <(StdErr)> <.+? <(BEA-000000)> <(at )',
	#'^[^>]+> <Notice> <(Std\w+)> <.+ <[^<]+)>',
]


# Patterns with no match groups will be ignored; use (?:...) for non-capture
# Patterns with optional match groups will crash the program.
exceptionPatterns = [
	# Captured StdErr Messages
	r'^\S+ <Notice> <(StdErr)> <.+? (com\.hazelcast\..*)',
	r'^\S+ <Notice> <(StdErr)> <.+? (INFO) (\S+ - (?:In|Out)\S+ \S+)',
	r'^\S+ <Notice> <(StdErr)> <.+? (FATAL): .+?  Exception is: (.+?)$',
	r'^\S+ <Notice> <(StdErr)> <.+ ([^<0-9]\S+) +(INFO) +\[\[\w+\].+?\] (\S+)',
	r'^\S+ <Notice> <(StdErr)> <.+? (SEVERE): .\w+ (.+?)>$',
	r'^\S+ <Notice> <(StdErr)> (?ms).+?com\.sun\.xml\..+?$\s(SEVERE): \w+: (.+?)>',
	r"^\S+ <Notice> <(StdErr)> (?ms).+?^(INFO|WARNING): .+? '(\w.+?)['@]",
	r"^\S+ <Notice> <(StdErr)> (?ms).+?(^WARNING): .+? serviceName='(.+?)'",
	r'^\S+ <Notice> <(StdErr)> (?ms)<.+?$\s?(INFO)',
	r'^\S+ <Notice> <(StdErr)> (?ms)<.+?$\s(SEVERE|ERROR|WARN).+?(^\S+):.+?at ((?:com\.cpc|cpdt)\.\S+)',
	r'^\S+ <Notice> <(StdErr)> (?ms)<.+?$\s(SEVERE|ERROR|WARN):\s*?$.+?^(\S+.+?)$',
	r'^\S+ <Notice> <(StdErr)> <.+ (\w+ of missing type cpdt\.\w+\.rules\.)',

	# ui-cpo ERROR ...
	r'^\S+ <Notice> <Stdout> <.+ ([^<0-9]\S+) (ERROR|WARN) (?ms).+?(^\S+):.+?at (com\.(?:cpc|pur)\S+)',
	r'^\S+ <Notice> <Stdout> <.+ ([^<0-9]\S+) (ERROR) \[\[\w+\].+?\] (\S+)',
	r'^\S+ <Notice> <Stdout> <.+ ([^<0-9]\S+) (ERROR) (?ms).+?(^\S.+?)[-\n(\?]',

	# Captured StdOut Messages
	r'^\S+ <Notice> <(Stdout)> <.+? {(svc=\w+, result=OK, operation=\w+),',
	r'^\S+ <Notice> <(Stdout)> <.+? (INFO) \[\[\w+\].+?\] (\S+ (?:In|Out).+)',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR) .* (bad SQL grammar.+?\])',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR|WARN|INFO) +\[\[\w+\].+?\] (\S+)',
	r'^\S+ <Notice> <Stdout> <.+? c\.q\.l\.co(?:re)?\.rolling\.',
	r'^\S+ <Notice> <(Stdout)> .+?(FATAL).+?(\w+).+ (\S+: [^:]+)',
	r'^\S+ <Notice> <(Stdout)> <\S+> <a3\w3\dd1-c1.+? <(Drawing white:\w+)',


	# Multiline matches ...
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR) (?ms).*?(^\w\S+).+?at ((?:com\.(?:cpc|pur)|cpdt\.)\S+)',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR) \S+ \S+ (site not (?ms)valid:).+?^uri :\[(\S+?)\]',
	r'^\S+ <Notice> <(Std...)> <.+? (?ms).+(PreparedStatementCallback); SQL \[(.+?)\]; (.+?)>?$',

	# Last ditch notice handlers
	r'^\S+ <Notice> <(Stdout)> <.+? \[\[\w+\].+?\] (ERROR|INFO |DEBUG) (\S+)',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR) (?ms).+?^ExceptionMessage{.+?(^\w\S.+?)[-:\n(\?]',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR|WARN|INFO) (?ms).+?(^\w\S.+?)[-:\n(\?]',
	r'^\S+ <Notice> <(StdErr)> <.+? <(Nested (?ms)exception:).+?^(\w[^:]+)',

	# Error messages reported by WebLogic
	r'^\S+ <(Error)> <(HTTP)> .+?path:/(\S+) (?ms).+?(^\S+?)\s.+?at .+?at (com\.(?:cp|pur)\S+)',
	r'^\S+ <(Error)> <(HTTP)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <(Kernel)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <(Kernel)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <(WebLogicServer)> .+? <\[(STUCK)\] (?ms).+?(^\w.+?)[-:\n(\?]',
	r'^\S+ <(Error)> <(WebLogicServer)> .+? <\[(STUCK)\] (?ms).+?(com\.(?:cp|pur)\S+)',
	r'^\S+ <(Error)> <ServletContext-/(.+?)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <ServletContext-/(cpotools)> .+?path:/(\S+) (?ms).+?(^\S+).+?at (com\.(?:cp|pur)\S+)',
	r'^\S+ <(Warning)> <(JDBC)> .+? <(Forcibly releasing) inactive/harvested (connection) ".+?" .+? (".+?")',

	# Startup notices
	r'^\S+ <Notice> <Security> .+? Loading trusted certificates',
	r'^\S+ <Notice> <Security> .+? Using default',
	r'^\S+ <Notice> <StdErr> .+? INFO: Registering Spring bean,',

	# Error / Critical
	r'^\S+ <(Error|Critical)> <(\S+)>',

	# Info messages - Ignored
	r'^\S+ <Info>',
	#r'^\S+ <Info> <(JDBC)> .+? pool ".+?" connected',
	#r'^\S+ <Info> <Management> .+? Java system properties',
	#r'^\S+ <Info> <Management> .+? Server state changed',
	#r'^\S+ <Info> <RJVM> .+? Network Configuration',
	#r'^\S+ <Info> <WebLogicServer> .+? WebLogic Server ".+?" version:',
	#r'^\S+ <Info> <WorkManager> .+? Initializing self-tuning thread pool',
	r'^[^>]+> <(?:Info|Notice)> <(?:Management|WebLogicServer)>',

	# Stray XML
	r'^\s*(<.+?>)',
]



lineRegexes = []
for pattern in linePatterns:
	try:
		lineRegexes.append(re.compile(pattern))
	except Exception:
		print 'invalid:', pattern

exceptionRegexes = []
for pattern in exceptionPatterns:
	try:
		exceptionRegexes.append(re.compile(pattern))
	except Exception:
		print 'invalid:', pattern


def processLine(line, stats):
	''' parse a line gathering stats
	'''
	return
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

		#if 'StdErr SEVERE SOAP' in key:
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
