#!/usr/bin/bash
# Install bart onto the system from the script's directory

INSTALL_BASE=/usr/local
SOURCE_BASE=$(dirname ${0})
BART_MANIFEST=/var/tmp/bart_manifest_$(hostname).0
SNF_MANIFEST=bartlog.xml

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


if [[ ! -f /var/svc/manifest/site/${SMF_MANIFEST} ]]; then
	updateChanged ${SOURCE_BASE}/${SMF_MANIFEST} /var/svc/manifest/site/${SMF_MANIFEST}
	svccfg import /var/svc/manifest/site/${SMF_MANIFEST}
elif updateChanged ${SOURCE_BASE}/${SMF_MANIFEST} /var/svc/manifest/site/${SMF_MANIFEST}; then
	svccfg import /var/svc/manifest/site/${SMF_MANIFEST}
fi


# Do initial run if required in background - disown process
if [ ! -f $BART_MANIFEST; then
	${INSTALL_BASE}/sbin/bartlog &
	disown
fi


# EOF	:indentSize=4:tabSize=4:noTabs=false:mode=bash:
