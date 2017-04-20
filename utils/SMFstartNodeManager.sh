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

# Create variable to store the application user ID (ie: dev50/stg50/prd50 = 50, dev10/stg10/prd10 = 10)
appid=`/usr/bin/echo $username | /usr/bin/cut -c4-5`

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

# build the Weblogic node manager script name to run
script="/cpg/cpo_apps/a${appnum}d${appid}/a${appnum}d${appid}${domain}/bin/startNodeManager.sh"

#echo "The script name to be run is: $script"

# The 50 and 60 stack users have a different syntax for starting the node manager that differs from the 10, 20 & 30 stacks
case ${appid} in
	5*|6*)
		#echo "The command to execute would be: $script > /cpg/cpo_var/a${appnum}d${appid}/a${appnum}d${appid}${domain}/servers/runtime/${CPG_HOSTNAME}-nodemgr_nohup.out 2>&1"
		$script > /cpg/cpo_var/a${appnum}d${appid}/a${appnum}d${appid}${domain}/servers/runtime/${CPG_HOSTNAME}-nodemgr_nohup.out 2>&1
		;;
	*)
		#echo "The command to execute would be: $script"
		$script
		;;
esac

exit $SMF_EXIT_OK