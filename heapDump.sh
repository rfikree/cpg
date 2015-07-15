#!/usr/bin/bash
set -x

server_id=$1
force=$2

usage() {
	cat <<EOF
usage $0 server_id|pid [-F]

  server id must be specified the form 'a1p10d1-c1m1ms01'

  Generate a heap dump using jmap and saves it into the VAR_STACK directory.
  It must be run from the same server and user id as the process to be dumped.

  Accepts -F as a second option in case force is required.
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

if [ "${force/-F/}" != '' ]; then
	usage
fi

if [ ! -d ${VAR_STACK} ]; then
	usage
fi

if [ ! -r /proc/${pid} ]; then
	echo "FATAL: unable to read data for pid ${pid}"
	usage
fi

filename=jmap.${server_id}.$(date +%y%m%d_%H%M).hprof

echo Capturing heap dump. The application server must remain running.
jmap -J-d64 ${force} -dump:format=b,file=${HOME}/${filename} ${pid}
chmod 640 ${HOME}/${filename}

echo Capture is complete.  Appliation server may be killed if required.
echo Moving heap dump to ${VAR_STACK}/${filename}
mv ${HOME}/${filename} ${VAR_STACK} &
disown

# EOF
