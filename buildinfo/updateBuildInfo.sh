#! /bin/bash

umask 022

# Update here if JAVA or WebLogic is updated
case $(uname) in
SunOS)
    for JAVA_HOME in  $(ls -dt /cpg/3rdParty/installs/java/jdk1.7* 2>/dev/null); do
        break
    done
    ;;
Linux)
    for JAVA_HOME in  $(ls -dt /usr/java/jdk1.7* 2>/dev/null); do
        break
    done
    ;;
esac
JAVA_VENDOR=Sun

export JAVA_HOME JAVA_VENDOR
export WL_HOME=/cpg/3rdParty/installs/Oracle/Middleware_Home1/wlserver_10.3

# WebLogic 12c if possible
if [ -d "/cpg/3rdParty/installs/Oracle/fmw12c-latest/wlserver" ] && [ -d "/usr/java/latest" ]; then
        WL_HOME=/cpg/3rdParty/installs/Oracle/fmw12c-latest/wlserver
        JAVA_HOME=/usr/java/latest
fi


# Make new files visible to everyone - doesn't seem to work with Java
umask 022

# Setup the environment - Add script directory to python path
export WLST_EXT_CLASSPATH=${WL_HOME}/server/lib/weblogic.jar
export PATH=${JAVA_HOME}/bin:${WL_HOME%/*}/oracle_common/common/bin:${WL_HOME}/common/bin:${PATH}
export WLST_PROPERTIES="-Dweblogic.security.TrustKeyStore=CustomTrust
    -Dweblogic.security.CustomTrustKeyStoreFileName=/cpg/3rdParty/security/CPGTrust.jks
    -Dweblogic.ThreadPoolPercentSocketReaders=75
    -Dweblogic.ThreadPoolSize=32
    -Dweblogic.security.SSL.enableJSSE=true
    -Dweblogic.security.allowCryptoJDefaultJCEVerification=true
    -Dweblogic.security.allowCryptoJDefaultPRNG=true
    -Dweblogic.security.SSL.enableJSSE=true
    -Dweblogic.ssl.JSSEEnabled=true
    -Dweblogic.security.SSL.minimumProtocolVersion=TLSv1.2
    -Dweblogic.security.allowCryptoJDefaultJCEVerification=true
    -Dweblogic.security.allowCryptoJDefaultPRNG=true
    -Dweblogic.security.SSL.ignoreHostnameVerification=true
    -Djdk.tls.client.protocols=TLSv1.2
    -Dpython.path=$(dirname ${0})"

# Determine the environment to run reports for
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
CPG_HOSTNAME=$(egrep -i "^${HOSTNAME}," ${CPG_ALIAS_LOOKUP_FILE})
CPG_HOSTNAME=$(echo ${CPG_HOSTNAME} | cut -d, -f2)
CPG_ENV=${CPG_HOSTNAME%-*}
CPG_ENV=${CPG_ENV#*-}
[[ -z ${CPG_ENV} ]] && CPG_ENV=loc


# Generate reports
$(dirname ${0})/build_reports.py -e ${CPG_ENV} &> buildReports.log

# Make new property files visible to everyone - this works.
chmod o=g *.properties *.html

# Copy reports to reporting server
scp ${CPG_ENV}*.html \
    optadm@cpowiki.cpggpc.ca:/cpg/cpo_apps/build-info/wipro &> scp.log

# Copy the profiles to NFS - new functionality
rsync -a ${CPG_ENV}*.properties \
    /cpg/repos/deployment_manifests &> copy.log

# EOF
