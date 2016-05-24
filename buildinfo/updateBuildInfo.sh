#! /bin/bash

# Update here if JAVA or WebLogic is updated
export JAVA_HOME=/cpg/3rdParty/installs/java/jdk1.7.0_80
export WL_HOME=/cpg/3rdParty/installs/Oracle/Middleware_Home/wlserver_10.3


# Setup the environment
export CLASSPATH=${WL_HOME}/server/lib/weblogic.jar
export PATH=${JAVA_HOME}/bin:${WL_HOME}/common/bin:${PATH}
export WLST_PROPERTIES="-Dweblogic.security.TrustKeyStore=CustomTrust
	-Dweblogic.security.CustomTrustKeyStoreFileName=/cpg/3rdParty/security/CPGTrust.jks
	-Dweblogic.ThreadPoolPercentSocketReaders=75
	-Dweblogic.ThreadPoolSize=32
	-Dweblogic.security.allowCryptoJDefaultJCEVerification=true
	-Dweblogic.security.allowCryptoJDefaultPRNG=true"

# Determine the environment to run reports for
PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
CPG_HOSTNAME=$(egrep -i "^${HOSTNAME}," ${CPG_ALIAS_LOOKUP_FILE})
CPG_HOSTNAME=${CPG_HOSTNAME##*,}
CPG_ENV=${CPG_HOSTNAME%%-*}


# Generate reports
$(dirname ${0})/buildReports.py -e ${CPG_ENV} &> buildReports.log

# Copy reports to reporting server
scp ${CGP_ENV}*.html \
	optadm@cpowiki.cpggpc.ca:/cpg/cpo_apps/build-info/wipro &> scp.log

# EOF
