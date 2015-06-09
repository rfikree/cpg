#!/usr/bin/bash
#set -x

server_id=$1

usage() {
	cat <<EOF
usage $0 server_id

  server id must be specified the form 'a1p10d1-c1m1ms01'

  Generate a tranlate gc log file and saves it into the VAR_STACK directory.
  It must be run from the same server and user id as the server to reported on.

EOF
	exit 1
}

if [ $# -ne 1 ]; then
	usage
fi

if [ "${server_id/a[1-6][dsp][1-6][0-5]d[129]-c[1-9]m[1-4]ms0[1-4]/}" != '' ]; then
	usage
fi

if [ ! -d ${VAR_STACK} ]; then
	usage
fi

pid=$(/usr/ucb/ps -axww | grep [w]eblogic.Name=$server_id | cut -c 1-6)
logfile=${VAR_STACK}/${server_id}-gc.$(date +%y%m%d_%H%M)

echo Processing gc log to $logname
${0%sh}py -p ${pid} $VAR_STACK/*/servers/${server_id}-gc.log | tee ${logfile}

# EOF
