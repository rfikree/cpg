#components.py - get components for a weblogic domain

from os import listdir

def _getWLdetails(category, entry):
	if '#' in entry:
		(name, version) = entry.split('#')
	else:
		(name, version) = (entry, 'none')
	targets = _getNames('/'.join((category, entry, 'Targets')))
	states = _getStates(entry, targets)
	for i in range (1, len(targets)):
		targets[i] = '-'.split(targets[i])[-1]
	targets = ','.join(targets)
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


def getArtifacts(adminurl, user='Deployment Monitor', passwd='yIHj6oSGoRpl66muev5S'):
	global appStateRuntime

	try:
		connect(user, passwd, adminurl, timeout=10000)
	except Exception, e:
		print 'Connection to', adminurl, 'failed'
		print e
		return None

	appStateRuntime = getMBean('domainRuntime:AppRuntimeStateRuntime').getAppRuntimeStateRuntime()
	serverConfig()

	artifactList=[]

	deployments = _getNames('AppDeployments')
	deployments.sort()
	#print 'deployments', deployments
	for item in deployments:
		artifactList.append(_getWLdetails('AppDeployments', item))

	libraries = _getNames('Libraries')
	libraries.sort()
	#print 'libraries', libraries
	for item in libraries:
		artifactList.append(_getWLdetails('Libraries', item))

	artifactList.extend(_getLibJars())

	disconnect()
	return artifactList


def _testGetArtifacts():
	if len(sys.argv) not in [2, 4]:
		print
		print 'usage: wlst.sh', sys.argv[0], 'adminurl'
		print 'usage: wlst.sh', sys.argv[0], 'adminurl user password'
		print
		exit('', 1)

	adminurl = sys.argv[1]

	if len(sys.argv) == 2:
		#print adminurl
		artifacts = getArtifacts(adminurl)
	else:
		user = sys.argv[2]
		passwd = sys.argv[3]
		#print adminurl, user, passwd
		artifacts = getArtifacts(adminurl, user, passwd)

	if artifacts:
		for artifact in artifacts:
			print artifact

if __name__ == "main":
	_testGetArtifacts()

# EOF
