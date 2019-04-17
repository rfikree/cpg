#! /bin/env wlst.sh
'''components.py - get components for a weblogic domain

Return a list of compments in a WebLogic domain as tuples in the form
  (component, version, state, target(s))
'''

# pylint:disable=duplicate-code,broad-except,global-statement,import-error

import sys
from os import listdir
from wlstModule import connect, disconnect, getMBean, serverConfig, get

__app_state_runtime__ = None

def _get_env_config():
    domain_dir = get('RootDirectory')
    directory = '/'.join((domain_dir, 'classpath-ext/resources'))
    configs = []
    try:
        for filename in listdir(directory):
            if filename.endswith('.id'):
                parts = filename.split('-')
                config = ('-').join(parts[:-1])
                version = parts[-1][:-3]
                configs.append((config, version, 'Config', 'classpath'))
    except OSError:
        pass
    return configs


def _get_wl_details(category, entry):
    if '#' in entry:
        (name, version) = entry.split('#')
        version = version.split('@')[0]
    else:
        (name, version) = (entry, 'none')
    targets = _get_names('/'.join((category, entry, 'Targets')))
    states = _get_states(entry, targets)
    for i in range(1, len(targets)):
        targets[i] = targets[i].split('-')[-1]
    targets = ','.join(targets)
    #print '\t'.join((name, version, states, targets))
    return (name, version, states, targets)

def _get_names(target):
    values = []
    for item in get(target):
        values.append(str(item).split('Name=')[1].split(',')[0])
    values.sort()
    return values

def _get_states(entry, targets):
    states = []
    for target in targets:
        #print 'xxxx', entry, target
        state = __app_state_runtime__.getCurrentState(entry, target)
        if state:
            state = state.split('_')[-1]
        else:
            print '%s has no state for %s' % (entry, target)
            state = 'Unknown'
        if state not in states:
            states.append(state)
    states.sort()
    return ','.join(states)


def _get_lib_jars():
    lib_jars = []
    domain_dir = get('RootDirectory')
    #print 'domain_dir', domain_dir
    for subdir in ('lib', 'lib/mbeantypes'):
        directory = '/'.join((domain_dir, subdir))
        #print 'directory', directory
        try:
            for filename in listdir(directory):
                if filename.endswith('.jar'):
                    components = filename[:-4].split('-')
                    name = '-'.join(components[:-1])
                    version = components[-1]
                    lib_jars.append((name, version, 'JarFile', subdir))
                    #print name, version, 'JarFile', subdir
        except OSError:
            pass
    lib_jars.sort()
    return lib_jars


def get_artifacts(adminurl, user='Deployment Monitor', passwd='yIHj6oSGoRpl66muev5S'):
    '''Get the list of artifacs for a WebLogic Domain'''
    global __app_state_runtime__

    artifact_list = []
    library_list = []
    result = (artifact_list, library_list)

    try:
        connect(user, passwd, adminurl, timeout=200000)
    except Exception, _e:
        print 'Connection to', adminurl, 'failed'
        print _e
        return result

    try:
        __app_state_runtime__ = getMBean('domainRuntime:AppRuntimeStateRuntime')\
                                      .getAppRuntimeStateRuntime()
        serverConfig()

        deployments = _get_names('AppDeployments')
        deployments.sort()
        #print 'deployments', deployments
        for item in deployments:
            artifact_list.append(_get_wl_details('AppDeployments', item))

    except Exception, _e:
        print 'Getting artifacts from', adminurl, 'failed'
        print _e

    artifact_list.extend(_get_env_config())

    try:
        artifact_list.extend(_get_lib_jars())

    except Exception, _e:
        print 'Getting jars from', adminurl, 'failed'
        print _e


    try:
        libraries = _get_names('Libraries')
        libraries.sort()
        #print 'libraries', libraries
        for item in libraries:
            library_list.append(_get_wl_details('Libraries', item))

    except Exception, _e:
        print 'Getting libraries from', adminurl, 'failed'
        print _e

    disconnect()
    #print result
    return result


def _test_get_artifacts():

    if len(sys.argv) not in [2, 4]:
        print
        print 'usage: wlst.sh', sys.argv[0], 'adminurl'
        print 'usage: wlst.sh', sys.argv[0], 'adminurl user password'
        print
        exit('', 1)

    adminurl = sys.argv[1]

    if len(sys.argv) == 2:
        #print adminurl
        artifacts = get_artifacts(adminurl)
    else:
        user = sys.argv[2]
        passwd = sys.argv[3]
        #print adminurl, user, passwd
        artifacts = get_artifacts(adminurl, user, passwd)

    if artifacts:
        applications, libraries = artifacts
        for artifact in applications:
            print 'Application:', artifact
        for artifact in libraries:
            print 'Library:', artifact

if __name__ == "main":
    _test_get_artifacts()


# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
