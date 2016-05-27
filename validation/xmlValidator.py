#! /usr/bin/env python
'''  Validate XML in files and directory trees
'''


import xml.dom.minidom
from os import listdir
from os.path import isfile, isdir, join
from optparse import OptionParser
import sys


def validateFile(filename):
	try:
		xml.dom.minidom.parse(filename)
		if options.verbose:
			print filename, 'is valid'
	except xml.parsers.expat.ExpatError as e:
		msg = str(e)
		if 'invalid token' in msg:
			pass
#		elif 'junk after document element' in msg:
#			pass
		else:
			print filename, msg


def validatePath(directory):
	if options.verbose:
		print 'Scanning directory', directory

	for f in listdir(directory):
		entry = join(directory, f)
		if isfile(entry) and (entry.endswith('.xml') or entry.endswith('.xhtml')):
			validateFile(entry)
		elif options.recurse and isdir(entry):
			validatePath(entry)


def main():
	global options
	usage = "usage: %prog [options] filename|directory ..."

	parser = OptionParser(usage=usage)
	parser.add_option("-n", "--norecurse",
					  action="store_false", dest="recurse",
					  help="don't recurse into directories")
	parser.add_option("-q", "--quiet",
					  action="store_false", dest="verbose", default=False,
					  help="don't print valid files or requested directories")
	parser.add_option("-r", "--recurse",
					  action="store_true", dest="recurse", default=False,
					  help="recurse into directories")
	parser.add_option("-v", "--verbose",
					  action="store_true", dest="verbose",
					  help="print valid files and requested directories")

	(options, args) = parser.parse_args()

	for source in args:
		if isfile(source):
			validateFile(source)
		elif isdir(source):
			validatePath(source)
		else:
			print "Invalid entry", source


if __name__  == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print 'User canceled scan'
		pass

# EOF