#!/usr/bin/bash
#set -x

. /lib/svc/share/smf_include.sh
# SMF_FMRI is the name of the target service. This allows multiple instances
# to use the same script - Expects instance name to be the stackname
SERVICE=$(SMF_FRMI##*:}

# Build domain and stack variable from sevice name
DOMAIN=a${SERVICE:3:1}${SERVICE:0:1}${SERVICE:3:2}
STACK=${DOMAIN}${SERVICE:5:2}

# Find the pid of the running process, if any
PID=$(/usr/ucb/ps -xwww | awk "/[j]ava.*${DOMAIN}/ {print \$1}")

START_SCRIPT=/cpg/cpo_apps/${DOMAIN}/${STACK}/bin/startNodeManager.sh


waitPid() {
	if [[ -n ${PID} ]]; then
		time=0
		while [[ ${time} -lt ${1:10} ]]; do
			sleep 1
			kill -0 ${PID} 2>/dev/null || break
			time=$(( time + 1 ))
		done
	fi
}

doStart() {
	if [[ -z ${PID} ]]; then
		${START_SCRIPT}
	else
		echo ${SMF_FRMI} already running with pid ${PID}
		exit ${SMF_EXIT_MON_DEGRADE}
	fi
}

doStop() {

	if [[ -n ${PID} ]]; then
		kill -HUP ${PID}
		time=0
		waitPid 10
		kill -0 ${PID} 2>/dev/null && kill -TERM ${PID}
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
		echo Action \"${1}" is not supported
		echo Use start|stop|restart
		exit ${SMF_EXIT_ERR_CONFIG}
		;;
esac

exit ${SMF_EXIT_OK}