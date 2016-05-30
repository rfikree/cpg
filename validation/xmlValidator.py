#! /usr/bin/env python
'''  Validate XML in files and/or directory trees
'''

import xml.dom.minidom
from os import listdir
from os.path import isfile, isdir, join
from optparse import OptionParser
import sys

from HTMLParser import HTMLParser, HTMLParseError

singletonTags = (
	'area',
	'base',
	'br',
	'col',
	'command',
	'embed',
	'hr',
	'img',
	'input',
	'link',
	'meta',
	'param',
	'source',
	'frame',
	)

closeOptionalTags = (
	'body',
	'colgroup',
	'dd',
	'dt',
	'head',
	'html',
	'li',
	'optgroup',
	'option',
	'p',
	'tbody',
	'td',
	'tfoot',
	'th',
	'thead',
	'tr',
	)



class SimpleHTMLValidator(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.openTags = []

	def parse(self, filename):
		self.filename = filename
		self.feed(open(filename).read())
		while self.openTags and self.openTags[-1] in closeOptionalTags:
			openTag = self.openTags.pop()
		if self.openTags:
			raise HTMLParseError('Unclosed tags: ' + ', '.join(self.openTags), self.getpos())
			openTags = []
		self.close()

	def handle_starttag(self, tag, attrs):
		if tag not in singletonTags:
			self.openTags.append(tag)

	def handle_endtag(self, tag):
		while self.openTags:
			openTag = self.openTags.pop()
			if openTag in singletonTags:
				self.showWarning('Singleton tag ' + tag + ' closed', self.getpos())
			if tag == openTag or openTag not in closeOptionalTags:
				break;
		if not self.openTags:
			raise HTMLParseError('Extra close tag ' + tag, self.getpos())
		if tag != openTag:
			raise HTMLParseError(tag + ' closes ' + openTag, self.getpos())

	def handle_startendtag(self, tag, attrs):
		if tag not in singletonTags:
			self.handle_starttag(tag, attrs)
			self.handle_endtag(tag)
		else:
			self.showWarning('Singleton tag ' + tag + ' /closed', self.getpos())

	def showWarning(self, msg, position=None):
		if not position:
			position = self.getpos()
		(lineno, offset) = position
		if self.lineno is not None:
			msg = msg + ", at line %d" % lineno
		if self.offset is not None:
			msg = msg + ", column %d" % (offset + 1)

		print self.filename, 'WARNING:', msg


def validateHTML(filename):
	try:
		parser =  SimpleHTMLValidator()
		parser.parse(filename)
		if options.verbose:
			print filename, 'is valid'
	except HTMLParseError as e:
		msg = str(e)
		print filename, msg


def validateXML(filename):
	try:
		xml.dom.minidom.parse(filename)
		if options.verbose:
			print filename, 'is valid'
	except xml.parsers.expat.ExpatError as e:
		msg = str(e)
		print filename, msg


def validatePath(directory):
	if options.verbose:
		print 'Scanning directory', directory

	for f in listdir(directory):
		entry = join(directory, f)
		if isfile(entry) and (entry.endswith('.xml') or entry.endswith('.xhtml')):
			validateXML(entry)
		elif isfile(entry) and (entry.endswith('.html') or entry.endswith('.html')):
			validateHTML(entry)
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
			validateXML(source)
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