# cpg.profile

VERSION='$Revision$'
VERSION=$(echo ${VERSION} | awk '{print $2}')

if [[ $0 =~ bash ]]; then
	echo
	echo '------------------------------------------------------------'
	echo '                   Welcome to CPG Server'
	echo "       Global cpg.profile (rev: ${VERSION}) for ${LOGNAME} ..."
	echo '------------------------------------------------------------'
	echo
fi


#================================================
# Gobal Variables
#================================================
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
PROJECT_NAME=USER
STACK=a1l10
SVN_REPO=http://cposvn.cpggpc.ca/configuration_repo/automation

VISUAL=vi

export PROJECT_NAME STACK SVN_REPO VISUAL

alias wlps="/usr/ucb/ps -axww | grep [w]eblogic."

#================================================
# Default image umask is 0077
#================================================
umask 027

#================================================
# OS / User - Automatically Determine
#================================================
if [ -z ${CPG_USER} ]; then
	OS_USERNAME=${LOGNAME}
else
	OS_USERNAME=${CPG_USER}
fi
STACK_NUM=''

case "${OS_USERNAME:0:3}" in
	prd)
		ENVIRONMENT=prd
		STACK_NUM=${OS_USERNAME:3:2}
		ENVIRONMENT_SHORT=p
		STACKUSER=true
		;;
	stg)
		ENVIRONMENT=stg
		STACK_NUM=${OS_USERNAME:3:2}
		ENVIRONMENT_SHORT=s
		STACKUSER=true
		;;
	dev)
		ENVIRONMENT=dev
		STACK_NUM=${OS_USERNAME:3:2}
		ENVIRONMENT_SHORT=d
		STACKUSER=true
		;;
	*)
		STACKUSER=false
		;;
esac
export ENVIRONMENT STACKUSER

#### Default values - may be overriden; DSS project overrides these

JAVA_VERSION=jdk1.7.0_121
JAVA_VENDOR=Sun

MW_DIR=Middleware_Home1
WL_DIR=wlserver_10.3

##### Overrides by userid
# Should be able to use new versions for these in most cases

#case "${OS_USERNAME}" in
	#dev[23]3|stg--)
	#    JAVA_VERSION=jdk1.7.0_65
	#    MW_DIR=Middleware_Home
	#    ;;
#esac


#### Overrides by Project

LOB=${STACK_NUM:0:1}
domains='1'
case $LOB in
	1)  PROJECT_NAME=CPO
		domains='1 2 9';;
	2)  PROJECT_NAME=BDT
		domains='1 9';;
	3)  PROJECT_NAME=WS;;
	5)  PROJECT_NAME=CPC-SOA
		MW_DIR=fmw50
		WL_DIR=Oracle_SOA1
		;;
	6)  PROJECT_NAME=PULSE
		MW_DIR=fmw60
		WL_DIR=Oracle_SOA1
		;;
	*)  ;;
esac

if [ "${STACKUSER}" == 'true' ]; then
	STACK=a${LOB}${ENVIRONMENT_SHORT}${STACK_NUM}
fi

unset LOB ENVIRONMENT_SHORT STACK_NUM


#================================================
# NFS Mounts
#================================================
APPS_MOUNT=/cpg/cpo_apps
APP_STACK=/cpg/cpo_apps/${STACK}

VAR_MOUNT=/cpg/cpo_var
VAR_STACK=/cpg/cpo_var/${STACK}

CONTENT_DIR=/cpg/content

INSTALL_DIR=/cpg/3rdParty/installs
SQLPLUS_HOME=${INSTALL_DIR}/Oracle/instantclient_12_1

SAPJCO_HOME=${INSTALL_DIR}/SAP/sapjco-sun_64-2.1.10
SAPSEC_HOME=${INSTALL_DIR}/SAP/sap-security-utils

export APP_STACK VAR_STACK CONTENT_DIR INSTALL_DIR JAVA_VENDOR
export SQLPLUS_HOME SAPJCO_HOME SAPSEC_HOME



#================================================
# System Shortcuts
#================================================
scripts=/cpg/3rdParty/scripts/cpg

if [ "${STACKUSER}" == 'true' ]; then
	# Handle setup case
	automation=${APP_STACK}/automation
	#Loop through existing domains and export shorthand links
	for domain in ${domains}; do
		eval d${domain}=${APP_STACK}/${STACK}d${domain}
		eval d${domain}logs=${VAR_STACK}/${STACK}d${domain}
		eval d${domain}scripts=${APP_STACK}/${STACK}d${domain}/automation
		export d${domain} d${domain}logs d${domain}scripts
	done
fi

export automation scripts
unset domain domains


#================================================
# Set WL_HOME and JAVA_HOME from automation directory - if available
#================================================
JAVA_HOME=${INSTALL_DIR}/java/${JAVA_VERSION}
WL_HOME=${INSTALL_DIR}/Oracle/${MW_DIR}/${WL_DIR}

if [ -f ${d1scripts}/stacks/${STACK}/*d1/Domain.properties ]; then
	eval $(egrep '^(jdk|bea)Path *=' \
		${d1scripts}/stacks/${STACK}/*d1/Domain.properties | tr -d ' ')
fi

if [[ "${JAVA_HOME}" != "${jdkPath}" \
&& -f "${jdkPath:-/XXX}/bin/java" ]]; then
	case $(uname -s) in
	SunOS)
		echo Setting JAVA_HOME from Domain.properties
		JAVA_HOME=${ROOT_PREFIX}${jdkPath}
		;;
	*)
		if [[ -z ${JAVA_HOME} ]]; then
			echo JAVA_HOME not set
		else
			JAVA_HOME is ${JAVA_HOME}
		fi
		;;
	esac
fi
if [[ "${WL_HOME}" != "${beaPath}/${WL_DIR}" \
&& -f "${beaPath}/${WL_DIR}/server/lib/weblogic.jar" ]]; then
	echo Setting WL_HOME from Domain.properties
	echo
	WL_HOME=${ROOT_PREFIX}${beaPath}/${WL_DIR}
fi

export JAVA_HOME WL_HOME
unset JAVA_VERSION MW_DIR WL_DIR


#================================================
# Configure Paths
#================================================
# Force standard $PATH directory
PATH=
for DIR in ${JAVA_HOME}/bin ${WL_HOME}/common/bin /usr/bin /usr/sfw/bin \
		/usr/local/bin ${scripts} ${scripts%/*}/bin /opt/WANdisco/bin \
		/usr/openwin/bin /bin /usr/sbin /sbin ${SQLPLUS_HOME} ${lscripts}; do
	if [[ -d ${DIR} && -r ${DIR} && ! -L ${DIR} ]]; then
		PATH=${PATH}:${DIR}
	fi
done
PATH=${PATH#:}

#CLASSPATH=$WL_HOME/server/lib/weblogic.jar:$CLASSPATH
for FILE in ${WL_HOME}/server/lib/weblogic.jar; do
	if [ -e ${FILE} ]; then
		if [[ ! "${CLASSPATH}:" == "${FILE}:"* ]]; then
			CLASSPATH=${FILE}:${CLASSPATH%:}
		fi
	fi
done
CLASSPATH=${CLASSPATH%:}:/cpg/3rdParty/scripts/cpg/testing

for DIR in /opt/WANdisco/lib ${SQLPLUS_HOME} ${SAPJCO_HOME} ${SAPSEC_HOME}; do
	if [ -d ${DIR} ]; then
		if [[ ! ":${LD_LIBRARY_PATH}:" =~ ":${DIR}:" ]]; then
			LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${DIR}
		fi
	fi
done
LD_LIBRARY_PATH=${LD_LIBRARY_PATH#:}

export CLASSPATH LD_LIBRARY_PATH PATH
unset DIR FILE


#================================================
# Default ulimit
#================================================
ULIMIT=`ulimit -H -n`
if [ $ULIMIT == 'unlimited' ]; then
	echo NOTE: Setting ulimit to 65535 due to an unlimited setting
	ulimit -Hn 65535
fi


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

CPG_TIER=None

if [ ${CPG_HOSTNAME_COUNT} -gt 1 ]; then
	echo
	echo 'ERROR in PROFILE:  Found more than 1 match of HOSTNAME in'
	echo "  ${CPG_ALIAS_LOOKUP_FILE}"
	echo
else
	CPG_HOSTNAME=$(echo ${CPG_HOSTNAME} | cut -d, -f2)
	CPG_TIER=${CPG_HOSTNAME##*-}
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
	local memory=($(/usr/sbin/swap -s | tr -d -c '0123456789 '))
	echo Memory utilization: $(( ${memory[2]} * 100 / \
		(  ${memory[2]} +  ${memory[3]} ) ))%
}

swapuse() {
	swap -l | \
	awk '$NF ~ /^[0-9]+$/ { blocks = blocks + $(NF-1); free = free + $NF; }
		END { print "Swap utilization:", int((blocks-free+1024)/2048), "MB" }'
}


if [[ "${STACKUSER}" != 'true' || -n "${CPG_USER}" ]]; then
	use() {
		case "${1}" in
		dev??|stg??|prd??)
			if [ -d /export/home/${1} ]; then
				CPG_USER=$1 source ${PROFILE_DIR}/cpg.profile
			else
				echo "User ${1} is not available on this system"
			fi
			;;
		*)
			echo 'Usage: use dev##|stg##|prd##'
			;;
		esac
	}
fi

# Make wget work with HTTPS connections
alias wget='\wget --no-check-certificate'

# Fix timezones for some databases - Temporary ??
alias java='java -Doracle.jdbc.timezoneAsRegion=false'

# Fix for WLST - Configure custom trust path.
export WLST_PROPERTIES="-Dweblogic.security.TrustKeyStore=CustomTrust
-Dweblogic.security.CustomTrustKeyStoreFileName=/cpg/3rdParty/security/CPGTrust.jks"


#==================================================
# Show settings
#==================================================
if [[ $0 =~ bash ]]; then
	echo "    HOSTNAME = ${CPG_HOSTNAME}"
	echo "    USERNAME = ${OS_USERNAME}"
	if [ "${PROJECT_NAME}" != 'USER' ]; then
		echo "     PROJECT = ${PROJECT_NAME}"
		echo "        TIER = ${CPG_TIER}"
		echo "   APP_STACK = ${APP_STACK}"
		echo "   VAR_STACK = ${VAR_STACK}"
	fi
	echo
	echo "   JAVA_HOME = ${JAVA_HOME}"
	echo "     WL_HOME = ${WL_HOME}"
	echo
	echo "        PATH = ${PATH}"
	echo "   CLASSPATH = ${CLASSPATH}"
	echo
	echo "      MEMORY = $(memuse | cut -d\  -f3)"
	echo "        SWAP = $(swapuse | cut -d\  -f3-)"
	echo
	echo '------------------------------------------------------------'
	echo
fi

unset OS_USERNAME STACKNUM CPG_TIER


#==================================================
# Verify status of the automation directory
#==================================================
if [[ ${STACKUSER} == true && -z ${CPG_USER} && ${CPG_HOSTNAME} = ???-cpodeploy ]]; then
	if [ -d ${APP_STACK}/automation ]; then
		# Temporarily doing svn locate on update failure
		svn update ${automation} || ( svn --non-interactive --password '' \
			relocate http://cposvn.innovapost.ca \
					 http://cposvn.cpggpc.ca ${automation} ; \
			svn update ${automation} )
		svn status ${automation}
	else
		svn co ${SVN_REPO}/trunk/secure ${automation}
	fi
fi


# EOF
