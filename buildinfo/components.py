#components.py get componets for a weblogic domain

from os import listdir

def _getEntry(category, entry):
	(name, version) = entry.split('#')
	targets = _getNames('/'.join((category, entry, 'Targets')))
	states = _getStates(entry, targets)
	targets = ' '.join(targets)
	#print '\t'.join((name, version, states, targets))
	return (name, version, states, targets)

def _getNames(target):
	values = []
	for item in get(target):
		values.append(str(item).split('Name=')[1].split(',')[0])
	values.sort()
	return values

def _getStates(entry, targets):
	states = []
	for target in targets:
		state=appStateRuntime.getCurrentState(entry, target).split('_')[1]
		if state not in states:
			states.append(state)
	states.sort()
	return ','.join(states)


def _getLibJars():
	libJars = []
	domainDir = get('RootDirectory')
	#print 'domainDir', domainDir
	for subdir in ('lib', 'lib/mbeantypes'):
		directory = '/'.join((domainDir, subdir))
		#print 'directory', directory
		try:
			for filename in listdir(directory):
				if filename.endswith('.jar'):
					components = filename[:-4].split('-')
					name = '-'.join(components[:-1])
					version = components[-1]
					libJars.append((name, version, 'LIBRARY', subdir))
					#print name, version, 'LIBRARY', subdir
		except OSError:
			pass
	libJars.sort()
	return libJars


def getArtifacts(user, passwd, adminurl):
	global appStateRuntime

	connect(user, passwd, adminurl)
	appStateRuntime = getMBean('domainRuntime:AppRuntimeStateRuntime').getAppRuntimeStateRuntime()
	serverConfig()

	artifactList=[]

	deployments = _getNames('AppDeployments')
	deployments.sort()
	#print 'deployments', deployments
	for item in deployments:
		artifactList.append(_getEntry('AppDeployments', item))

	libraries = _getNames('Libraries')
	libraries.sort()
	#print 'libraries', libraries
	for item in libraries:
		artifactList.append(_getEntry('Libraries', item))

	artifactList.extend(_getLibJars())

	disconnect()
	return artifactList


def _testGetArtifacts():
	if len(sys.argv) < 4:
		print
		print 'usage', sys.argv[0], 'user password adminurl'
		print
		exit('', 1)

	user = sys.argv[1]
	passwd = sys.argv[2]
	adminurl = sys.argv[3]
	print user, passwd, adminurl

	artifacts = getArtifacts(user, passwd, adminurl)
	print artifacts

if __name__ == "main":
	_testGetArtifacts()

# EOF
