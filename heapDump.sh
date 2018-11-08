#!/usr/bin/bash
#set -x

MATCH=${1}
FORCE=${2}

usage() {
    cat <<EOT
usage $0 pattern|pid [-F]

  patttern must match only one Java process in the output of ps

  Generate a heap dump using jmap and saves it into the VAR_STACK directory.
  It must be run from the same server and user id as the process to be dumped.

  Accepts -F as a second option in case force is required.

  Filename will use the weblogicName for the process or the pid to
  identify the heap dump source
EOT
    exit 1
}

if [[ -z ${1} ]]; then
    usage
fi

PS="ps -fu $(id -un)"
if [ -e /usr/ucb/ps ]; then
    PS='/usr/ucb/ps awxx'
fi
PID=(( $(${PS} | awk -f <(cat - <<EOT
    /java/ && /${MATCH}/ {print \$1}
EOT
)))

if [[ ${#PID[@] -ne 1 ]]; then
    echo Matced PIDs: ${PID}
    echo
    usage
if

if [ ! -r /proc/${PID} ]; then
    echo "FATAL: unable to access process ${PID}"
    echo
    usage
fi

server_id=$( ${PS} | grep ${PID} | tr ' ' '\n' | \
        grep weblogic.Name | uniq | cut -d= -f 2 )
if [[ -z ${server_id} ]]; then
    server_id=pid${server_id}
fi
#echo ${server_id}

if [ "${FORCE/-F/}" != '' ]; then
    usage
fi

FILENAME=jmap.${server_id}.$(date +%y%m%d_%H%M).hprof

echo Capturing heap dump. The application server must remain running.
jmap -J-d64 ${FORCE} -dump:format=b,file=${HOME}/${FILENAME} ${PID}
chmod 640 ${HOME}/${FILENAME}

echo Capture is complete.  Appliation server may be killed if required.
if [[  -d ${VAR_STACK} ]]; then
    echo Moving heap dump to ${VAR_STACK}/${FILENAME}
    mv ${HOME}/${FILENAME} ${VAR_STACK} &
    disown
else
    echo Heap dump is ${HOME}/${FILENAME}
fi

# EOF
