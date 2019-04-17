#! /bin/env wlst.sh
#components.py - get components for a weblogic domain

from os import listdir
from wlstModule import *

def _getEnvConfig():
    domainDir = get('RootDirectory')
    path = '/'.join(domainDir, 'classpath-ext/resources')
    configs = []
    try:
        for filename in listdir(directory):
            if filename.endswith('.id'):
                parts = filename.split('-')
                config = ('-').join(parts[:-1])
                version = parts[-1][:-3]
                configs.append((config, version, 'Config', 'environment'))
    except OSError:
        pass
    return configs


def _getWLdetails(category, entry):
    if '#' in entry:
        (name, version) = entry.split('#')
        version = version.split('@')[0]
    else:
        (name, version) = (entry, 'none')
    targets = _getNames('/'.join((category, entry, 'Targets')))
    states = _getStates(entry, targets)
    for i in range (1, len(targets)):
        targets[i] = targets[i].split('-')[-1]
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
        #print 'xxxx', entry, target
        state=appStateRuntime.getCurrentState(entry, target)
        if state:
            state=state.split('_')[-1]
        else:
            print '%s has no state for %s' % (entry, target)
            state='Unknown'
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
                    libJars.append((name, version, 'JarFile', subdir))
                    #print name, version, 'JarFile', subdir
        except OSError:
            pass
    libJars.sort()
    return libJars


def getArtifacts(adminurl, user='Deployment Monitor', passwd='yIHj6oSGoRpl66muev5S'):
    global appStateRuntime

    artifactList=[]
    libraryList=[]
    result = (artifactList, libraryList)

    try:
        connect(user, passwd, adminurl, timeout=200000)
    except Exception, e:
        print 'Connection to', adminurl, 'failed'
        print e
        return result

    try:
        appStateRuntime = getMBean('domainRuntime:AppRuntimeStateRuntime').getAppRuntimeStateRuntime()
        serverConfig()

        deployments = _getNames('AppDeployments')
        deployments.sort()
        #print 'deployments', deployments
        for item in deployments:
            artifactList.append(_getWLdetails('AppDeployments', item))

    except Exception, e:
        print 'Getting artifacts from', adminurl, 'failed'
        print e
        pass

    artifactList.extend(_getEnvConfig())

    try:
        artifactList.extend(_getLibJars())

    except Exception, e:
        print 'Getting jars from', adminurl, 'failed'
        print e
        pass

    try:
        libraries = _getNames('Libraries')
        libraries.sort()
        #print 'libraries', libraries
        for item in libraries:
            libraryList.append(_getWLdetails('Libraries', item))

    except Exception, e:
        print 'Getting libraries from', adminurl, 'failed'
        print e
        pass

    disconnect()
    #print result
    return result


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
        applications, libraries = artifacts
        for artifact in applications:
            print 'Application:', artifact
        for artifact in libraries:
            print 'Library:', artifact

if __name__ == "main":
    _testGetArtifacts()


# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
