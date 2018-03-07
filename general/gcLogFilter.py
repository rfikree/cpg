#!/usr/bin/python

# NOTES:
# - Expects timestamped data to be on a single line.
#   There appear to be occational records which do not follow this format.
# - Funtionality to provide the basetime in various manners is provided to
#   Support rotated logs.

import getopt, os, re, sys, time


def usage():
    print "Usage:", sys.argv[0],  "[OPTION] gcLogFileName"
    print
    print "Filters a Java GC log replacing offsets with ISO8601 timestamps"
    print "  unless otherwise specified with one of the optiions"
    print "  offsets are relative to the log creation time."
    print ""

    print "Options:"
    print "  -p, --pid         PID from which to get time base"
    print "  -t, --timestamp   Time base formatted YYYY-MM-DD HH:MM:SS"
    print "  -o, --offset      Time base as an offset from epoch"
    print "  -v, --verbose     Print lines without offsets"
    sys.exit(2)


def formatDate(ordinal, format='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format, time.localtime(ordinal))

def offsetFromString(offset, format='%Y-%m-%d %H:%M:%S'):
    try:
        return time.mktime(time.strptime(offset, format))
    except:
        print "ERROR: Unable to parse timestamp: ", offset

def getBasetime(file):
    try:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
        #print "last changed: %s" % time.ctime(ctime)
        return ctime
    except OSError:
        print "ERROR: Unable to stat file: ", file
        return None

def filterFile(file, baseTime, verbose):
    pattern = re.compile ('^(\d+.\d+):\s+(.*)')

    try:
        infile = open(file)
    except IOError:
        print "ERROR: Unable to read file: ", file
        return

    if baseTime is None:
        baseTime = getBasetime(file)
        print "Using file creation timestamp", formatDate(baseTime), "\n"

    for line in infile:
        found = pattern.match(line)
        if found:
            logTime = formatDate( baseTime + float( found.group(1)),
                '%Y-%m-%dT%H:%M:%S:' )
            print logTime, found.group(2)
        elif verbose:
            print line,

    infile.close()


# Mainline code  starts here
try:
    opts, args = getopt.getopt(sys.argv[1:], "hp:t:o:v",
        ["help", "pid=", "timestamp=", "offset=", "verbose"])
except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()

basetime = None
verbose = None

for o, a in opts:
    if o in ("-h", "--help"):
        usage()
    elif o in ("-p", "--pid"):
        basetime = getBasetime( "/proc/" + a )
    elif o in ("-t", "--timestamp"):
        basetime = offsetFromString(a)
    elif o in ("-o", "--offset"):
        basetime = float(a)
    elif o in ("-v", "--verbose"):
        verbose = True

if len(args) == 1:
    filterFile(args[0], basetime, verbose)
else:
    usage()

## jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
