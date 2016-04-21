#! /usr/bin/env wlst.sh

import getopt
import os
import sys
import ConfigParser
sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])))

from components import getArtifacts
from generateReport import genReport

def usage(status):
	print '''

	Usage: ./buildReports.py [-h] [-e environment] [-u user] [-p passsword]

	Options
		-h, --help: Print this help message
		-e, --environment: Specify environment to run for
		-u, --user: Specify user to connect with
		-p, --password: Specify the password to connect with
	'''
	sys.exit(status)

def getStacks(config, environment, stackList):
	''' Generate a list of stacks add related URLs from a list
	'''
	if not stackList:
		print 'FATAL: Environment', environment, 'has no stacks.'
		sys.exit(2)

	stacks = []
	stackList.sort()
	for stackName in stackList:
		urls = config.get(environment, stackName).split('\n')
		stacks.append(( stackName, urls ))

	#print 'stacks:', stacks
	return stacks

def getComponents(urls, user, passwd):
	''' Get the components for a stack - one or more URLs
	'''
	components = []

	for url in urls:
		artifacts = getArtifacts(url, user, passwd)
		if artifacts:
			components.append((url, artifacts))

	#print components
	return components

def saveReport(reportName, report):
	''' Save the report to a file
	'''
	filename = ''.join((reportName, '.html'))
	f = open(filename, 'w')
	f.write(report)
	f.close


def createReports(propertyFile, environment, user, passwd):
	'''create the reports for the selected environment
	'''
	allComponents = []
	config = ConfigParser.ConfigParser()
	config.read(propertyFile)
	if not config.has_section(environment):
		print 'FATAL: Invalid environment', environment, 'selected.'
		sys.exit(2)

	stackList = config.options(environment)
	#print 'stackList:', stackList
	stacks = getStacks(config, environment, stackList)
	#print 'stacks:', stacks

	for (stackName, urls) in stacks:
		#print 'stackName:', stackName, ' - urls:', urls
		stackComponents = getComponents(urls, user, passwd)
		if stackComponents:
			#print 'stackComponents:', stackComponents
			report = genReport(stackName, stackComponents)
			#print report
			saveReport(stackName, report)
			allComponents.extend(stackComponents)

	if allComponents:
		title = config.get('titles', environment)
		report = genReport(title, allComponents)
		saveReport(environment, report)
		#print report


def main():
	''' Read options and generate reportss
	'''

	user='Deployment Monitor'
	passwd='yIHj6oSGoRpl66muev5S'

	#print 'sys.argv:', sys.argv
	propertyFile = sys.argv[0][:-2] + 'properties'

	try:
		options, args = getopt.getopt(sys.argv[1:],
					'he:u:p:', ['help', 'enviroment=', 'user=', 'password='])
	except getopt.GetoptError:
		# print help information and exit:
		usage(2)

	if not options:
		usage(2)

	# Process setup options
	for o, a in options:
		if o in ('-h', '--help'):
			usage(0)
		elif o in ('-u', '--user'):
			user = a
		elif o in ('-p', '--password'):
			passwd = a

	# Run the report
	for o, a in options:
		if o in ('-e', '--enviroment' and a != 'titles'):
			#print 'propertyFile, a', propertyFile, a
			stacks = createReports(propertyFile, a, user, passwd)
		elif o in ('-e', '--enviroment'):
			usage(2)


if __name__ == 'main':
	try:
		main()
	except KeyboardInterrupt, e:
		print ()
		print ('Processing cancelled')
		print ()
	except Exception, e:
		print ()
		print ('FATAL Unhandled Exception')
		print (e)

# EOF
