#!/usr/bin/env python
'''
This program masks credit card numbers a file.

This version expects a known prefix before the credit card number.
These prefixes have been identified by extensive pattern matching.
'''

from __future__ import print_function
from optparse import OptionParser

import gzip
import os
import sys
import re

def openLogFile(fileName):
    '''Open a file even if it is compressed
    '''
    if fileName.endswith('.gz'):
        return gzip.open(fileName, 'r')
    else:
        return open(fileName, 'r')

def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    #print(card_number, checksum % 10, digits[-1])
    return checksum % 10

def is_luhn_valid(card_number):
    return luhn_checksum(card_number) == 0

def filterFile(fileName):

    ''' Filter a file using a fixed regex
    '''
    filePrefix = fileName + ':'
    fileChanged = False
    line = None
    #print(fileName)

    #matchPattern = r'(((VIS|MC|AME)[A-Z0-9]{1,4}-?\d{4})(\d{2,9})(\d{4})(?!\d))'
    #matchPattern = r'(([VMAD][A-Z0-9]{2,4}-?)(\d{13,16}))'
    #matcher = re.compile(matchPattern, re.I)

    matchPattern = r'(VIS[A1]|MC1?|AME[1X]|credit card.*)[- ]\#?(\d{13,16})(?!\d)'
    matcher = re.compile(matchPattern)

    try:
        baseFileName = fileName
        if baseFileName.endswith('.gz'):
            baseFileName = baseFileName[:-3]
        outFileName = baseFileName + '.tmp'
        outFile = open(outFileName, 'w')

        for line in openLogFile(fileName):
            result = matcher.search(line)

            if (result):
                fileChanged = True
                ccNumber = result.group(2)
                ccMasked  = '*' * (len(ccNumber) - 4 ) + ccNumber[-4:]
                line = line.replace(ccNumber, ccMasked)

            outFile.write(line)

        outFile.close()

        if fileChanged:
            # Touch and replace
            fileStats = os.stat(fileName)
            fileTimes = (fileStats.st_atime ,fileStats.st_mtime)
            os.utime(outFileName, fileTimes)
            os.remove(fileName)
            os.rename(outFileName, baseFileName)
            print("Masked CC numbers in", fileName)
        else:
            os.remove(outFileName)

    except Exception, e:
        print ('Failed to process', fileName)
        if line is not None:
            print ('Line: ', line)
        if e is not None:
            print (e)
        pass


def main():
    ''' Read options and process file(s)
    '''

    # Set defaults

    # Build and execute command line parser
    parser = OptionParser(version='0.1')

    (options, args) = parser.parse_args()

    for arg in args:
        filterFile(arg)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt, e:
        print ()
        print ('Processing cancelled')
        print ()
    except Exception, e:
        print ()
        print ('FATAL Unhandled Exception')
        print (e)


# jedit	:tabSize=4:indentSize=4:noTabs=true:mode=python:
# vim: ai ts=4 sts=4 et sw=4 ft=python
# EOF
