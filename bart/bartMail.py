#!/usr/bin/env python

"""Send the contents of a directory and/or file(s) as a MIME message."""

import os
import sys
import smtplib
# For guessing MIME type based on file name extension
import mimetypes

from optparse import OptionParser
from optparse import OptionGroup

from email import encoders
#from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

COMMASPACE = ', '

def add_directory(outer, directory):
    '''Add the files in a directory to the message without recursion'''
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            add_file(outer, filename)

def add_file(outer, path):
    '''Add a file to the message'''
    if not os.path.isfile(path):
        print 'Warning: file not found -', path
        return
    filename = os.path.basename(path)

    # Additioanal mimetypes
    mimetypes.add_type('text/plain', '.log')
    # Guess the content type based on the file's extension.  Encoding
    # will be ignored, although we should check for simple things like
    # gzip'd or compressed files.
    ctype, encoding = mimetypes.guess_type(path)
    if ctype is None or encoding is not None:
        # No guess could be made, or the file is encoded (compressed), so
        # use a generic bag-of-bits type.
        ctype = 'application/octet-stream'

    maintype, subtype = ctype.split('/', 1)
    if maintype == 'text':
        fp = open(path, 'rU')	# Ensure Unix line endings
        # Convert to DOS line endings and use default characterset
        msg = MIMEText(fp.read().replace('\n', '\r\n'), _subtype=subtype)
        fp.close()
    elif maintype == 'image':
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'audio':
        fp = open(path, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=subtype)
        fp.close()
    else:
        fp = open(path, 'rb')
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(fp.read())
        fp.close()
        # Encode the payload using Base64
        encoders.encode_base64(msg)
    # Set the filename parameter
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    outer.attach(msg)

def main():
    ''' Parse the arguements and send a message.
        This is an enhanced replacement for mailx in send mode.
    '''
    parser = OptionParser(usage="""\
Send the contents of a directory as a MIME message.

Usage: %prog [options]

Unless the -o option is given, the email is sent by forwarding to your local
SMTP server, which then does the normal delivery process.  Your local machine
must be running an SMTP server.
""")
    parser.add_option('-F', '--from',
                      type='string', action='store', metavar='FROM',
                      dest='sender',
                      help='The value of the From: header (required)')
    parser.add_option('-t', '--to',
                      type='string', action='append', metavar='RECIPIENT',
                      default=[], dest='recipients',
                      help='A To: header value (at least one required)')
    parser.add_option('-c', '--cc',
                      type='string', action='append', metavar='RECIPIENT',
                      default=[], dest='cc_recipients',
                      help='A CC: header value')
    parser.add_option('-s', '--subject',
                      type='string', action='store', metavar='SUBJECT',
                      help='Optional  subject for this message')

    group = OptionGroup(parser, "Content Options - at least one required")
    group.add_option('-d', '--directory',
                     type='string', action='store', metavar='DIRECTORY',
                     default=None, dest='directory',
                     help="""Mail the contents of the specified directory,
                     otherwise don't use a directory.  Only the regular
                     files in the directory are sent, and we don't recurse to
                     subdirectories.""")
    group.add_option('-f', '--file',
                     type='string', action='append', metavar='FILEPATH',
                     default=[], dest='files',
                     help="""Mail the contents of the specified file,
                     otherwise use the directory.  Only the regular
                     files in the directory are sent, and we don't recurse to
                     subdirectories.""")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Delivery Options - optional")
    group.add_option('-S', '--server',
                     type='string', action='store', metavar='SERVER',
                     default='localhost',
                     help='The server to send the message to')
    group.add_option('-o', '--output',
                     type='string', action='store', metavar='FILE',
                     help="""Print the composed message to FILE instead of
                     sending the message to the SMTP server.""")
    parser.add_option_group(group)

    opts, args = parser.parse_args()
    if not opts.sender or not opts.recipients:
        parser.print_help()
        sys.exit(1)
    if not opts.directory and not opts.files:
        parser.print_help()
        sys.exit(1)
    if args:
        parser.print_help()
        sys.exit(1)

    # Create the enclosing (outer) message
    outer = MIMEMultipart()
    outer['From'] = opts.sender
    outer['To'] = COMMASPACE.join(opts.recipients)
    if opts.cc_recipients:
        outer['CC'] = COMMASPACE.join(opts.cc_recipients)
        opts.recipients.extend(opts.cc_recipients)
    if opts.subject:
        outer['Subject'] = opts.subject
    outer.preamble = 'This message is intended for a MIME-aware mail reader.\n'

    if opts.directory:
        add_directory(outer, opts.directory)
        if not opts.subject:
            outer['Subject'] = 'Contents of directory %s' % os.path.abspath(opts.directory)
    else:
        if not opts.subject:
            outer['Subject'] = 'Contents of file(s): %s' % COMMASPACE.join(opts.files)
        for filename in opts.files:
            add_file(outer, filename)

     # Now send or store the message
    composed = outer.as_string()
    if opts.output:
        fp = open(opts.output, 'w')
        fp.write(composed)
        fp.close()
    else:
        smtp = smtplib.SMTP(opts.server)
        smtp.sendmail(opts.sender, opts.recipients, composed)
        smtp.quit()


if __name__ == '__main__':
    main()
