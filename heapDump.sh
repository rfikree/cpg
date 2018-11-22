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

PS="ps -o pid,args -u $(id -un)"
[ -e /usr/ucb/ps ] && PS='/usr/ucb/ps axww'
PID=( $(${PS} | awk "\$1 ~ /^${MATCH}\$/ || /[j]ava.*${MATCH}/ {print \$1}") )

if [[ ${#PID[@]} -ne 1 ]]; then
    echo Matched PIDs: ${PID[@]}
    echo
    usage
fi

if [ ! -r /proc/${PID} ]; then
    echo "FATAL: unable to access process ${PID}"
    echo
    usage
fi

server_id=$( ${PS} | grep ${PID} | tr ' ' '\n' | \
        grep weblogic.Name | uniq | cut -d= -f 2 )
[[ -z ${server_id} ]] && server_id=pid${server_id}
#echo ${server_id}

if [ "${FORCE/-F/}" != '' ]; then
    usage
fi

FILENAME=jmap.${server_id}.$(date +%y%m%d_%H%M).hprof

echo Capturing heap dump. The application server must remain running.
jmap -J-d64 ${FORCE} -dump:format=b,file=${HOME}/${FILENAME} ${PID}
chmod 640 ${HOME}/${FILENAME}

echo Capture is complete.  Application server may be killed if required.
if [[  -d ${VAR_STACK} ]]; then
    echo Moving heap dump to ${VAR_STACK}/${FILENAME}
    mv ${HOME}/${FILENAME} ${VAR_STACK} &
    disown
else
    echo Heap dump is ${HOME}/${FILENAME}
fi

# EOF
