#!/usr/bin/env python
''' statsmerge - will merge muiltiple stats files.

Lines will be prefixed with a file index.
'''

import sys
import os
import heapq
import getopt

def standard_keyfunc(line):
	""" The standard key function in my application.
	    Keys are fudged for headers (nonURLs)
	"""
	fields = line.split()
	if len(fields) < 8:
		if line.startswith('Parsed:'):
			key = '+'
		else:
			key = '~' + ' '.join(fields[1:])
	else:
		if fields[0] == 'Count':
			key = '-'
		else:
			key = ' '.join(fields[7:])
	return key

def decorated_file(f, key):
    """ Yields an easily sortable tuple.
        Tuple will retain file ordering, and provides a print line in
        addition to the original line.
        Printline is prefixed with a file id unless it is a header
        starting wih a space.
    """
    for line in f:
    	fileno = f.fileno() - 2
    	filekey = key(line)
    	if filekey != '-':
    		printline = '%2d %s' % (fileno, line)
    	else:
    		printline = '   %s' % (line,)
        yield (key(line), fileno, line, printline)

def mergeSortedFiles(paths, outfile, dedup=True, keyfunc=standard_keyfunc):
	""" Does the same thing SortedFileMerger class does.
	"""
	files = map(open, paths) #open defaults to mode='r'
	oline = ['', 0, '', '']
	output = open(outfile, 'w') if outfile else sys.stdout

	for line in heapq.merge(*[decorated_file(f, keyfunc) for f in files]):
		# Eat empty lines
		if len(line[2]) < 2:
			continue
		# Add a blank line between key changes
		if line[1] <= oline[1] or line[0] != oline[0]:
			output.write('\n')
		# Don't print duplicate lines (headers & others)
		if line[2] != oline[2]:
			output.write(line[3])
		oline = line

def usage(status=0):
  	print ('''
This program merges statistics reports generated by logstats.py.
''')
  	print ('Usage:', sys.argv[0].split('/')[-1], '[options] file...')
  	print ('''
Options:
    --help (-?):  Print this usage
    --output (-o) <file>: Output report to specified file (default stdout)
''')
	sys.exit(status)

def main():
	outfile = None

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'ho:',
			['help', 'output='])

		for opt, arg in opts:
			if opt in ('-h', '--help'):
			  usage()
			elif opt in ('-o', '--output'):
				outfile = arg

	except getopt.GetoptError,e:
		print (e)
		usage(2)
	except Exception, e:
		print (e)
		usage(-1)

	if not args:
		usage()

	mergeSortedFiles(args, outfile)

if __name__ == '__main__':
	main()

# EOF
