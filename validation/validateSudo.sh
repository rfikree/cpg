#! /bin/bash
#set -x

# Config parameters

PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles

CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
export CPG_HOSTNAME=$(egrep -i "^$(hostname)," \
	${CPG_ALIAS_LOOKUP_FILE} | cut -d, -f2)

LS_SUFFIX=${CPG_HOSTNAME:0:1}
WL_PREFIX=${CPG_HOSTNAME%%-*}
WL_EXCLUSIONS='prd(13|35)'

EXTRA_USERS=
LS_USERS=
WL_USERS=


#### Function definitions

getWebLogicUsers() {
	WL_USERS=$(getent passwd | grep ^${WL_PREFIX}${1:-[0-9]}[0-9]: |
				cut -d: -f1 | egrep -v "${WL_EXCLUSIONS}" | sort)

}
getLSusers(){
	LS_USERS=$(getent passwd | grep ^s00[0-9]${LS_SUFFIX}: |
						cut -d: -f1 | sort)
	LS_USERS="interwvn lscsadm ${LS_USERS}"
}

validateAccess() {
	if ! sudo -u ${1} echo ${1} works; then
		echo ${1} fails
		sleep 5
	fi
}

validateUsers() {
	for user in ${EXTRA_USERS} ${LS_USERS} ${WL_USERS}; do
		validateAccess ${user}
	done
}


#### Mainline

# Verify user prefix is valid
case ${WL_PREFIX:-''} in
	dev|stg|prd)
		# OK - do nothing
		;;
	*)
		echo $0 is not intended to run on ${CPG_HOSTNAME} \(${HOSTNAME}\)
		exit 1;
		;;
esac

# Build user list for this stack
# Values:
#	LS_USERS - LiveSite users for this host
#   WL_USERS - WebLogic users for this host

case ${CPG_HOSTNAME##*-} in
	appadm|bdt|blcpo|uicpo|ws)
		if [[ ${WL_PREFIX} != dev ]]; then
			EXTRA_USERS='apm'
		fi
		getWebLogicUsers '[1-3]'
		;;

	cpodeploy)
		EXTRA_USERS='interwvn optadm'
		if [[ ${WL_PREFIX} != dev ]]; then
			EXTRA_USERS="apm ${EXTRA_USERS}"
		fi
		getWebLogicUsers '[1-6]'
		;;
	wladm)
		if [[ ${WL_PREFIX} != dev ]]; then
			EXTRA_USERS='apm'
		fi
		getWebLogicUsers '[1-6]'
		;;
	soaz[01])
		if [[ ${WL_PREFIX} != dev ]]; then
			EXTRA_USERS='apm'
		fi
		getWebLogicUsers '[5-6]'
		;;
	lscs)
		getLSusers
		;;
	*)
		echo $0 is not intended to run on ${CPG_HOSTNAME} \(${HOSTNAME}\)
		exit 1;
		;;
esac


# Update credentials - prompting for password if required
sudo -v
echo

# Perform the validations
validateUsers
echo

# List access
sudo -l
echo

# EOF
