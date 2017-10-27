#!/usr/bin/bash

INSTALL_BASE=/usr/local
SOURCE_BASE=/cpg/3rdParty/scripts/cpg/bart
BART_MANIFESTS=/var/tmp

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
	elif ! diff -q ${1} ${2} >/dev/null; then
		echo Updating: ${2}
		cp ${2}{,.$(date +%Y%m%dT%H%M)}
		cp ${3} ${1} ${2}
		return 0
	fi
	return 1
}


# Function to update or install files only if missing or changed
installFiles() {
}


# Define the rules file to apply; check for unsupported server
rules_file=bart.rules
case ${CPG_HOSTNAME:-''} in
        *-appadm)
                ;;
        *-bdt)
                ;;
        *-blcpo)
                 ;;
        *-cpodeploy)
        		rules_file=bart.rules.cpodeploy
                ;;
#        *-soaz0)
#                ;;
#        *-soaz1)
#                ;;
        *-uicpo)
                ;;
        *-wladm)
                ;;
        *-ws)
                ;;
        *)
        		echo Unknown host ${HOSTNAME} ${CPG_HOSTNAME}
        		exit 99
        		;;
esac


# Install the files
updateChanged ${SOURCE_BASE}/${1} ${INSTALL_BASE}/etc/bart.rules
updateChanged ${SOURCE_BASE}/${1} ${INSTALL_BASE}/sbin/bartlog


# Remove script from bin if found
if [ -f ${INSTALL_BASE}/bin/bartlog ]; then
	rm ${INSTALL_BASE}/bin/bartlog
fi


# Do initial run if required
if [ ! -f $BART_MANIFESTS/bart.manifest.0 ]; then
	${INSTALL_BASE}/sbin/bartlog &
fi


# EOF
