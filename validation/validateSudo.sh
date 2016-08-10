#! /usr/bin/bash
#set -x

# Config parameters
SCRIPT_NAME=$(basename ${0})

INTROSCOPE_DIR=/cpg/3rdParty/installs/introscope/9.7.1.0
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles

CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
export CPG_HOSTNAME=$(egrep -i "^$(hostname)," \
	${CPG_ALIAS_LOOKUP_FILE} | cut -d, -f2)

USERPREFIX=${CPG_HOSTNAME%%-*}



#### Function definitions

startEPAgent() {
	if $(ps -fu apm | grep [j]ava >/dev/null); then
		echo Introscope EPAgent is already running
	else
		echo Introscope EPAgent is NOT running
		$SKIP su - apm -c "${INTROSCOPE_DIR}/${EPAGENT}/bin/EPACtrl.sh start"
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

	wlDomain=${cmdScript%/bin*}
	wlDomain=${wlDomain##*/}
	wlPort=${wlDomain:3:2}${wlDomain:6:1}00

	if $(netstat -an | grep "$wlPort.*LISTEN" >/dev/null); then
		echo ${wlDomain}: ${cmdName} is already running
	else
		echo ${wlDomain}: ${cmdName} is NOT running
		wlUser=${USERPREFIX}${wlDomain:3:2}
		$SKIP su - ${wlUser} -c "${cmdScript} ${cmdOptions}"
	fi
}

doStartups() {
	# Silently ignore commands if not running as root
	if [[ ! $(id) =~ uid=0\(root\) ]]; then
		SKIP='true ||'
	fi

	# Start Introscope EP Agent - doesn't run in dev
	if [[ -n ${EPAGENT} && ${USERPREFIX} != dev ]]; then
		startEPAgent
	fi

	# Start node managers
	if [[ -n ${NODEMANAGERS} && -n ${DOMAIN} ]]; then
		for SCRIPT in /cpg/cpo_apps/${NODEMANAGERS}???/a????${DOMAIN}/bin/startNodeManager.sh; do
			runWebLogicScript ${SCRIPT} 'NodeManager' ''
		done
	fi

	# Start WebLogic admin servers - SOA servers start differently s
	if [[ -n ${ADMINSERVERS} && -n ${DOMAIN} ]]; then
		for SCRIPT in /cpg/cpo_apps/a[1-3]???/a????${DOMAIN}/bin/startWebLogic.sh; do
			runWebLogicScript ${SCRIPT} 'WebLogic AdminServer' '& disown'
		done
		#for SCRIPT in /cpg/cpo_apps/a[56]???/a????${DOMAIN}/bin/startWebLogic.sh; do
			#runWebLogicScript ${SCRIPT} 'WebLogic AdminServer'
		#done
	fi
}

removeScript() {
	rm -f /etc/init.d/${SCRIPT_NAME}
	rm -f /etc/rc?.d/[SK][0-9][0-9]${SCRIPT_NAME}
}

installScript() {
	cp ${0} /etc/init.d/${SCRIPT_NAME}
	for x in 3; do
		ln /etc/init.d/${SCRIPT_NAME} /etc/rc${x}.d/S99${SCRIPT_NAME}
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

# Perform selected action

case ${1} in
	start)
		doStartups
		;;
	status)
		# Skip all startup commands
		SKIP='true ||'
		doStartups
		;;
	stop)	# noop
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
