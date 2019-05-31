#! /bin/bash

umask 022

# Update here if JAVA or WebLogic is updated
case $(uname) in
SunOS)
    for JAVA_HOME in  $(ls -drt /cpg/3rdParty/installs/java/jdk1.7*); do
        continue
    done
    ;;
Linux)
    for JAVA_HOME in  $(ls -drt /usr/java/jdk1.7*); do
        continue
    done
    ;;
esac
JAVA_VENDOR=Sun

export JAVA_HOME JAVA_VENDOR
export WL_HOME=/cpg/3rdParty/installs/Oracle/Middleware_Home1/wlserver_10.3

# Make everything visible
umask 022

# Setup the environment
export CLASSPATH=${WL_HOME}/server/lib/weblogic.jar
export PATH=${JAVA_HOME}/bin:${WL_HOME}/common/bin:${PATH}
export WLST_PROPERTIES="-Dweblogic.security.TrustKeyStore=CustomTrust
    -Dweblogic.security.CustomTrustKeyStoreFileName=/cpg/3rdParty/security/CPGTrust.jks
    -Dweblogic.ThreadPoolPercentSocketReaders=75
    -Dweblogic.ThreadPoolSize=32
    -Dweblogic.security.SSL.enableJSSE=true
    -Dweblogic.security.allowCryptoJDefaultJCEVerification=true
    -Dweblogic.security.allowCryptoJDefaultPRNG=true
    -Dweblogic.security.SSL.enableJSSE=true
    -Dweblogic.ssl.JSSEEnabled=true
    -Dweblogic.security.SSL.minimumProtocolVersion=TLSv1
    -Dweblogic.security.allowCryptoJDefaultJCEVerification=true
    -Dweblogic.security.allowCryptoJDefaultPRNG=true
    -Dweblogic.security.SSL.ignoreHostnameVerification=true
    -Djdk.tls.client.protocols=TLSv1,TLSv1.1,TLSv1.2"

# Determine the environment to run reports for
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
CPG_HOSTNAME=$(egrep -i "^${HOSTNAME}," ${CPG_ALIAS_LOOKUP_FILE})
CPG_HOSTNAME=$(echo ${CPG_HOSTNAME} | cut -d, -f2)
CPG_ENV=${CPG_HOSTNAME%-*}
CPG_ENV=${CPG_ENV#*-}


# Generate reports
$(dirname ${0})/build_reports.py -e ${CPG_ENV} &> buildReports.log

# Copy reports to reporting server
scp ${CPG_ENV}*.html \
    optadm@cpowiki.cpggpc.ca:/cpg/cpo_apps/build-info/wipro &> scp.log

# Copy the profiles to NFS - new functionality
cp ${CPG_ENV}*.properties \
    /cpg/repos/maven/release_repo/deployment_manifests &> scp.log

# EOF
