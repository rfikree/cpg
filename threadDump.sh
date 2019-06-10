#!/usr/bin/bash
#set -x

MATCH=${1}

for JAVA_VERSION in $(ls -drt /cpg/3rdParty/installs/java/jdk1.8* 2>/dev/null); do
    if [ -d ${JAVA_VERSION} ]; then
        JAVA_HOME=${JAVA_VERSION}
    else
        echo ${JAVA_VERSION} is invalid
        exit 1
    fi
done

PATH=${JAVA_HOME}/bin:/usr/xpg4/bin:${PATH}


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

if [[ -z ${VAR_STACK} ]]
    VAR_STACK=/cpg/cpo_var/a${LOGNAME:3:1}${LOGNAME:0:1}${LOGNAME:3:2}
fi
if [[ -d ${VAR_STACK} ]]; then
    VAR_STACK=/tmp
fi
LOGNAME=${VAR_STACK}/jstack.${server_id}.$(date +%y%m%d_%H%M%S)

echo Saving thread_dump to $LOGNAME
jstack -l ${PID} > $LOGNAME
cmdStatus=$?
if [[ ${cmdStatus} -ne 0 ]];
    echo jstack failed with status ${cmdStatus}
fi
exit ${cmdStatus}


# EOF
