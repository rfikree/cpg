#!/usr/bin/bash
#set -x

#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#
# Copyright 2006 Sun Microsystems, Inc. All rights reserved.
# Use is subject to license terms.
#
# ident "%Z%%M% %I% %E SMI"
. /lib/svc/share/smf_include.sh
# SMF_FMRI is the name of the target service. This allows multiple instances
# to use the same script

getproparg() {
 val=`svcprop -p $1 $SMF_FMRI`
 [ -n "$val" ] && echo $val
}

# Config parameters
SCRIPT_NAME=$(basename ${0})

PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles

CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
export CPG_HOSTNAME=$(egrep -i "^$(hostname)," ${CPG_ALIAS_LOOKUP_FILE} | cut -d, -f2)

# Get User who is running script
username=`getproparg method_context/user`
#echo "The user running this script is: $username"

# Create variable to store the application number (1=CPO,2=BDT,3=CMSS,5=SOA Common Payment,6=SOA Pulse)
appnum=`/usr/bin/echo $username | /usr/bin/cut -c4`

# Create a variable for the stack (d=development, s=staging, p=production
appstack=`/usr/bin/echo $username | /usr/bin/cut -c1`

# Create variable to store the application user ID (ie: dev50/stg50/prd50 = 50, dev10/stg10/prd10 = 10)
appid=`/usr/bin/echo $username | /usr/bin/cut -c4-5`

# Create a stack variable
stack=a${appnum}${appstack}${appid}

# Handle stop option
PID=`ps -fu ${username} | awk '/java.*[-]client/ {print $2}'`

waitPid() {
	if [[ -n ${PID} ]]; then
		time=0
		while [[ ${time} -lt ${1:-10} ]]; do
			sleep 1
			kill -0 ${PID} 2>/dev/null || break
			time=$(( time + 1 ))
		done
	fi
}

if [ -n "${PID}" ]; then
	if [ "${1}" == stop -o "${1}" == restart ]; then
		echo Killing process\(es\): ${PID} for ${username}
		kill ${PID}
		waitPid 20
		kill -0 ${PID} 2>/dev/null && exit ${SMF_EXIT_ERR_FATAL}
		exit ${SMF_EXIT_OK}
	else
		echo Already running process\(es\): ${PID} for ${username}
		exit ${SMF_EXIT_ERR_NOSMF}
	fi
else
	if [ "${1}" == stop -o "${1}" == restart ]; then
		echo No processes:${PID} for ${username}
		exit ${SMF_EXIT_OK}
	fi
fi


## Wait for file systems to be mounted - randomly 1 to 5 seconds
#for DIR in /cpg/3rdParty /cpg/content /cpg/cpo_apps /cpg/cpo_var; do
#	if [[ -d ${DIR} ]]; then
#		while [[ ! -e ${DIR}/.mounted ]]; do 
#			sleep $(( ${RANDOM} / 6554 + 1 ))
#		done
#	fi
#done


# Determine the WL domain this host runs for the user and assign to domain variable

case ${CPG_HOSTNAME:-''} in
        *-appadm)
                domain=d9
                ;;
        *-bdt)
                domain=d1
                ;;
        *-blcpo)
                domain=d2
                ;;
        *-soaz0)
                domain=d1
                ;;
        *-soaz1)
                domain=d1
                ;;
        *-uicpo)
                domain=d1
                ;;
        *-ws)
                domain=d1
                ;;
esac


# Define the WL_HOME and JAVA_HOME from the Domain.properties file
PROPS_FILE=/cpg/cpo_apps/${stack}/automation/stacks/${stack}/*d1/Domain.properties
if [ -f ${PROPS_FILE} ]; then
	eval $(egrep '^(jdk|bea)Path *=' ${PROPS_FILE} | tr -d ' ')

	if [[ -n ${beaPath} ]]; then
		export WL_HOME=${beaPath}/wlserver_10.3
	fi
fi                                                      
if [[ -n ${jdkPath} ]]; then 
	JAVA_HOME=${jdkPath}
else	# Fallback to directory search
	for JAVA_HOME in $(ls -drt /cpg/3rdParty/installs/java/jdk1.7*); do
		continue
	done
fi
export JAVA_HOME


# LD_LIBRARY_PATH should not be required after next configuration run.
# Add the SAPJCO and SAP Security to LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/cpg/3rdParty/installs/SAP/sapjco-sun_64-2.1.10
LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/cpg/3rdParty/installs/SAP/sap-security-utils


# build the Weblogic node manager script name to run
script="/cpg/cpo_apps/${stack}/${stack}${domain}/bin/startNodeManager.sh"

#echo "The script name to be run is: $script"

# The 50 and 60 stack users have a different syntax for starting the node manager that differs from the 10, 20 & 30 stacks
case ${appid} in
	5*|6*)
		# Set the environment to use UTF-8 en_CA
		export LANG=en_CA.UTF-8
		export LC_ALL=en_CA.UTF-8
		export LC_MONETARY=en_CA.UTF-8
		export LC_NUMERIC=en_CA.UTF-8
		export LC_ALL=en_CA.UTF-8
		export LC_MESSAGES=C
		export LC_COLLATE=en_CA.UTF-8
		export LC_CTYPE=en_CA.UTF-8
		export LC_TIME=en_CA.UTF-8
		#echo "The command to execute would be: $script > /cpg/cpo_var/${stack}/${stack}${domain}/servers/runtime/${CPG_HOSTNAME}-nodemgr_nohup.out 2>&1"
		$script &> /cpg/cpo_var/${stack}/${stack}${domain}/servers/runtime/${CPG_HOSTNAME}-nodemgr_nohup.out &
		sleep 2
		;;
	*)
		#echo "The command to execute would be: $script"
		$script
		;;
esac

exit $SMF_EXIT_OK
