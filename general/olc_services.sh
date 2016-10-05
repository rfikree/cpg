#!/bin/sh
#set -x

# Ensure workable PATH
SAVE_PATH=${PATH}
PATH=/sbin:/bin:/usr/sbin:/usr/bin
export PATH

# Config parameters
SCRIPT=`python -c "import os,sys; print os.path.realpath(sys.argv[1])" ${0}`
SCRIPT_NAME=`basename ${SCRIPT}`
HOSTNAME=`hostname`

# Required dirs
DIRS="/cpg/3rdParty /cpg/cpo_apps /cpg/cpo_var"

INTROSCOPE_DIR=/cpg/3rdParty/installs/introscope/9.7.1.0
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles

CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
CPG_HOSTNAME=`egrep -i "^${HOSTNAME}," \
	${CPG_ALIAS_LOOKUP_FILE} | cut -d, -f2`
export CPG_HOSTNAME

USERPREFIX=`echo ${CPG_HOSTNAME} | cut -d- -f1`


#### Function definitions

startEPAgent() {
	if `ps -fu apm | grep [j]ava >/dev/null`; then
		echo Introscope EPAgent is already running
	else
		echo Introscope EPAgent is NOT running
		$SKIP su - apm -c "${INTROSCOPE_DIR}/${EPAGENT}/bin/EPACtrl.sh start"
	fi
}

stopEPAgent() {
	if `ps -fu apm | grep [j]ava >/dev/null`; then
		echo Introscope EPAgent is already running
		$SKIP su - apm -c "${INTROSCOPE_DIR}/${EPAGENT}/bin/EPACtrl.sh stop"
	else
		echo Introscope EPAgent is NOT running
	fi
}

runWebLogicScript() {
	cmdScript=${1}
	cmdName=${2}
	cmdOptions=${3}

	if [ ! -x $cmdScript ]; then
		echo Unable to exectute ${cmdScript}
		exit 1
	fi

	wlDomain=`echo ${cmdScript} | awk -F/ '{print $5}'`
	wlPort=`echo $wlDomain | awk '{print substr($1,4,2) substr($1,7,1) "00"}'`

	if `netstat -an | grep "$wlPort.*LISTEN" >/dev/null`; then
		echo ${wlDomain}: ${cmdName} is already running
	else
		echo ${wlDomain}: ${cmdName} is NOT running
		wlUser=${USERPREFIX}`echo ${wlDomain} | awk '{print substr($1,4,2)}'`
		$SKIP su - ${wlUser} -c "${cmdScript} ${cmdOptions}"
	fi
}

pauseWebLogic() {
	domain=$1
	stack=`echo ${domain} | awk '{print substr($1,4,2)}'`
	url_path=/health/setState.jsp=paused
	SKIP_SLEEP='true ||'

	# Show status instead of pausing server if skipping
	if [ -n ${SKIP:-''} ]; then
		url_path=/health/healthcheck.htm
	fi

	for host in `netstat -a | grep "${HOSTNAME}[.]${stack}[1-9]0[1-9] .* LISTEN" | \
			cut -f1 -d\ | tr '.' ':'| sort`; do
		java URLReader http://${host}${url_path}
		${SKIP} unset SKIP_SLEEP
	done
}

stopWebLogic() {
	domain=$1
	domainUser=${USERPREFIX}`echo ${domain} | awk '{print substr($1,4,2)}'`
	action=kill

	# Show process instead of killing process if skipping
	if [ -n ${SKIP:-''} ]; then
		action='ps -fp'
	fi

	for pid in `ps -fu ${domainUser} | awk '/java / {print $2}'`; do
		${action} ${pid} | tail -1
	done
}


doStartups() {
	# Start Introscope EP Agent - doesn't run in dev
	if [ -n ${EPAGENT:-''} -a ${USERPREFIX:-''} != dev ]; then
		startEPAgent
	fi

	# Start node managers
	if [ -n ${NODEMANAGERS:-''} -a -n ${DOMAIN:-''} ]; then
		for RUN_SCRIPT in /cpg/cpo_apps/${NODEMANAGERS}???/a????${DOMAIN}/bin/startNodeManager.sh; do
			runWebLogicScript ${RUN_SCRIPT} 'NodeManager' ''
		done
	fi

	# Start WebLogic admin servers - SOA servers start differently
	if [ -n ${ADMINSERVERS:-''} -a -n ${DOMAIN:-''} ]; then
		for RUN_SCRIPT in /cpg/cpo_apps/a[1-3]???/a????${DOMAIN}/bin/startWebLogic.sh; do
			runWebLogicScript ${RUN_SCRIPT} 'WebLogic AdminServer' '& disown'
		done
		#for SCRIPT in /cpg/cpo_apps/a[56]???/a????${DOMAIN}/bin/startWebLogic.sh; do
			#runWebLogicScript ${RUN_SCRIPT} 'WebLogic AdminServer'
		#done
	fi
}

doShutdowns() {
	# Start Introscope EP Agent - doesn't run in dev
	if [ -n ${EPAGENT:-''} -a ${USERPREFIX:-''} != dev ]; then
		$SKIP stopEPAgent
	fi

	# Stop WebLogic admin servers
	if [ -n ${ADMINSERVERS:-''} -a -n ${DOMAIN:-''} ]; then
		for DOMAIN_DIR in /cpg/cpo_apps/a[1-6]???; do
			stopWebLogic `echo ${DOMAIN_DIR} | awk -F/ '{print $NF}'`
		done
	fi

	# Stop WebLogic managed servers and node managers
	if [ -n ${NODEMANAGERS:-''} -a -n ${DOMAIN:-''} ]; then
		for DOMAIN_DIR in /cpg/cpo_apps/${NODEMANAGERS}???; do
			pauseWebLogic `echo ${DOMAIN_DIR} | awk -F/ '{print $NF}'`
		done

		$SKIP $SKIP_SLEEP sleep 45

		for DOMAIN_DIR in /cpg/cpo_apps/${NODEMANAGERS}???; do
			stopWebLogic `echo ${DOMAIN_DIR} | awk -F/ '{print $NF}'`
		done
	fi
}

doBackground() {
	if `id | grep uid=0 > /dev/null`; then
		logfile=/var/tmp/${SCRIPT_NAME}.$$
		/bin/tty &> ${logfile}.state
		echo >>  ${logfile}.state
		env >>  ${logfile}.state
		echo >>  ${logfile}.state
		set >>  ${logfile}.state
		${SCRIPT} background &> ${logfile} &
	else
		${SCRIPT} background
	fi
}

waitForResources() {
	echo ${CPG_HOSTNAME} ${USERPREFIX} `/bin/tty`
	for resource in ${DIRS}; do
		while ! df ${resource}; do
			sleep 5
		done
	done
}

removeScript() {
	rm -f /etc/init.d/${SCRIPT_NAME}
	rm -f /etc/rc?.d/[SK][0-9][0-9]${SCRIPT_NAME}
}

installScript() {
	if [ ${0} == /etc/init.d/${SCRIPT_NAME} ]; then
		echo FATAL: Cannot install from ${0}
	fi
	if [ -h ${0} ]; then
		echo FATAL: Cannot install from ${0}
	fi
	cp ${0} /etc/init.d/
	chmod 755 /etc/init.d/${SCRIPT_NAME}
	for level in 3; do
		ln -s -f /etc/init.d/${SCRIPT_NAME} /etc/rc${level}.d/S99${SCRIPT_NAME}
	done
	for level in 0 1 2 S; do
PP		ln -s -f /etc/init.d/${SCRIPT_NAME} /etc/rc${level}.d/K00${SCRIPT_NAME}
	done
}


#### Mainline

# Verify user prefix is valid
case ${USERPREFIX:-''} in
	dev|stg|prd)
		# OK - do nothing
		;;
	*)
		echo $0 is not intended to run on ${CPG_HOSTNAME} \(${HOSTNAME}\)
		exit 1;
		;;
esac

# Determine what to run for this stack
# Values:
#   ADMINSERVERS - non empty if WebLogic AdminServers should run on this server
#		This should only be set for one case (WebLogic Admin server zones)
#	NODEMANAGERS - application prefix for nodemanagers (matches 2 characters)
#   DOMAIN - domain suffix pattern for weblogic script path (matches 2 characters)
#		Required if either ADMINSERVERS or NODEMANAGERS is set
# 	EPAGENT	- epagent directory to run epagent startup script from
#       cpodeploy has a custom agent setup

case ${CPG_HOSTNAME:-''} in
	*-appadm)
		NODEMANAGERS='a[12]'
		DOMAIN=d9
		EPAGENT=epagent
		;;
	*-bdt)
		NODEMANAGERS=a2
		DOMAIN=d1
		EPAGENT=epagent
		;;
	*-blcpo)
		NODEMANAGERS=a1
		DOMAIN=d2
		EPAGENT=epagent
		;;
	*-cpodeploy)
		EPAGENT=epagent_cpodeploy
		;;
	*-soaz0)
		NODEMANAGERS=a5
		DOMAIN=d1
		EPAGENT=epagent
		;;
	*-soaz1)
		NODEMANAGERS=a6
		DOMAIN=d1
		EPAGENT=epagent
		;;
	*-uicpo)
		NODEMANAGERS=a1
		DOMAIN=d1
		EPAGENT=epagent
		;;
	*-wladm)
		ADMINSERVERS=true
		DOMAIN='d[129]'
		EPAGENT=epagent
		;;
	*-ws)
		NODEMANAGERS=a3
		DOMAIN=d1
		EPAGENT=epagent
		;;
	*)
		echo $0 is not intended to run on ${CPG_HOSTNAME} \(${HOSTNAME}\)
		exit 1;
		;;
esac

# Ignore commands if not running as root
if `id | grep -v uid=0 > /dev/null`; then
	SKIP='echo'
fi

# Perform selected action

case ${1} in
	start)
		doBackground
		;;
	background)
		waitForResources
		doStartups
		;;
	status)
		# Skip all startup commands
		SKIP='true ||'
		doStartups
		;;
	stop)
		doShutdowns
		;;
	install)
		installScript
		;;
	remove)
		removeScript
		;;
	*)
		echo
		echo "usage: $0 start|status|stop|install|remove"
		echo
		;;
esac

# EOF
