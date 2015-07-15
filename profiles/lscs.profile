# cpg.profile

VERSION=1.0

echo
echo '------------------------------------------------------------'
echo '                   Welcome to CPG Server'
echo "       Global lscl.profile (ver. ${VERSION}) for ${LOGNAME} ..."
echo '------------------------------------------------------------'
echo


#================================================
# Gobal Variables
#================================================
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
SVN_REPO=http://cposvn.innovapost.ca/configuration_repo/automation

#TERM=vt220; export TERM
VISUAL=vi

export SVN_REPO VISUAL

#================================================
# Default image umask is 0077
#================================================
umask 027

#### Default values

JAVA_VERSION=jdk1.7.0_80



#================================================
# NFS Mounts
#================================================
VAR_STACK=/cpg/cpo_var/${STACK}

JAVA_HOME=${INSTALL_DIR}/java/${JAVA_VERSION}

export VAR_STACK JAVA_HOME


#================================================
# System Shortcuts
#================================================
scripts=/cpg/3rdParty/scripts/lscs

export automation


#================================================
# Configure Paths
#================================================
# Force standard $PATH directory
PATH=
for DIR in ${JAVA_HOME}/bin ${WL_HOME}/common/bin /usr/bin /usr/sfw/bin \
		/usr/local/bin ${scripts} ${scripts%/*} /bin/opt/WANdisco/bin \
		/usr/openwin/bin /bin /usr/sbin /sbin; do
	if [[ -d ${DIR} && -r ${DIR} && ! -L ${DIR} ]]; then
		PATH=${PATH}:${DIR}
	fi
done
PATH=${PATH#:}

for DIR in /opt/WANdisco/lib; do
	if [ -d ${DIR} ]; then
		if [[ ! ":${LD_LIBRARY_PATH}:" =~ ":${DIR}:" ]]; then
			LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${DIR}
		fi
	fi
done
LD_LIBRARY_PATH=${LD_LIBRARY_PATH#:}

export LD_LIBRARY_PATH PATH
unset DIR FILE


#==================================================
# OS / Host - Determine CPG Hostname and Tier
#==================================================
CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map

if [ ! -f ${CPG_ALIAS_LOOKUP_FILE} ]; then
	echo
	echo 'ERROR in PROFILE:  CPG Hostname mapping file NOT found:'
	echo "                   ${CPG_ALIAS_LOOKUP_FILE}"
	echo
fi

CPG_HOSTNAME=$(egrep -i "^${HOSTNAME}," ${CPG_ALIAS_LOOKUP_FILE})
CPG_HOSTNAME_COUNT=$(echo ${CPG_HOSTNAME} | fgrep ',' | wc -l)

if [ ${CPG_HOSTNAME_COUNT} -gt 1 ]; then
	echo
	echo 'ERROR in PROFILE:  Found more than 1 match of HOSTNAME in'
	echo "  ${CPG_ALIAS_LOOKUP_FILE}"
	echo
else
	CPG_HOSTNAME=$(echo ${CPG_HOSTNAME} | cut -d, -f2)
fi

export CPG_HOSTNAME
unset CPG_HOSTNAME_COUNT CPG_ALIAS_LOOKUP_FILE DASH_COUNT


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

memuse() {
	memory=($(/usr/sbin/swap -s | tr -d -c '0123456789 '))
	echo Memory utilization: $(( ${memory[2]} * 100 / \
		(  ${memory[2]} +  ${memory[3]} ) ))%
}

# Make wget work with HTTPS connections
alias wget='\wget --no-check-certificate'



#==================================================
# Show settings
#==================================================
echo "    HOSTNAME = ${CPG_HOSTNAME}"
echo "    USERNAME = ${OS_USERNAME}"
echo
echo "   JAVA_HOME = ${JAVA_HOME}"
echo
echo "        PATH = ${PATH}"
echo
echo "      MEMORY = $(memuse | cut -d\  -f3)"
echo
echo '------------------------------------------------------------'
echo

unset OS_USERNAME


# EOF
