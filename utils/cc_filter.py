#!/usr/bin/env python
'''
This program filters a file.

This version is being configured for filtering files containing
credit card numbers.

'''

from __future__ import print_function
from optparse import OptionParser

import gzip
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

def notKnownFalsePositive(line, prefixes, contents):
	for prefix in prefixes:
		if line.startswith(prefix):
			return False
	for content in contents:
		if content in line:
			return False
	return True

def filterFile(fileName):

	''' Filter a file using a fixed regex
	'''
	filePrefix = fileName + ':'
	fileStatus = None
	line = None
	#print(fileName)

	# Known false positive prefixes
	prefixes = ( 'Cookie: ', )
	contents = ( 'com.cpc.security.impl.CpidAuthenticationProcessingFilter',
				'com.cpc.app.fastsearch.utility.FastEngineUtility',
				'/cpotools/apps/track/personal/findByTrackNumber_direct',
				'/cpotools/apps/track/business/findByTrackNumber_direct',
				'com.cpc.ws.client.tap.impl.TapTrackClientImpl',
				'com.cpc.ws.client.tap.TapException',
				'cvc-simple-type 1: element PIN value',
				'com.cpc.cpo.cpid.sso.EasySSOIntegrationHandler',
				'%3FtrackingNumber%3D',
				'trackingNumber=',
				'trackNum=',
				'trackId=',
				'Tracking Number:',
				'Tracking Numbers:',
				'TapException in ImageServlet for PIN:',
				'/cpo/apps/search?query=',
				'/cpotools/apps/fpo/personal/findPostOfficeList?lat',
				'trackingnumber=',
				'tracking_number=',
				'/cpo/mc/personal/campaigns/holiday/default.jsf',
				'com.cpc.cpo.cpid.signin.SignInAction',
				'com.cpc.cpo.cpid.forgotpassword.ForgotPasswordAction',
				'org.springframework.security.authentication.UsernamePasswordAuthenticationToken',
				'Item / PIN Number(s)',
				'PackageService:getClaimsItem',
				'/track/personal/findByTrackNumber_direct',
				'com.cpc.app.common.dcc.DCCService',
				'CPO Payment object, creditCard:',
				'PACKAGE QUERY FAILED, PIN',
				'com.cpc.app.ccm.ServiceTicketForm',
				'/cpo/apps/search?',
				'com.cpc.app.ccm.ServiceTicketForm',
				'/cpotools/mc/app/tpo/orderentry/',
				'/cpotools/apps/track/personal/findByTrackNumber',
				'/cpo/mc/default.jsf?',
				'/cpotools/apps/fpo/business/findPostOfficeList',
				'Error invoking package service for package# :',
				'com.cpc.integration.serviceTicket.ServiceTicketBLImpl',
				'com.cpc.cpo.cpid.itfsvc.impl.LdapSecurityItfSvcImpl',
				'com.cpc.cpo.cpid.itfsvc.impl.SapSecurityItfSvcImpl',
				'com.cpc.cpo.cpid.dao.impl.SapUserDaoImpl',
				'com.cpc.cpo.cpid.service.impl.SecuritySvcImpl',
				'SECURITY password for',
				'SECURITY Bad Credentials for username',
				'SECURITY User',
				'/cpo/mc/default.jsf%3f',
				'/cpotools/mc/app/tpo/pym/targeting.jsf?',
				'com.cpc.tradezoneWS.services.',
				'com.cpc.integration.tap.builder.TapFunctionBuilder',
				'<Distance>',
				'<ZZ_KEYDOC>',
				'<Pin>',
				'<PIN>',
				'<TrxID>',
				'<FileName>',
				'<ReferenceNumber1>',
				'<ReturnPin>',
				'<Line>',
				'GET	/',
				'Headers: {connection=[Keep-Alive], content-type=[text/xml]',
				'Headers: {Accept=[application/soap+xml], connection=[Keep-Alive],',
				'[Cookie] = [',
				'QueryString :[search=',
				'locking account for 1 minutes',
				'|EN|0|PIN',
				'Additional Information:',
				'BadlyFormattedFlowExecutionKeyException: Badly formatted',
				'cvc-simple-type 1: element CollectiveNum value',
				)

	# Patterns for VISA (2), MasterCard, AMEX, and Discover Card (3)
	patterns = ( r'4[0-9]{15}',
				 r'4[0-1][0-9]{11}',
				 r'5[1-5][0-9]{14}',
				 r'3[47][0-9]{13}',
				 r'6011[0-9]{12}',
				 r'622[0-9]{11}',
				 r'6[45][0-9]{14}')

	#matchPattern = r'(([VMAD][A-Z0-9]{2,4}-?)(\d{13,16}))'
	matchPattern = ''.join(('(\A|\D)(?P<CC>', '|'.join(patterns), r')(?!\d)'))
	matcher = re.compile(matchPattern, re.I)

	skipPattern = r'(VIS[A1]|MC1?|AME[1X]|credit card.*)[- ](\d{13,16})(?!\d)'
	skipMatcher = re.compile(skipPattern)

	try:
		for line in openLogFile(fileName):
			#print(line)
			results = matcher.findall(line)

			for result in results:
				#print (', '.join(result))

				if skipMatcher.search(line):
					fileStatus = ' '.join((filePrefix, 'Matched'))
					if not is_luhn_valid(result[1]):
						print(result[1], 'is invalid **')
					#else:
						#print(result[1], 'is valid')
				else:
					if is_luhn_valid(result[1]):
						if notKnownFalsePositive(line, prefixes, contents):
							print(' '.join((filePrefix, result[1], line)))

		if fileStatus is not None:
			print(fileStatus)

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


# EOF
