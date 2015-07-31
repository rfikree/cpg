#!/bin/bash
SCRIPT_DIR=`dirname $0`
SCRIPT_NAME=`basename $0`
OS_USERNAME=`id | cut -d'(' -f2 | cut -d')' -f1`
STACK_NUM=${OS_USERNAME:3:2}
PROJECT=${OS_USERNAME:3:1}
PATH=$PATH:/usr/local/bin

MIN_DAYS=1
MAX_DAYS=91
unset doCCclean

# Handle logs rotated shortly after midnight and/or using EST instead of EDT
export TZ=Canada/Mountain

if [ ! -x /usr/local/bin/stat ]; then
	echo FATAL: /usr/local/bin/stat not executable
	exit 1
fi

COMPRESS_DAYS=${1}

if [[ -z "${COMPRESS_DAYS}" \
|| ${COMPRESS_DAYS} != ${COMPRESS_DAYS//[^0-9]} ]];then
	echo "Usage examples..."
	echo "    ${SCRIPT_DIR}/logManagement_compress.sh 3"
	echo "    Compress files older than 3 days"
	echo ""
	exit -1
fi

#### Subroutines

cleanCC() {
	${SCRIPT_DIR}/cc_clean.py ${1}
}

# Move files to history directory creating directory if required
# Skip if target exists.  It should be moved on a later run.
archiveFile() {
	[ -n "$doCCclean" ] && cleanCC ${1}
	file=$(basename $1)
	baseDir=$(dirname $1)/history
	subDir=${file%%.*}
	subDir=${subDir%-${STACK}d[1-9][-_]c[1-9]m[0-9]ms0[0-9]*}
	subDir=${subDir%_${STACK}d[1-9][-_]c[1-9]m[0-9]ms0[0-9]*}
	subDir=${subDir%AdminServer*}
	subDir=${subDir%$hostname*}
	if [ -z "${subDir}" ]; then
		suffix=${file#${STACK}d[1-9][-_]c[1-9]m[0-9]ms0[0-9]}
		suffix=${suffix#AdminServer}
		subDir=${file%$suffix}
	fi
	targetDir=${baseDir}/${subDir}
	if [ ! -d ${targetDir} ]; then
		mkdir -p ${targetDir}
	fi
	if [ ! -f ${targetDir}/${file} ]; then
		echo $1 ${targetDir}
		mv -i $1 ${targetDir}
	fi
}

# Rename files to include datestamp avoiding collisions.
# uses modification date
renameFile() {
	if [ -f "${1}" ]; then
		prefix=${1%.log*}
		prefix=${prefix%.out*}
		if [[ ${prefix} = ${prefix/20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]/} ]]; then
			# Timestamp is modification date less 2 hours
			# This should the date of the last write
			mtime=$(stat -c %y ${1} | cut -c1-10)

			suffix=${1#$prefix}
			suffix=.${suffix//[^a-z]/}
			newName=${prefix}_${mtime}${suffix}
			if [[ -f ${newName} || -f ${newName}.gz ]]; then
				for x in {0..9}; do
					newName=${prefix}_${mtime}x${x}${suffix}
					if [[ ! -f ${newName} && ! -f ${newName}.gz ]]; then
						break
					fi
				done
			fi
			echo  ${1} $(basename ${newName})
			mv -i ${1} ${newName}
		fi
	else
		echo "Filename \"${1}\" is not a file"
	fi
}

# Compress files avoiding collisions
compressFile() {
	if [ -f "${1}" ]; then
		if [[ ${1} = ${1%.gz} && ${1} = ${1%.zip} ]]; then
			file=${1}
			if [ -f ${file}.gz ]; then
				filebase=${file%.*}
				fileext=.${file##*.}
				for x in {0..9}; do
					newfile=${filebase}x${x}${fileext}
					if [[ ! -f ${newfile} && ! -f ${newfile}.gz ]]; then
						echo ${file} $(basename ${newfile})
						mv -i ${file} ${newfile}
						file=${newfile}
						break
					fi
				done
			fi
			[ -n "$doCCclean" ] && cleanCC ${file}
			echo ${file}
			nice gzip ${file}
		else
			echo "Filename \"${1}\" indicates the file is already compressed"
		fi
	else
		echo "Filename \"${1}\" is not a file"
	fi
}


#### Mainline

echo "Executing $SCRIPT_NAME for $OS_USERNAME."

case "${OS_USERNAME:0:3}" in
	prd )
		ENVIRONMENT="prd"
		ENVIRONMENT_SHORT="p"
		MAX_DAYS=14
		if [ ${OS_USERNAME:0:4} == "prd1" ];then
			doCCclean=true
		fi
		;;
	stg )
		ENVIRONMENT="stg"
		ENVIRONMENT_SHORT="s"
		;;
	dev )
		ENVIRONMENT=""
		ENVIRONMENT_SHORT="d"
		if [ "${OS_USERNAME}" == "dev60" ]; then
			 ENVIRONMENT="stg"
		fi
		;;
	* )
		echo "Run only from a stack userid"
		exit 1
		;;
esac

STACK="a$PROJECT$ENVIRONMENT_SHORT$STACK_NUM"
if [[ "$ENVIRONMENT" != "" && -d "/$ENVIRONMENT/cpo" ]]; then
	CPO_VAR="/$ENVIRONMENT/cpo/cpo_var/$STACK"
else
	CPO_VAR="/cpo/cpo_var/$STACK"
fi
if [ ! -d ${CPO_VAR} ]; then
	echo "Can not locate working directory ${CPO_VAR}"
	exit 99
fi
cd ${CPO_VAR} &>/dev/null


if [ ${COMPRESS_DAYS} -lt ${MIN_DAYS} ]; then
	echo "Adjusted compress days from ${COMPRESS_DAYS} to ${MIN_DAYS}"
	COMPRESS_DAYS=${MIN_DAYS}
elif [ ${COMPRESS_DAYS} -gt ${MAX_DAYS} ]; then
	echo "Adjusted compress days from ${COMPRESS_DAYS} to ${MAX_DAYS}"
	COMPRESS_DAYS=${MAX_DAYS}
fi


#### Move logs to history directories

# Recently rotated logs
# Use two digits for log files to skip rotated GC logs
for file in ${STACK}*/*/*.log*[0-9][0-9]* ${STACK}*/*/*.out*[0-9]* \
		${STACK}*/*/*20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*; do
	if [ -f ${file} ]; then
		archiveFile ${file}
	fi
done

# Server logs for inactive servers (contents and over 2 days old)
for file in $(find ${STACK}*/servers/*[1-9].log ${STACK}*/servers/*.out \
		-mtime +2 -size +1); do
	if [ -f ${file} ]; then
		archiveFile ${file}
	fi
done

# SOA diagnostic logs
for file in ${STACK}*/servers/*/logs/*-diagnostic-[0-9]*.log; do
	if [ -f $file ]; then
		fname=$(basename ${file})
		sname=$(basename ${file%/logs/*})
		dbase=${file%/servers/*}/servers
		version=${fname%.log}
		version=${version##*-}
		target=${fname%-$version*}.log${version}
		tdir=${dbase}/history/${sname}
		[ -d ${tdir} ] || mkdir ${tdir}
		echo  ${file} ${tdir}/${target}
		mv -i ${file} ${tdir}/${target}
	fi
done

# SOA owsm/msglogging logs
for file in ${STACK}*/servers/*/logs/owsm/msglogging/diagnostic-[0-9]*.log ; do
	if [ -f $file ]; then
		fname=$(basename ${file})
		sname=$(basename ${file%/logs/*})
		dbase=${file%/servers/*}/servers
		version=${fname%.log}
		version=${version#emoms-}
		target=${sname}-owsm-${fname%-$version*}.log${version}
		tdir=${dbase}/history/${sname}
		[ -d ${tdir} ] || mkdir ${tdir}
		echo  ${file} ${tdir}/${target}
		mv -i ${file} ${tdir}/${target}
	fi
done

# SOA syman logs
for file in ${STACK}*/servers/*/sysman/log/emoms-[0-9]*.log ; do
	if [ -f $file ]; then
		fname=$(basename ${file})
		sname=$(basename ${file%/sysman/*})
		dbase=${file%/servers/*}/servers
		version=${fname%.log}
		version=${version#emoms-}
		target=${sname}_${fname%-$version*}.log${version}
		tdir=${dbase}/history/${sname}
		[ -d ${tdir} ] || mkdir ${tdir}
		echo  ${file} ${tdir}/${target}
		mv -i ${file} ${tdir}/${target}
	fi
done

# Inactive log files
for file in $(find ${STACK}*/*/*.log -mtime +300); do
	if [ -f $file ]; then
		archiveFile $file
	fi
done


#### Rename logs in history directories

# Rename files for later compression
for file in $(find  ${STACK}*/*/history -type f \
		\( ! -name \*.gz -a ! -name \*.zip -a ! -name \*-gc.log* \
		-a ! -name \*20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]* \)  2>/dev/null); do
	renameFile ${file}
done


#### Begin compression
echo "Compressing..."

# Compress rotated domain logs after 1 day
for file in $(find ${STACK}*/servers/history/AdminServer \
		-name "${STACK}d?_20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*.log" \
		-mtime +1 2>/dev/null); do

	compressFile ${file}
done

# Compress remaining logs (logback format) and server files(.log, .out)
for file in $(find ${STACK}*/*/history ! -name \*gz ! -name \*zip -type f \
		-name \*20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]\* \
		-mtime +${COMPRESS_DAYS} 2>/dev/null); do

	compressFile ${file}
done

# Compress sso profile log files.
for file in $(find ${STACK}*/applications/ssoprofilelogs \
		! -name \*gz ! -name \*zip -type f \
		-name \*20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]\* \
		-mtime +${COMPRESS_DAYS} 2>/dev/null); do

	compressFile ${file}
done

#### Remove old garbage collection logs (after 14 days)
# Keeps rotated logs a reasonable amount of time.

for file in $(find ${STACK}*/servers/*-gc.log* \
		-mtime +14 2>/dev/null); do
	echo ${file}
	rm ${file}
done

echo "Complete."

# EOF
