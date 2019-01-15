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
INSTALL_DIR=/cpg/3rdParty/installs
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
PROJECT_NAME=USER
STACK=a1l10
SVN_REPO=http://cposvn.cpggpc.ca/configuration_repo/automation

VISUAL=vi

export PROJECT_NAME STACK SVN_REPO VISUAL

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
        USER_PATTERN=''
        ;;
esac
export ENVIRONMENT STACKUSER

#### Default values - may be overriden;

JAVA_BASE=${INSTALL_DIR}/java
[[ $(uname) == Linux ]] && JAVA_BASE=/usr/java

for JAVA_VERSION in $(ls -drt ${JAVA_BASE}/jdk1.7* 2>/dev/null); do
    if [ -d ${JAVA_VERSION} ]; then
        JAVA_HOME=${JAVA_VERSION}
    else
        echo ${JAVA_VERSION} is invalid
    fi
done
if [[ $(uname) == Linux || -z ${JAVA_VERSION} ]]; then
    JAVA7_VERSION=${JAVA_VERSION}
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

MW_DIR=Middleware_Home12c
WL_DIR=wlserver


#### Configuration by Project

LOB=${STACK_NUM:0:1}
domains='1'
case $LOB in
    1)  PROJECT_NAME=CPO
        domains='1 2';;
    3)  PROJECT_NAME=WS;;
    5)  PROJECT_NAME=CPC-SOA
        MW_DIR=fmw${STACK_NUM}
        WL_DIR=wlserver_10.3
        ;;
    6)  PROJECT_NAME=PULSE
        MW_DIR=fmw${STACK_NUM}
        WL_DIR=wlserver_10.3
        ;;
    *)  ;;
esac

if [[ ${PROJECT_NAME} == CPO && $(uname) == Linux ]]; then
    domains='1 2'
fi

if [[ ${PROJECT_NAME} == CPO && $(id | cut -d "(" -f2 | cut -d ")" -f1) == dev12 ]] || [[ ${PROJECT_NAME} == CPO && $(id | cut -d "(" -f2 | cut -d ")" -f1) == stg12 ]]; then
    domains='1 2'
    MW_DIR=Middleware_Home1
    WL_DIR=wlserver_10.3
    JAVA_HOME=/cpg/3rdParty/installs/java/jdk1.7.0_181
fi

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


if [[ "${WL_HOME}" != "${beaPath}/${WL_DIR}" \
&& -f "${beaPath}/${WL_DIR}/server/lib/weblogic.jar" ]]; then
    #echo Setting WL_HOME from Domain.properties
    #echo
    WL_HOME=${beaPath}/${WL_DIR}
fi

export JAVA_HOME WL_HOME BEA_HOME ORACLE_HOME JAVA_HOME2
unset MW_DIR WL_DIR jdkPath beaPath jdkVer JAVA7_VERSION


#================================================
# Configure Paths
#================================================
# Force standard $PATH directory
PATH=
for DIR in ${JAVA_VERSION}/bin /usr/xpg6/bin /usr/xpg4/bin /usr/bin \
        /usr/sfw/bin /bin /usr/sbin /sbin/ usr/openwin/bin /usr/local/bin \
        /opt/WANdisco/bin ${ORACLE_HOME}/common/bin ${SQLPLUS_HOME} \
        ${scripts} ${scripts%/*}/bin ${lscripts}; do
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

if [[ ! ${CLASSPATH} =~ /cpg/3rdParty/scripts/cpg/testing ]]; then
    CLASSPATH=${CLASSPATH%:}:/cpg/3rdParty/scripts/cpg/testing
fi

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


case "${CPG_HOSTNAME:0:3}" in
    prd|l-p|s-p)
        USER_PATTERN='prd[1356][01]'
        ;;
    stg|l-s|s-s)
        USER_PATTERN='stg[1356][012345]'
        ;;
    dev|l-d|s-d)
        USER_PATTERN='dev[1356][012345]'
        ;;
    *)
        STACKUSER=false
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
if [[ $(uname -r) == '5.10' ]]
    alias wlps="/usr/ucb/ps -axww | grep [w]eblogic."
fi

if [ $(uname) == SunOS ]; then
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
-Dweblogic.security.SSL.minimumProtocolVersion=TLSv1
-Dweblogic.security.allowCryptoJDefaultJCEVerification=true
-Dweblogic.security.allowCryptoJDefaultPRNG=true
-Dweblogic.security.SSL.ignoreHostnameVerification=true
-Djdk.tls.client.protocols=TLSv1,TLSv1.1,TLSv1.2"
#-Dsun.security.ssl.allowUnsafeRenegotiation=true
#-Dsun.security.ssl.allowLegacyHelloMessages=true"


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

unset OS_USERNAME STACKNUM CPG_TIER


#==================================================
# Verify status of the automation directory
#==================================================
if [[ ${STACKUSER} == true && -z ${CPG_USER} && ${CPG_HOSTNAME} = *-cpodeploy ]]; then
    SVN_WD_VER=$(sqlite3 ${automation}/.svn/wc.db "PRAGMA user_version" 2>/dev/null)
    if [[ $(uname) == Linux &&  ! -d ${automation}  ]]; then
         echo -e '\ny' || svn co ${SVN_REPO}/trunk/secure ${automation}
    elif [[ $(uname) = Linux && ${SVN_WD_VER} -eq 29 ]]; then
        svn update ${automation}
        svn status ${automation}
    elif [[ $(uname) = SunOS && ${SVN_WD_VER} -eq 31 ]]; then
        svn update ${automation}
        svn status ${automation}
    fi
fi


# EOF
