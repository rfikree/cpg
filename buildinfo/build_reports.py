#! /usr/bin/env wlst.sh
'''build_report.py - build the build information reports.

Uses the buildReports.properties file to identify the URLs for the
WebLogic Admin Servers to connect to.
'''

import getopt
import os
import sys
#import filecmp     # Need to be on WebLogic 12c - see end of file.

from components import get_artifacts
from generate_report import gen_report
from ordered_config_parser import ConfigParser

def usage(status):
    '''Print the usage documentation for this application'''
    print '''

    Usage: ./buildReports.py [-h] [-e environment] [-u user] [-p passsword]

    Options
        -h, --help: Print this help message
        -e, --environment: Specify environment to run for
        -u, --user: Specify user to connect with
        -p, --password: Specify the password to connect with

    Valid environments are defined in buildReports.properties.

    '''
    sys.exit(status)

def get_stacks(config, environment):
    '''Generate a list of stacks add related URLs from a list'''
    stack_list = config.options(environment)
    #print 'stack_list:', stack_list
    if not stack_list:
        #print 'FATAL: Environment', environment, 'has no stacks.'
        sys.exit(2)

    stacks = []
    stack_list.sort()
    for stack_name in stack_list:
        urls = config.get(environment, stack_name).split('\n')
        stacks.append((stack_name, urls))

    #print 'stacks:', stacks
    return stacks

def get_components(urls, user, passwd):
    '''Get the components for a stack - one or more URLs'''
    components = []

    for url in urls:
        artifacts = get_artifacts(url, user, passwd)
        if artifacts:
            components.append((url, artifacts))

    #print components
    return components

def save_report(report_name, report):
    '''Save the report to a file'''
    filename = ''.join((report_name, '-build.html'))
    _f = open(filename, 'w')
    _f.write(report)
    _f.close()


def add_state_section(state, section, states):
    '''Add properties to a section, creating section if needed'''
    _states = states[:]
    if not _states:
        return
    _states.sort()
    if not state.has_section(section):
        state.add_section(section)
    for item, version, _state, _targets in _states:
        state.set(section, item, version)


def save_state(stack_name, stack_components):
    '''Save the state (artifacts and versions) to a file'''
    state = ConfigParser()
    for (dummy, components) in stack_components:
        artifacts, libaries = components
        add_state_section(state, 'artifacts', artifacts)
        add_state_section(state, 'libraries', libaries)

    filename = ''.join((stack_name, '.properties.new'))
    propfile = ''.join((stack_name, '.properties'))
    _f = open(filename, 'w')
    state.write(_f)
    _f.close()
    if _file_cmp(filename, propfile):
        os.remove(filename)
    else:
        os.rename(filename, propfile)


def create_reports(property_file, environment, user, passwd):
    '''Create the reports for the selected environment'''
    all_components = []
    config = ConfigParser()
    config.read(property_file)
    if not config.has_section(environment):
        print 'FATAL: Invalid environment', environment, 'selected.'
        sys.exit(2)

    stacks = get_stacks(config, environment)
    #print 'stacks:', stacks

    # Generate reports for each stack
    for (stack_name, urls) in stacks:
        #print 'stack_name:', stack_name, ' - urls:', urls
        stack_components = get_components(urls, user, passwd)
        if stack_components:
            save_state(stack_name, stack_components)
            #print 'stack_components:', stack_components
            report = gen_report(stack_name, stack_components)
            #print report
            save_report(stack_name, report)
            all_components.extend(stack_components)

    # Generate report for all stacks
    if all_components:
        title = config.get('titles', environment)
        report = gen_report(title, all_components)
        #print report
        save_report(environment, report)


def main():
    '''Read options and generate reports'''

    user = 'Deployment Monitor'
    passwd = 'yIHj6oSGoRpl66muev5S'

    #print 'sys.argv:', sys.argv
    property_file = sys.argv[0][:-2] + 'properties'

    try:
        options, _a = getopt.getopt(sys.argv[1:],
                                    'he:u:p:',
                                    ['help', 'enviroment=', 'user=', 'password='])
    except getopt.GetoptError:
        # print help information and exit:
        usage(2)

    if not options:
        usage(2)

    # Process setup options
    for _o, _a in options:
        if _o in ('-h', '--help'):
            usage(0)
        elif _o in ('-u', '--user'):
            user = _a
        elif _o in ('-p', '--password'):
            passwd = _a

    # Run the report
    for _o, _a in options:
        if _o in ('-e', '--enviroment' and _a != 'titles'):
            #print 'property_file, _a', property_file, _a
            create_reports(property_file, _a, user, passwd)
        elif _o in ('-e', '--enviroment'):
            usage(2)

def _file_cmp(file1, file2):
    ''' File cmp based on library module '''
    bufsize = 8192
    status = False
    try:
        _fp1 = open(file1, 'rb')
        _fp2 = open(file2, 'rb')
        while True:
            _b1 = _fp1.read(bufsize)
            _b2 = _fp2.read(bufsize)
            if _b1 != _b2:
                break
            if not _b1:
                status = True
                break
        _fp1.close()
        _fp2.close()
    except:     # pylint: disable=bare-except
        pass
    return status


if __name__ == 'main':
    try:
        main()
    except KeyboardInterrupt, _e:
        print
        print 'Processing cancelled'
        print

# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
