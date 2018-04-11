#! /usr/bin/env python
'''  Validate XML in files and/or directory trees
'''

import xml.dom.minidom
from os import listdir
from os.path import isfile, isdir, join
from optparse import OptionParser
import sys
import codecs

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

neverNestedTags = (
    'script'
)


class SimpleHTMLValidator(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.openTags = []
        self.tagLocs = []
        self.warnings = False

    def parse(self, filename):
        self.filename = filename
        try:
            try:
                self.feed(codecs.open(filename, encoding='utf-8').read())
            except UnicodeDecodeError:
                if self.warnings:
                    print filename, 'Warning: encoding is not UTF-8 -trying cp1252'
                self.feed(codecs.open(filename, encoding='cp1252').read())
        except OSError as e:
            raise HTMLParseError('Exception ' + type(e).__name__ + ' ' + str(e) , self.getpos())
        except ValueError as e:
            raise HTMLParseError('Exception ' + type(e).__name__ + ' ' + str(e) , self.getpos())

        while self.openTags and self.openTags[-1] in closeOptionalTags:
            openTag = self.openTags.pop()
        if self.openTags:
            raise HTMLParseError('Unclosed tags: ' + ', '.join(self.openTags), self.getpos())
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag in neverNestedTags and tag in self.openTags:
            self.showWarning('"' + tag + '" should not be nested inside another "'
                + tag + '" tag', self.getpos())
        if tag not in singletonTags:
            self.openTags.append(tag)
            self.tagLocs.append(self.getpos())

    def handle_endtag(self, tag):
        if tag in singletonTags:
            self.showWarning('Singleton tag "' + tag + '" used as closing tag', self.getpos())
            return
        if not self.openTags:
            raise HTMLParseError('Extra closing tag "' + tag + '" used', self.getpos())
        while self.openTags:
            openTag = self.openTags.pop()
            tagLoc = self.tagLocs.pop()
            if tag == openTag or openTag not in closeOptionalTags:
                break
        if tag != openTag:
            openMsg = '"{0}" (line {1[0]}, column {1[1]})'.format(openTag, tagLoc)
            raise HTMLParseError('"' + tag + '" tag closes ' + openMsg, self.getpos())

    def handle_startendtag(self, tag, attrs):
        if tag not in singletonTags:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)
        else:
            self.showWarning('Singleton tag "' + tag + '" closed', self.getpos())

    def setWarnings(self, value):
        self.warnings = value

    def showWarning(self, msg, position=None):
        if self.warnings:
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
        parser.setWarnings(options.warnings)
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


def validateFile(fname):
    if fname.split('.')[-1] in ('xml', 'xsl', 'xhtml'):
        validateXML(fname)
    elif fname.endswith('.html'):
        validateHTML(fname)


def validatePath(directory):
    if options.verbose:
        print 'Scanning directory', directory

    for f in listdir(directory):
        entry = join(directory, f)
        if validateFile(entry):
            validateXML(entry)
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
    parser.add_option("-w", "--warnings",
                      action="store_true", dest="warnings", default=False,
                      help="show warning messages")

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

# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
