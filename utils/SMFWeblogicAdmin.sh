#!/usr/bin/bash
#set -x

. /lib/svc/share/smf_include.sh
# SMF_FMRI is the name of the target service. This allows multiple instances
# to use the same script - Expects instance name to be the stackname
SERVICE=${SMF_FMRI##*:}

# Build domain and stack variable from sevice name
DOMAIN=a${SERVICE:3:1}${SERVICE:0:1}${SERVICE:3:2}
STACK=${DOMAIN}${SERVICE:5:2}

# Get User who is running script
USERNAME=`getproparg method_context/user`

# Set the vendor so we get the right JVM
JAVA_VENDOR=Sun
export JAVA_VENDOR

# Variables needed by SOA Suite for locale setting
LANG=en_CA.UTF-8
LC_ALL=en_CA.UTF-8
LC_MONETARY=en_CA.UTF-8
LC_NUMERIC=en_CA.UTF-8
LC_ALL=en_CA.UTF-8
LC_MESSAGES=C
LC_COLLATE=en_CA.UTF-8
LC_CTYPE=en_CA.UTF-8
LC_TIME=en_CA.UTF-8
export LANG LS_ALL LC_MONETARY LC_NUMERIC LC_ALL
export LC_MESSAGES LC_COLLATE LC_CTYPE LC_TIME


# Find the pid of the running process, if any
PS="ps -uf ${USERNAME} -o pid,args"
[ -e /usr/ucb/ps ] && PS='/usr/ucb/ps wxx'
PID=( $(${PS} | awk -f "/[j]ava.*${STACK}/ {print \$1}") )

DOMAIN_HOME=/cpg/cpo_apps/${DOMAIN}/${STACK}
START_SCRIPT=${DOMAIN_HOME}/bin/startWebLogic.sh
STOP_SCRIPT=${DOMAIN_HOME}/bin/stopWebLogic.sh
LOG_DIR=/cpg/cpo_var/${DOMAIN}/${STACK}/servers/runtime
LOG_FILE=${LOG_DIR}/AdminServer_nohup.out

waitPid() {
    if [[ -n ${PID} ]]; then
        time=0
        while [[ ${time} -lt ${1:-10} ]]; do
            sleep 1
            kill -0 ${PID} 2>/dev/null || break
            time=$(( time + 1 ))
        done
    fi
}

doStart() {
    [[ -d ${LOG_DIR} ]] || mkdir -m 755 ${LOG_DIR}
    if [[ -z ${PID} ]]; then
        ${START_SCRIPT} &> ${LOG_FILE} & 	# Run in background
        echo ${SMF_FRMI} starting Weblogic $!
        sleep 5 	# Wait for Background to start Java process
    else
        echo ${SMF_FRMI} already running with pid ${PID}
        exit ${SMF_EXIT_OK}
    fi
}

doStop() {
    if [[ -n ${PID} ]]; then
        cd ${DOMAIN_HOME}
        ${STOP_SCRIPT}
        waitPid 90
        kill -0 ${PID} 2>/dev/null && kill -TERM ${PID}
        waitPid 60
        kill -0 ${PID} 2>/dev/null && kill -KILL ${PID}
        waitPid 5
        kill -0 ${PID} 2>/dev/null && exit ${SMF_EXIT_ERR_FATAL}
    fi
}

if [ ! -f ${START_SCRIPT} ]; then
    echo FATAL: ${START_SCRIPT} not found
    exit ${SMF_EXIT_ERR_PERM}
fi

case ${1} in
    start)
        doStart
        ;;
    stop)
        doStop
        ;;
    restart)
        doStop
        waitPid 10
        doStart
        ;;
    *)
        echo Action \"${1}\" is not supported
        echo Use start\|stop\|restart
        exit ${SMF_EXIT_ERR_CONFIG}
        ;;
esac

exit ${SMF_EXIT_OK}
