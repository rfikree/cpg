#!/usr/bin/env python

""" LogMessageStats summarizes log file reporting message counts and
the logfile space utilized by the log file. """

from optparse import OptionParser
import fileinput
import sys
import re


linePatterns = [
	# WebLogic Notices - Ignored
	'^\S+ <Notice> <Std\w\w\w> .+? <LoggingService>',

	# Stdout messages - filterd by domain
	'^\S+ <Notice> <Stdout> <\S+> <a2\w2\dd1-c1.+? INFO',
	'^\S+ <Notice> <(Stdout)> <\S+> <a[23].+? (ERROR|WARN|INFO) \[(?:\[\w+\])?.+?\] (.+?)[-0-9:=>]',
	#'^\S+ <Notice> <(Stdout)> <\S+> <a[23]\w\d\dd1-c1.+? (ERROR) \[\S+\] (.+?)[):=>]',
	'^\S+ <Notice> <(Stdout)> <\S+> <a[23]\w\d\dd1-c2.+? {(svc=\w+, result=\w+, operation=\w+),',
	'^\S+ <Notice> <(Stdout)> <\S+> <a[23]\w\d\dd1-c2.+? (xmlns:env="http://schemas.xmlsoap.org/soap/envelope/")',
	#'^\S+ <Notice> <(Stdout)> <\S> <a3\w3\dd1-c1.+?  (INFO)(from logger \w+),',
	#'^\S+ <Notice> <(Stdout)> <\S+> <a3.+? (INFO) \[(?:\[\w+\])?.+?\] (\S+ \w+) \w+[-:=>]',
	'^\S+ <Notice> <(Stdout)> <\S+> <a3\w3\dd1-c1.+? <(Drawing white:\w+)>',


	# Stdout messages
	'^\S+ <Notice> <Stdout> .+? Fetching customer profile for CPCID',
	'^\S+ <Notice> <Stdout> .+ WARN +\[(?:SearchLookup|InvalidationMonitor)\]',
	'^\S+ <Notice> <(Stdout)> (ERROR) \S+ (\S+) .+?(File not found:.+?)>',
	'^\S+ <Notice> <(Stdout)> ([^<0-9]\S+) (ERROR) .+ (MissingProperty.+)>',
	'^\S+ <Notice> <(Stdout)> .+ ([^<0-9]\S+) (ERROR|WARN):? (?:\[\[\w+\].+\] )?(\S.+?)(?: ?[-:\n(\?])',
	'^\S+ <Notice> <(Stdout)> .+ (WARN) +\[XSSFilter\] (.+?)>',
	'^\S+ <Notice> <(Stdout)> .+ (c.c.n.u.t.c.TermsOfUseController \w+ \w+)',
	'^\S+ <Notice> <(Stdout)> .+ <\S+ (ERROR|WARN) +\[\S+?\] (.+?)(?: ?[-:>]|code|name)',
	'^\S+ <Notice> <Stdout> .+? <log4j: setFile',

	# StdErr ouput
	'^\S+ <Notice> <(StdErr)> .+? (\[IntroscopeAgent.Agent\] Exception \w+ing method tracer)',
	'^\S+ <Notice> <(StdErr)> .+? (\[IntroscopeAgent.Agent\] Temporarily throttling the errors)',
	'^\S+ <Notice> <(StdErr)> .+? <(line \d+:\d+ no viable .+?)>',

	# Unhandled exceptions
	'^\S+ <Notice> <(StdErr)> <.+? <(BEA-000000)> <(at) ',
	'^\S+ <Notice> <(StdErr)> <.+? <(BEA-000000)> <(\S+)>',
	'^\S+ <Notice> <(Std\w\w\w)> <.+? <((?!at )[^>]+)>\s*$',

	# WebLogic Error Message
	'^\S+ <(Error)> <(CpgIdentityJAASAsserterLogger)> .+ <BEA-000000> <(Failed to lookup customer profile)',
	'^\S+ <(Error)> <(CpgIdentityJAASAsserterLogger)> .+ <BEA-000000> <(.+?: \w+)',
	'^\S+ <(Error)> <(HTTP)> .+? <(Malformed Request ".+?")',

	# WebLogic Info messages
	'^\S+ <(Info)> <(Common)> .+? <(Reached maximum capacity of pool "\w+")',
	#'^\S+ <(Info)> <(Cluster)> .+? <(Lost \d+ unicast message\(s\))',
	#'^\S+ <(Info)> <(Common)> .+? <(Created "\d+" resources for pool "\w+")',
	#'^\S+ <(Info)> <(JDBC)> .+? (pool ".+?") has been (closed)',
	#'^\S+ <(Info)> <(WorkManager)> .+? M(maximum thread constraint ClusterMessaging is reached)',
	'^\S+ <Info>',

	# WebLogic Warnings
	'^\S+ <(Warning)> <(Socket)> .+? <(Closing socket as no data read)',
	'^\S+ <(Warning)> <(CpgIdentityJAASAsserterLogger)> .+ <BEA-000000> <(.+?: \w+)',

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
	r'^\S+ <Notice> <(StdErr)> (?ms).+?com\.sun\.xml\..+?$\s(SEVERE): \w+: (.+?)$',
	r"^\S+ <Notice> <(StdErr)> (?ms).+?^(INFO|WARNING): .+? '(\w.+?)['@]",
	r"^\S+ <Notice> <(StdErr)> (?ms).+?(^WARNING): .+? serviceName='(.+?)'",

	# Captured StdOut Messages
	r'^\S+ <Notice> <Stdout> <.+? c.q.l.core.rolling.',
	r'^\S+ <Notice> <(Stdout)> <.+? {(svc=\w+, result=OK, operation=\w+),',
	r'^\S+ <Notice> <(Stdout)> <.+? (INFO) \[\[\w+\].+?\] (\S+ (?:In|Out).+)',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR) .* (bad SQL grammar.+?\])',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR|WARN|INFO) +\[\[\w+\].+?\] (\S+)',

	# ui-cpo ERROR ...
	r'^\S+ <Notice> <Stdout> <.+ ([^<0-9]\S+) (ERROR|WARN) (?ms).+?(^\S+):.+?at (com\.(?:cpc|pur)\S+)',
	r'^\S+ <Notice> <Stdout> <.+ ([^<0-9]\S+) (ERROR) \[\[\w+\].+?\] (\S+)',
	r'^\S+ <Notice> <Stdout> <.+ ([^<0-9]\S+) (ERROR) (?ms).+?(^\S.+?)[-\n(\?]',

	# Multiline matches ...
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR) (?ms).*?(^\w\S+).+?at (com\.(?:cpc|pur)\S+)',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR) \S+ \S+ (site not (?ms)valid:).+?^uri :\[(\S+?)\]',

	# Last ditch notice handlers
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR) (?ms).+?^ExceptionMessage{.+?(^\w\S.+?)[-:\n(\?]',
	r'^\S+ <Notice> <(Stdout)> <.+? (ERROR|WARN|INFO) (?ms).+?(^\w\S.+?)[-:\n(\?]',

	# Error messages reported by WebLogic
	r'^\S+ <(Error)> <(HTTP)> .+?path:/(\S+) (?ms).+?(^\S+?)\s.+?at .+?at (com\.(?:cp|pur)\S+)',
	r'^\S+ <(Error)> <(HTTP)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <(Kernel)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <(Kernel)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <(WebLogicServer)> .+? <\[(STUCK)\] (?ms).+?(^\w.+?)[-:\n(\?]',
	r'^\S+ <(Error)> <ServletContext-/(.+?)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	r'^\S+ <(Error)> <ServletContext-/(cpotools)> .+?path:/(\S+) (?ms).+?(^\S+).+?at (com\.(?:cp|pur)\.\S+)',
	r'^\S+ <(Warning)> <(JDBC)> .+? <(Forcibly releasing) inactive/harvested (connection) ".+?" .+? (".+?")',

	# Startup notices
	r'^\S+ <Notice> <Security> .+? Loading trusted certificates',
	r'^\S+ <Notice> <Security> .+? Using default',
	r'^\S+ <Notice> <StdErr> .+? INFO: Registering Spring bean,',

	# Info messages - Ignored
	r'^\S+ <Info>',
	#r'^\S+ <Info> <(JDBC)> .+? pool ".+?" connected',
	#r'^\S+ <Info> <Management> .+? Java system properties',
	#r'^\S+ <Info> <Management> .+? Server state changed',
	#r'^\S+ <Info> <RJVM> .+? Network Configuration',
	#r'^\S+ <Info> <WebLogicServer> .+? WebLogic Server ".+?" version:',
	#r'^\S+ <Info> <WorkManager> .+? Initializing self-tuning thread pool',

	# Stray XML
	r'^\s*(<.+?>)',
]

lineRegexes = []
for pattern in linePatterns:
	#print pattern
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
		if not match.groups():
			return

		key = ' '.join(match.groups())
		count, size = stats.get(key, (0, 0))
		stats[key] = (count + 1, size + len(line))

		#if 'Stdout WARN XSSFilter' in key:
		#	print 'WAT key', key
		#	print 'WAT pattern', regex.pattern
		#	print line

	else:
		print >> sys.stderr, ':'.join((fileName, str(messageLineNo))), \
			'processLine:', line


def processException(lines, stats):
	''' parse an exception gathering stats
	'''
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

		#if key.startswith('Error') and 'HTsTP' in key:
		#	print 'WAT key', key
		#	print 'WAT pattern', regex.pattern
		#	print allLines
		#print 'WAT key', key
		#print 'WAT pattern', regex.pattern

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


	if stats:
		reportStats(stats)

if __name__ == '__main__':
	main()

# EOF
