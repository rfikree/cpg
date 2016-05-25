# cpg.profile

VERSION='$Rev: $'
VERSION=$(echo ${VERSION} | tr - '$')

if [[ $0 =~ bash ]]; then
	echo
	echo '------------------------------------------------------------'
	echo '                   Welcome to CPG Server'
	echo "       Global lscl.profile (${VERSION}) for ${LOGNAME} ..."
	echo '------------------------------------------------------------'
	echo
fi

unset VERSION


#================================================
# Gobal Variables
#================================================
INSTALL_DIR=/cpg/3rdParty/installs
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
export SVN_REPO=http://cposvn.cpggpc.ca/configuration_repo/automation
export VISUAL=vi


#================================================
# Default image umask is 0077
#================================================
umask 027


#================================================
# Configure JAVA
#================================================
case $(uname -s) in
SunOS)
	JAVA_VERSION=jdk1.7.0_80
	export JAVA_HOME=${INSTALL_DIR}/java/${JAVA_VERSION}
	;;
Linux)
	JAVA_HOME=$(readlink /usr/java/latest)
	if [[ -n ${JAVA_HOME} ]]; then
		echo JAVA_HOME is ${JAVA_HOME}
	else
		echo JAVA_HOME not set
	fi
	;;
*)
	echo JAVA_HOME: unsupported OS $(uname -s)
	;;
esac

#==================================================
# OS / Host - Determine CPG Hostname and Tier
#==================================================
CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map

if [ ! -f ${CPG_ALIAS_LOOKUP_FILE} ]; then
	if [[ $0 =~ bash ]]; then
		echo
		echo 'ERROR in PROFILE:  CPG Hostname mapping file NOT found:'
		echo "                   ${CPG_ALIAS_LOOKUP_FILE}"
		echo
	fi
fi

export CPG_HOSTNAME=$(egrep -i "^${HOSTNAME}," ${CPG_ALIAS_LOOKUP_FILE})
CPG_HOSTNAME_COUNT=$(echo ${CPG_HOSTNAME} | fgrep ',' | wc -l)

if [ ${CPG_HOSTNAME_COUNT} -gt 1 ]; then
	CPG_HOSTNAME=${HOSTNAME}
	if [[ $0 =~ -bash ]]; then
		echo
		echo 'ERROR in PROFILE:  Found more than 1 match of HOSTNAME in'
		echo "  ${CPG_ALIAS_LOOKUP_FILE}"
		echo
	fi
else
	CPG_HOSTNAME=$(echo ${CPG_HOSTNAME} | cut -d, -f2)
fi

unset CPG_HOSTNAME_COUNT CPG_ALIAS_LOOKUP_FILE DASH_COUNT


#================================================
# System Shortcuts
#================================================
export lscripts=/cpg/3rdParty/scripts/lscs
export scripts=/cpg/3rdParty/scripts/cpg

export odlogs=/cpg/cpo_var/${CPG_HOSTNAME}/interwvn
export odhome=/cpg/interwoven/OpenDeployNG

# Really don't need *lscc001 subdirectories - need to fix install scripts
if [[ ${LOGNAME} =~ s00* ]]; then
	export logs=/cpg/cpo_var/${CPG_HOSTNAME}/${LOGNAME}/${LOGNAME}lscs001
	export stack=/cpg/stacks/${LOGNAME}/${LOGNAME}lscs001
fi



#================================================
# Configure Paths
#================================================
# Force standard $PATH directory
PATH=
for DIR in ${JAVA_HOME}/bin ${WL_HOME}/common/bin /usr/bin /usr/sfw/bin \
		/usr/local/bin ${lscripts} /bin/opt/WANdisco/bin \
		/usr/openwin/bin /bin /usr/sbin /sbin; do
	if [[ -d ${DIR} && -r ${DIR} && ! -L ${DIR} ]]; then
		PATH=${PATH}:${DIR}
	fi
done
export PATH=${PATH#:}

for DIR in /opt/WANdisco/lib; do
	if [ -d ${DIR} ]; then
		if [[ ! ":${LD_LIBRARY_PATH}:" =~ ":${DIR}:" ]]; then
			LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${DIR}
		fi
	fi
done
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH#:}

unset DIR FILE


#==================================================
# User setup
#==================================================
# Set prompt
if [ "${CPG_HOSTNAME}" != "${HOSTNAME}" ]; then
	PS1="${LOGNAME}@${CPG_HOSTNAME} (${HOSTNAME}) \w\n> "
else
	PS1="${LOGNAME}@${CPG_HOSTNAME} \w\n> "
fi
export PS1

# Make wget work with HTTPS connections
alias wget='\wget --no-check-certificate'



#==================================================
# Show settings
#==================================================
if [[ $0 =~ bash ]]; then
	echo "    HOSTNAME = ${CPG_HOSTNAME}"
	echo "    USERNAME = ${LOGNAME}"
	echo
	echo "   JAVA_HOME = ${JAVA_HOME}"
	echo
	echo "        PATH = ${PATH}"
	echo
	echo '------------------------------------------------------------'
	echo
fi

unset OS_USERNAME INSTALL_DIR PROFILE_DIR


# EOF
