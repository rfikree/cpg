#!/usr/bin/bash
#set -x

. /lib/svc/share/smf_include.sh
# SMF_FMRI is the name of the target service. This allows multiple instances
# to use the same script - Expects instance name to be the stackname
SERVICE=${SMF_FMRI##*:}

# Build domain and stack variable from sevice name
DOMAIN=a${SERVICE:3:1}${SERVICE:0:1}${SERVICE:3:2}
STACK=${DOMAIN}${SERVICE:5:2}

# Variables needed by SOA Suite for locale setting
export LANG=en_CA.UTF-8
export LC_ALL=en_CA.UTF-8
export LC_MONETARY=en_CA.UTF-8
export LC_NUMERIC=en_CA.UTF-8
export LC_ALL=en_CA.UTF-8
export LC_MESSAGES=C
export LC_COLLATE=en_CA.UTF-8
export LC_CTYPE=en_CA.UTF-8
export LC_TIME=en_CA.UTF-8

# Find the pid of the running process, if any
PID=$(/usr/ucb/ps -xwww | nawk "/[j]ava.*${STACK}/ {print \$1}")

START_SCRIPT=/cpg/cpo_apps/${DOMAIN}/${STACK}/bin/startWebLogic.sh
STOP_SCRIPT=/cpg/cpo_apps/${DOMAIN}/${STACK}/bin/stopWebLogic.sh
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
		sleep 5 	# Wait for Background to start Java process
	else
		echo ${SMF_FRMI} already running with pid ${PID}
		exit ${SMF_EXIT_OK}
	fi
}

doStop() {
	if [[ -n ${PID} ]]; then
		${STOP_SCRIPT}
		waitPid 20
		kill -0 ${PID} 2>/dev/null && kill -TERM ${PID}
		waitPid 30
		kill -0 ${PID} 2>/dev/null && kill -KILL ${PID}
		waitPid 5
		kill -0 ${PID} 2>/dev/null || exit ${SMF_EXIT_ERR_FATAL}
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
