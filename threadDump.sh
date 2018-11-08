#!/usr/bin/bash
#set -x

MATCH=${1}

usage() {
    cat <<EOT
usage $0 pattern|pid [-F]

  patttern must match only one Java process in the output of ps

  Generate a heap dump using jmap and saves it into the VAR_STACK directory.
  It must be run from the same server and user id as the process to be dumped.

  Accepts -F as a second option in case force is required.

  Filename will use the weblogicName for the process or the pid to
  identify the thread dump source
EOT
    exit 1
}

if [[ -z ${1} ]]; then
    usage
fi

PS="ps -fu $(id -un)"
FIELD=2
if [ -e /usr/ucb/ps ]; then
    PS='/usr/ucb/ps awxx'
    FIELD=1
fi
PID=( $(${PS} | awk -f <(cat - <<EOT
    /java/ && /${MATCH}/ {print \$${FIELD}}
EOT
) ) )

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
if [[ -z ${server_id} ]]; then
    server_id=pid${server_id}
fi
#echo ${server_id}

if [[ -z ${VAR_STACK} || ! -d ${VAR_STACK} ]]; then
    VAR_STACK=/tmp
fi
LOGNAME=${VAR_STACK}/jstack.${server_id}.$(date +%y%m%d_%H%M%S)

echo Saving thread_dump to $LOGNAME
jstack -l ${PID} > $LOGNAME

# EOF
