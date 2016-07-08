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
	"^[^>]+> <(Warning|Error)> (<oracle\.\S+)> .+?BEA-000000> <\s?(\S+(?: [^0-9 >{[]+){,4})",
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

	# Cross site filtering
	'^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S+ (ERROR|WARN ) (\[XSSFilter\] .+?)[,>]',

	# DEBUG Messages
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S+ \[\[\w+\].+?\] (DEBUG) +(\S+)",

	# RWS Logging
	'^\S+ <Notice> <(Stdout)> <\S+> <a[23]\w+-c2.+? {(svc=\w+, result=\w+, operation=\w+),',
	'^\S+ <Notice> <(Stdout)> <\S+> <a[23]\w+-c2.+? (xmlns:env="http://schemas.xmlsoap.org/soap/envelope/")',

	# CMSS Web Service
	'^\S+ <Notice> <(Stdout)> <\S+> <a3\w{3}d1-c1.+? <(Drawing white:\w+)',

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
	'^\S+ <(Error)> <(HTTP)> Unmatched:.+? <(Malformed Request ".+?")',
	'^\S+ <(Warning)> <(HTTP)> .+? (class loader configuration ignored)',
	'^\S+ <(Warning)> <(JNDI)> .+? (non-versioned global resource "\w+")',
	"^\S+ <(Error|Critical)> <(\S+)> .+<(\S+(?: -)?(?: [^-0-9@:;,>=' [\n]+){,4}).+?>",

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


# Match multiline first to get usable details.  Then match single line message
exceptionPatterns = [
	# SOA Patterns
	"^[^>]+> <(Warning|Error)> (<oracle\.\S+)> .+?BEA-000000> (?ms)<(JMSAdapter[^:](?: [^0-9 >{[]+){,4}).*?$\s(\w\S+[^0-9>\n\([]*)",
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?BEA-000000> (?ms).+?$\s(\w\S+[^0-9>\n[]*)",
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?(SOA-\d+)> (?ms).+?$\s(\w+[^0-9>\n[]*)",
	"^[^>]+> <(Warning|Error)> <(Connector|Diagnostics|EJB|JMX)> .+?(BEA-\d+)> (?ms).+?$\s(\w[^0-9>\n\([]*)",
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?BEA-000000> <\s?(\S+(?: [^0-9 >{[]+){,4})",
	"^[^>]+> <(Warning|Error)> <(oracle\.\S+)> .+?(OWS-\d+)> <\s?(\S+(?: [^0-9 >{[]+){,4})",
	"^[^>]+> <(Warning|Error)> <(Default)> .+?(JMX-\d+)> (?ms).+?$.*?^(\w.*?)$",
	"^[^>]+> <(Error)> <(WebLogicServer)> .+?(BEA-000337)> <\[(STUCK)",
	"^[^>]+> <Notice> <Diagnostics> .*?BEA-320068> <Watch 'StuckThread' with severity 'Notice'",

	#### Stdout
	# Date Application Level Thread Message (CPO)
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S{10} \S+ ([a-z]\S+) (ERROR|WARN|INFO) \[\[\w+\].+?\] (?ms)(\S+).+?at ((?:com\.(?:cpc|pur)|cpdt\.)\S+)",
	r"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S{10} \S+ ([a-z]\S+) (ERROR|WARN|INFO) \[\[\w+\].+?\] ([^> \n]+(?: -)?(?: [^-0-9@:;>=' [\n]+){,4})",

	# Date Level Thread Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ (ERROR|WARN|INFO) \[\[\w+\].+?\] (?ms)(\S+).+?at ((?:com\.(?:cpc|pur)|cpdt\.)\S+)",
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ (ERROR) \[\[\w+\].+?\] (\S+).+msg=PreparedStatementCallback; (.+)",
	r"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ (ERROR|WARN|INFO) \[\[\w+\].+?\] ([^> \n]+(?: -)?(?: [^-0-9@:;>=' [\n]+){,4})",

	# Date Level ?? Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ (ERROR|WARN|INFO) +\[\S+\] (?ms)(\S+).+?at ((?:com\.(?:cpc|pur|int)|cpdt\.)\S+)",
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ (ERROR|WARN|INFO) \[RuntimeRenderingManager\] (?ms)(.+?)$.+?uri :\[(\S+?)\]",
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ (ERROR) \[\S+\] (\S+).+?PreparedStatementCallback; (.+)",
	r"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ (ERROR|WARN|INFO) +\[\S+\] ([^> \n]+(?: -)?(?: [^-0-9@:;>=' [\n]+){,4})",

	# Date Thread Level Message
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ \[\[\w+\].+?\] (ERROR|WARN|INFO|DEBUG) (?ms)(\S+).+?at ((?:com\.(?:cpc|pur)|cpdt\.)\S+)",
	#r"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <(?:\S{10} )?\d\S+ \[\[\w+\].+?\] (ERROR|WARN|INFO) +([^> \n]+(?: -)?(?: [^-0-9@:;>=' [\n]+){,4})",

	# Date Application Level Message (CPO WebServices)
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\d{4}\S{6} \S+ ([a-z]\S+) (ERROR|WARN|INFO) (?ms)(\S+).+?at ((?:com\.(?:cpc|pur)|cpdt\.)\S+)",
	#r"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\d{4}\S{6} \S+ ([a-z]\S+) (ERROR|WARN|INFO) ([^> \n]+(?: -)?(?: [^-0-9@:;>=' [\n]+){,4})",

	# Remaining Stdout messages
	'^\S+ <Notice> <(Stdout)> <\S+> <a[23]\w+-c2.+? {(svc=\w+, result=\w+, operation=\w+),',
	'^\S+ <Notice> <(Stdout)> <\S+> <a1\w{3}d1-c4.+?<BEA-000000> <\[.+?\]\[(FATAL)\]\S+?\]\[(.+)',
	'^\S+ <Notice> <Stdout> <.+? c\.q\.l\.co(?:re)?\.rolling\.',
	'^\S+ <Notice> <(Stdout)> <\S+> <a3\w{3}d1-c1.+? <(Drawing white:\w+)',

	#'^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\S{10} \S+ ([a-z]\S+)

	#### StdErr
	# Thread Level Message
	r"^\S+ <Notice> <(StdErr)> .+?BEA-000000> <\[\[\w+\].+?\] (ERROR|WARN|INFO) +([^> \n]+(?: -)?(?: [^-0-9@:;>=' [\n]+){,4})",

	# Package loader
	r"^\S+ <Notice> <(StdErr)> .+?BEA-000000> <\[(PackageClassLoader)\S+\] +([^> \n]+(?: -)?(?: [^-0-9@:;>= [\n]+){3})",

	# Spring Loader
	r"^\S+ <Notice> <(StdErr)> .+?BEA-000000> <.+[AP]M (\w+\.\S+) (?ms).+?$\s^(INFO): ([^> \n]+(?: -)?(?: [^-0-9@:;,>=' [\n]+){,4})",

	# SAAJ SOAP Format
	"\S+ <Notice> <(StdErr)> .+?BEA-000000> <.+[AP]M (com\.sun\.\S+) (?ms).+?$.+?^(SEVERE):? (\S+(?: -)?(?: [^-0-9@:;>=' [\n]+){,4})",

	# LDAP Pool
	"^\S+ <Notice> <(StdErr)> .+?BEA-000000> <.+[AP]M (org\.springframework\.ldap\S+)(?ms) .+?$\s^(WARNING):.+?at ((?:com\.(?:cpc|pur)|cpdt\.)\S+)$",

	# Logback
	"^\S+ <Notice> <(Stdout)> .+?BEA-000000> <\d\S+ \|-(INFO) in (\w+\.[^> ]+(?: -)?(?: [^-0-9@:;>=' []+){,4})",

	# Hazelcast - Last as declare multiline match before we match hazelcast
	"^\S+ <Notice> <(StdErr)> .+?BEA-000000> <.+[AP]M (?ms)(com\.hazelcast\.\S+)$\s^(WARNING|INFO): (?:.+?]){3} (.+?):",
	#
	r"^\S+ <Notice> <(StdErr)> .+? <Caused by: ([^> \n]+(?: -)?(?: [^-0-9@:;,>=' [\n]+){,4})",
	r"^\S+ <Notice> <(StdErr)> .+? <(\w+\.[^> \n]+(?: -)?(?: [^-0-9@:;,>=' [\n]+){,4})",
	"^\S+ <Notice> <(StdErr)> .+? <(Some product derivations are being skipped)",

	#### WebLogic
	# Waring / Error / Critial messages
	'^\S+ <(Error)> <(HTTP)> .+?path:/(\S+) (?ms).+?(^\S+?)\s.+?at .+?at (com\.(?:cp|pur)\S+)',
	'^\S+ <(Error)> <(HTTP)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	'^\S+ <(Error)> <(Kernel)> (?ms).+?(^\S+).+at (weblogic\.\S+)',
	'^\S+ <(Error)> <(WebLogicServer)> .+? <\[(STUCK)\] (?ms).+?(com\.(?:cp|pur)\S+)',
	r'^\S+ <(Error)> <(WebLogicServer)> .+? <\[(STUCK)\] (?ms).+?(^\w.+?)[-:.\n\(\?]',
	'^\S+ <(Error)> <(ServletContext-/.+?)> (?ms).+?(^\S+).+?at (weblogic\.\S+)',
	'^\S+ <(Error)> <(ServletContext-/cpotools)> .+?path:/(\S+) (?ms).+?(^\S+).+?at (com\.(?:cp|pur)\S+)',
	'^\S+ <(Warning)> <(JDBC)> .+? <(Forcibly releasing) inactive/harvested (connection) ".+?" .+? (".+?")',
	r"^\S+ <(Error|Critical)> <(\S+)> .+<(\S+(?: -)?(?: [^-0-9@:;,>=' [\n]+){,4})",

	# Startup notices
	'^\S+ <Notice> <Security> .+? Loading trusted certificates',
	'^\S+ <Notice> <Security> .+? Using default',
	'^\S+ <Notice> <StdErr> .+? INFO: Registering Spring bean,',

	# Info messages - Ignored
	'^\S+ <Info>',
	#'^\S+ <Info> <(JDBC)> .+? pool ".+?" connected',
	#'^\S+ <Info> <Management> .+? Java system properties',
	#'^\S+ <Info> <Management> .+? Server state changed',
	#'^\S+ <Info> <RJVM> .+? Network Configuration',
	#'^\S+ <Info> <WebLogicServer> .+? WebLogic Server ".+?" version:',
	#'^\S+ <Info> <WorkManager> .+? Initializing self-tuning thread pool',
	'^[^>]+> <(?:Info|Notice)> <(?:Management|WebLogicServer)>',

	# Stray XML
	'^\s*(<.+?>)',
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