# cpg.profile

VERSION='$Revision$'
VERSION=$(echo ${VERSION} | awk '{print $2}')

if tty -s; then
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
INSTALL_DIR=/cpg/3rdParty/installs
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
PROJECT_NAME=USER
SVN_REPO=http://cposvn.cpggpc.ca/configuration_repo/automation
DERBY_FLAG=false
VISUAL=vi

export PROJECT_NAME SVN_REPO VISUAL DERBY_FLAG

#================================================
# Default image umask is 0077
#================================================
umask 027

#================================================
# OS / User - Automatically Determine
#================================================
if [ -z ${CPG_LOGNAME} ]; then
    if [ -z ${CPG_USER} ]; then
        CPG_LOGNAME=${LOGNAME}
    else
        CPG_LOGNAME=${CPG_USER}
    fi
fi

case "${CPG_LOGNAME:0:3}" in
    dev|loc|stg|prd)
        ENVIRONMENT=${CPG_LOGNAME:0:3}
        STACK_NUM=${CPG_LOGNAME:3:2}
        ENVIRONMENT_SHORT=${CPG_LOGNAME:0:1}
        STACKUSER=true
        STACK=a${STACK_NUM:0:1}${ENVIRONMENT_SHORT}${STACK_NUM}
        ;;
    *)
        ENVIRONMENT=loc
        STACK_NUM=10
        ENVIRONMENT_SHORT=l
        STACKUSER=false
        STACK=a1l10
        CPG_LOGNAME=loc10
        ;;
esac
export ENVIRONMENT STACKUSER CPG_LOGNAME STACK


#### Configuration by Project

domains='1'
case ${STACK_NUM:0:1} in
    1)  PROJECT_NAME=CPO
        domains='1 2';;
    5)  PROJECT_NAME=CPC-SOA
        MW_DIR=fmw${STACK_NUM}
        ;;
    6)  PROJECT_NAME=PULSE
        MW_DIR=fmw${STACK_NUM}
        ;;
    *)  ;;
esac
unset ENVIRONMENT_SHORT STACK_NUM


#### Default values - may be overriden;

JAVA_BASE=${INSTALL_DIR}/java
[[ $(uname) == Linux ]] && JAVA_BASE=/usr/java
[[ $(uname -v) =~ Ubuntu ]] && JAVA_BASE=/usr/lib/jvm

for JAVA_VERSION in $(ls -drt ${JAVA_BASE}/jdk1.7* 2>/dev/null); do
    if [ -d ${JAVA_VERSION} ]; then
        JAVA_HOME=${JAVA_VERSION}
    else
        echo ${JAVA_VERSION} is invalid
    fi
done
if [[ $(uname) == Linux || -z ${JAVA_VERSION} ]]; then
    JAVA7_VERSION=${JAVA_VERSION:-''}
    for JAVA_VERSION in $(ls -drt ${JAVA_BASE}/jdk1.8*); do
        if [ -d "${JAVA_VERSION}" ]; then
            JAVA_HOME=${JAVA_VERSION}
        else
            echo ${JAVA_VERSION} is invalid
        fi
    done
fi
export JAVA_HOME=${JAVA_HOME}
JAVA_VENDOR=Sun

if [[ -z ${JAVA_VERSION} ]]; then
    JAVA_VERSION=$(readlink -f /usr/bin/java)
    JAVA_VERSION=${JAVA_VERSION%/jre/bin/java}
    if [[ -n ${JAVA_VERSION} ]]; then
        echo JAVA_VERSION is ${JAVA_VERSION}
    else
        echo JAVA_VERSION not set
    fi
fi


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

if [[ -n ${STACK} ]]; then
    # Handle setup case
    automation=${APP_STACK}/automation
    #Loop through existing domains and export shorthand links
    for domain in ${domains}; do
        eval d${domain}=${APP_STACK}/${STACK}d${domain}
        eval d${domain}logs=${VAR_STACK}/${STACK}d${domain}
        eval d${domain}scripts=${APP_STACK}/${STACK}d${domain}/automation
        export d${domain} d${domain}logs d${domain}scripts
    done
    PYTHONPATH=${automation}/secure
fi

export automation scripts PYTHONPATH
unset domain domains


#================================================
# Set WL_HOME and JAVA_HOME from automation directory - if available
#================================================
if [ -f ${automation}/stacks/${STACK}/*d1/Domain.properties ]; then
    eval $(egrep '^(jdk|bea)(Path|Ver) *=' \
        ${automation}/stacks/${STACK}/*d1/Domain.properties | tr -d ' ')
fi
JAVA_HOME2=${jdkPath}

if [ -d ${beaPath:-''} ]; then
    BEA_HOME=${beaPath}
else
    BEA_HOME=${INSTALL_DIR}/Oracle/${MW_DIR}
fi


WL_HOME=$(echo ${BEA_HOME}/wlserver*)
ORACLE_HOME=${BEA_HOME}/oracle_common
[ -d ${ORACLE_HOME:-''} ] || unset ORACLE_HOME
SOA_ORACLE_HOME=${BEA_HOME}/soa
# */soa is WebLogic 12c; Oracle_SOA1 is WebLogic 10
[ -d ${SOA_ORACLE_HOME:-''} ] || SOA_ORACLE_HOME=${BEA_HOME}/Oracle_SOA1
[ -d ${SOA_ORACLE_HOME:-''} ] || unset SOA_ORACLE_HOME

# Temporary fix while switching to Java 8
if [[ $(uname -s) = Linux \
&& ${JAVA7_VERSION} =~ ${jdkVer:-xx} ]]; then
    JAVA_VERSION=${JAVA7_VERSION}
fi

if [[ ${JAVA_HOME} != ${jdkPath} \
&& -f ${jdkPath:-/XXX}/bin/java ]]; then
    if [[ $(uname) = SunOS ]]; then
        echo Setting JAVA_HOME from Domain.properties
        JAVA_HOME=${jdkPath}
        JAVA_VERSION=${jdkPath}
    elif [[ $(uname) = Linux ]]; then
        JAVA_HOME=${JAVA_VERSION}
    fi
fi
if [[ -z ${JAVA_HOME} ]]; then
    echo JAVA_HOME not set
fi


export JAVA_HOME WL_HOME BEA_HOME ORACLE_HOME JAVA_HOME2
unset MW_DIR jdkPath beaPath jdkVer JAVA7_VERSION


#================================================
# Configure Paths
#================================================
# Force standard $PATH directory
PATH=
for DIR in ${JAVA_VERSION}/bin /usr/xpg6/bin /usr/xpg4/bin /usr/bin \
        /usr/sfw/bin /bin /usr/sbin /sbin/ usr/openwin/bin /usr/local/bin \
        /opt/WANdisco/bin ${SOA_ORACLE_HOME:-xxxx}/common/bin \
        ${ORACLE_HOME}/common/bin ${WL_HOME}/common/bin ${SQLPLUS_HOME} \
        ${scripts} ${scripts%/*}/bin ${lscripts:-''}; do
    if [[ -d ${DIR} && -r ${DIR} && ! -L ${DIR} ]]; then
        PATH=${PATH}:${DIR}
    fi
done
PATH=${PATH#:}

CLASSPATH=
for FILE in ${WL_HOME}/server/lib/weblogic.jar \
    	    /cpg/3rdParty/scripts/cpg/testing .; do
    if [[ -e ${FILE} ]]; then
        if ! [[ :${CLASSPATH}: =~  :${FILE}: ]]; then
            CLASSPATH=${CLASSPATH#:}:${FILE}
        fi
    fi
done

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

if [ ${CPG_HOSTNAME_COUNT} -gt 1 ]; then
    echo
    echo 'ERROR in PROFILE:  Found more than 1 match of HOSTNAME in'
    echo "  ${CPG_ALIAS_LOOKUP_FILE}"
    echo
fi
if [ ${CPG_HOSTNAME_COUNT} -ge 1 ]; then
    CPG_HOSTNAME=$(echo ${CPG_HOSTNAME} | cut -d, -f2)
    CPG_TIER=${CPG_HOSTNAME##*-}
elif [[ -n ${STACK} ]]; then
    CPG_HOSTNAME=localhost
    CPG_TIER=Local
else
    CPG_TIER=None
fi

case "${CPG_HOSTNAME:0:3}" in
    prd|l-p|s-p)
        USER_PATTERN='prd[156][01]'
        ;;
    stg|l-s|s-s)
        USER_PATTERN='stg[156][012345]'
        ;;
    dev|l-d|s-d)
        USER_PATTERN='dev[156][012345]'
        ;;
    localhost)
        USER_PATTERN=${LOGNAME}
        ;;
    *)
        USER_PATTERN=''
        ;;
esac

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

# Fix for
alias wlps="ps -fu ${LOGNAME} | grep [w]eblogic"
if [[ $(uname -r) == '5.10' ]]; then
    alias wlps="/usr/ucb/ps -axww | grep [w]eblogic."
fi

if [ $(uname) == SunOS ]; then
    memuse() {
        local memory=($(/usr/sbin/swap -s | tr -d -c '0123456789 '))
        echo Memory utilization: $(( ${memory[2]} * 100 / \
            (  ${memory[2]} +  ${memory[3]} ) ))%
    }

    swapuse() {
        swap -lk | tr -d -c '0123456789 s' |\
        awk 'BEGIN { blocks = 8; free = 8; }
            $NF ~ /^[0-9]+$/ { blocks = blocks + $(NF-1); free = free + $NF; }
            END { print "Swap utilization:",
                    int( ( ( 512 + blocks - free ) / blocks ) * 100 ) "%",
                    "of", int(blocks/1048576), "GB"}'
    }
fi

if [[ "${STACKUSER}" != 'true' || -n "${CPG_USER}" ]]; then
    use() {
        CPG_USER=${1} source ${PROFILE_DIR}/cpg.profile
    }
fi

# Cleanup WSLT temp files
if [[ "${STACKUSER}" == 'true' ]]; then
    find /var/tmp -name wlst_module* -user ${LOGNAME} -mtime +2 \
        -exec rm {} + 2>/dev/null & disown
fi

# Make wget work with HTTPS connections
alias wget='\wget --ca-directory=/cpg/3rdParty/security/ca_dir'

# Fix timezones for some databases - Temporary ??
alias java='java -Doracle.jdbc.timezoneAsRegion=false'

# Fix for WLST - Configure custom trust path; TLSv1
export WLST_PROPERTIES="-Dweblogic.security.TrustKeyStore=CustomTrust
-Dweblogic.security.CustomTrustKeyStoreFileName=/cpg/3rdParty/security/CPGTrust.jks
-Dweblogic.security.SSL.enableJSSE=true
-Dweblogic.ssl.JSSEEnabled=true
-Dweblogic.security.SSL.minimumProtocolVersion=TLSv1.2
-Dweblogic.security.allowCryptoJDefaultJCEVerification=true
-Dweblogic.security.allowCryptoJDefaultPRNG=true
-Dweblogic.security.SSL.ignoreHostnameVerification=true
-Djdk.tls.client.protocols=TLSv1,TLSv1.1,TLSv1.2"
#-Dsun.security.ssl.allowUnsafeRenegotiation=true
#-Dsun.security.ssl.allowLegacyHelloMessages=true"


#==================================================
# Show settings
#==================================================
if tty -s; then
    echo "    HOSTNAME = ${CPG_HOSTNAME}"
    echo "    USERNAME = ${CPG_LOGNAME:=$LOGNAME}"
    if [ "${PROJECT_NAME}" != 'USER' ]; then
        echo "     PROJECT = ${PROJECT_NAME}"
        echo "        TIER = ${CPG_TIER}"
        echo "   APP_STACK = ${APP_STACK}"
        echo "   VAR_STACK = ${VAR_STACK}"
    fi
    echo
    echo "   JAVA_HOME = ${JAVA_HOME}"
    [[ ${JAVA_HOME} != ${JAVA_VERSION} ]] && \
    echo "JAVA_VERSION = ${JAVA_VERSION}"
    echo "     WL_HOME = ${WL_HOME}"
    echo
    echo "        PATH = ${PATH}"
    echo "   CLASSPATH = ${CLASSPATH}"

    if [ $(uname) == SunOS ]; then
        echo
        echo "      MEMORY = $(memuse | cut -d\  -f3)"
        echo "        SWAP = $(swapuse | cut -d\  -f3-)"
    fi

    echo
    echo '------------------------------------------------------------'
    echo
fi

unset STACKNUM PROJECT CPG_TIER


#==================================================
# Update and verify status of the automation directory
#==================================================
if [[ ${CPG_HOSTNAME} = *-cpodeploy && ${CPG_LOGNAME} == ${USER} ]]; then
    svn update ${automation}
    svn status ${automation}
fi


# EOF
