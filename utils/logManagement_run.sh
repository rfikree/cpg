#!/bin/bash
#set -x

minimumCompress=1
minimumDelete=14
scriptDir=$(dirname $0)


usage() {
	cat <<EOF

usage $0 [compress_days [delete_days]

  Runs the compress script and optionally the delete script once an hour or so

  compress_days (default $minimumCompress) - days until log files will be compressed.
  delete_days - days until log files will be deleted; never if not set.

  Minimum values: compress_days = $minimumCompress; delete_days = $minimumDelete

EOF
	exit 1
}


if [ "${1//[0-9]/}" != "" ]; then
	usage
fi
if [ "${2//[0-9]/}" != "" ]; then
	usage
fi



# Check and fix compressDays parameter
compressDays=${1:-$minimumCompress}
if [ ${compressDays} -lt ${minimumCompress} ]; then
	echo "Setting compress days to $minimumCompress"
	compressDays=${minimumCompress}
fi

# Check and fix deleteDays parameter
deleteDays=${2}
if [ ${deleteDays:-$minimumDelete} -lt ${minimumDelete} ]; then
	echo "Setting delete days to $minimumDelete"
	deleteDays=${minimumDelete}
fi

# Don't allow setting deletion in production
if [ ${LOGNAME:0:3} = "prd" ]; then
	if [ ${deleteDays:-0} -le ${minimumDelete} ]; then
		echo "Skipping deletion for production: ${ENVIRONMENT:-prd}"
		deleteDays=
	else
		deleteDays=400
	fi
fi


# Setup logging directory
VAR_STACK=/cpg/cpo_var/a${LOGNAME:3:1}${LOGNAME:0:1}${LOGNAME:3:2}
logDir=${VAR_STACK}/cleanup_logs
[ -d ${logDir} ] || mkdir ${logDir}


# Run the compression script
logFile=${logDir}/compress.$(date +%y%m%d_%H%M)
${scriptDir}/logManagement_compress.sh ${compressDays} > ${logFile} 2>&1
[ $(cat ${logFile} | wc -l) -le 3 ] &&  rm ${logFile}


# Conditionally run the compression script
if [ ${deleteDays:-0} -ge ${minimumDelete} ]; then
	logFile=${logDir}/delete.$(date +%y%m%d_%H%M)
	${scriptDir}/logManagement_delete.sh ${deleteDays} > ${logFile} 2>&1
	[ $(cat ${logFile} | wc -l) -le 3 ] &&  rm ${logFile}
fi


# EOF
