#!/usr/bin/bash
# Install bart onto the system from the script's directory

INSTALL_BASE=/usr/local
SOURCE_BASE=$(dirname ${0})
BART_MANIFESTS=/var/tmp

PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
CPG_HOSTNAME=$(egrep -i "^$(hostname)," ${CPG_ALIAS_LOOKUP_FILE})
export CPG_HOSTNAME=${CPG_HOSTNAME##*,}


# Function to update or install configs only if missing or changed
#    Params: source destination [cp_options]
updateChanged() {
	if [ ! -f ${1} ]; then
		echo FATAL: Source file ${1} is missing
		exit 1
	elif [ ! -f ${2} ]; then
		echo Installing: ${2}
		cp ${3} ${1} ${2}
		return 0
	elif ! diff ${1} ${2} &>/dev/null; then
		echo Updating: ${2}
		#cp ${2}{,.$(date +%Y%m%dT%H%M)}
		rm -f ${2}.$(date +%Y)*
		cp ${3} ${1} ${2}
		return 0
	fi
	return 1
}


# Define the rules file to apply; check for unsupported server
rules_file=bart.rules.full
case ${CPG_HOSTNAME:-'unknown'} in
	*-appadm)
		rules_file=bart.rules.local
		;;
	*-bdt)
		rules_file=bart.rules.local
		;;
	*-blcpo)
		rules_file=bart.rules.local
		 ;;
	*-cpodeploy)
		rules_file=bart.rules.cpodeploy
		;;
	*-soaz0)
		rules_file=bart.rules.full
		;;
	*-soaz1)
		rules_file=bart.rules.full
		;;
	*-uicpo)
		rules_file=bart.rules.local
		;;
	*-wladm)
		rules_file=bart.rules.weblogic
		;;
	*-ws)
		rules_file=bart.rules.local
		;;
	unknown)
		rules_file=bart.rules.full
		;;
	*)
		echo Unknown host ${HOSTNAME} ${CPG_HOSTNAME}
		exit 99
		;;
esac


# Install the files
updateChanged ${SOURCE_BASE}/${rules_file} ${INSTALL_BASE}/etc/bart.rules
updateChanged ${SOURCE_BASE}/bartlog ${INSTALL_BASE}/sbin/bartlog
updateChanged ${SOURCE_BASE}/bartMail.py ${INSTALL_BASE}/sbin/bartMail.py


# Choose the manifest based on Solaris version
if [[ $(uname -r) == '5.11' ]]; then # Run bartlog on abn SMF schedule
	MANIFEST=bartlog.xml
else	# Need to wait for run times.
	MANIFEST=bart_runner.xml
fi

if [[ $(uname -r) == '5.11' ]]; then # Solaris 11
	if [[ ! -f /var/svc/manifest/site/${MANIFEST} ]]; then
		updateChanged ${SOURCE_BASE}/${MANIFEST} /var/svc/manifest/site/${MANIFEST}
		svccfg apply site:${MANIFEST}
	elif updateChanged ${SOURCE_BASE}/${MANIFEST} /var/svc/manifest/site/${MANIFEST}; then
		svccfg refresh site:${MANIFEST}
	fi
else	# Solaris 10
	if [[ ! -f /var/svc/manifest/site/${MANIFEST} ]]; then
		updateChanged ${SOURCE_BASE}/${MANIFEST} /var/svc/manifest/site/${MANIFEST}
		svccfg import /var/svc/manifest/site/${MANIFEST}
		svcadm start  site:${MANIFEST}
	elif updateChanged ${SOURCE_BASE}/bart_runner.xml /var/svc/manifest/site/bart_runner.xml; then
		svcadm restart  site:${MANIFEST}
	fi
fi


# Do initial run if required
if [ ! -f $BART_MANIFESTS/bart.manifest.0 ]; then
	${INSTALL_BASE}/sbin/bartlog &
fi


# EOF	:indentSize=4:tabSize=4:noTabs=false:mode=bash:
