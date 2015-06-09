#!/usr/bin/bash
#set -x

server_id=$1

usage() {
	cat <<EOF
usage $0 server_id|pid

  server id must be specified the form 'a1p10d1-c1m1ms01'

  Generate a thread dump using jstack and saves it into the VAR_STACK directory.
  It must be run from the same server and user id as the process to be dumped.

EOF
	exit 1
}

if [ $# -ne 1 ]; then
	usage
fi

if [ "${server_id/a[1-6][dsp][1-6][0-5]d[129]-c[1-9]m[1-4]ms0[1-9]/}" == '' ]; then
	pid=$(/usr/ucb/ps -axww | grep [w]eblogic.Name=$server_id | \
					cut -c 1-6 | tr -d ' ' )
elif [ "${server_id/[0-5]*/}" == '' ]; then
	pid=${server_id}
	server_id=pid${server_id}
else
	usage
fi

if [ ! -d ${VAR_STACK} ]; then
	usage
fi

if [ ! -r /proc/${pid} ]; then
	echo "FATAL: unable to read data for pid ${pid}"
	usage
fi

pid=$(/usr/ucb/ps -axww | grep [w]eblogic.Name=$server_id | cut -c 1-6)
logname=${VAR_STACK}/jstack.$server_id.$(date +%y%m%d_%H%M%S)

echo Saving thread_dump to $logname
jstack -l $pid > $logname

# EOF