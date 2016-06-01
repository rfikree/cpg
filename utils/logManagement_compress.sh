#!/bin/bash

SCRIPT_DIR=$(cd $(dirname $0) >/dev/null; echo ${PWD})
SCRIPT_NAME=$(basename $0)
STACK_NUM=${LOGNAME:3:2}
PROJECT=${LOGNAME:3:1}

MIN_DAYS=1
MAX_DAYS=31
unset doCCclean

COMPRESS_DAYS=${1}

if [[ -z "${COMPRESS_DAYS}" \
|| ${COMPRESS_DAYS} != ${COMPRESS_DAYS//[^0-9]} ]];then
	echo "Usage examples..."
	echo "    ${SCRIPT_DIR}/logManagement_compress.sh 3"
	echo "    Compress files older than 3 days"
	echo ""
	exit 1
fi


#### Subroutines

cleanCC() {
	${SCRIPT_DIR}/cc_clean.py ${1}
}

lockfile() {
	local lockfile=$1.lok
	if [ ! -f $1 ]; then
		echo Lockfile: missing file $1
		return 1
	elif ( umask 777; mkdir ${lockfile} ); then
		trap "[ -d ${lockfile} ] && rmdir ${lockfile}" EXIT
		return 0
	else
		echo Lockfile: already locked $1
		return 1
	fi
}

unlockfile() {
	local lockfile=$1.lok
	if [ ! -d ${lockfile} ]; then
		echo Unlockfile: no lock for $1
	else
		rmdir ${lockfile}
	fi
}

# Move files to history directory creating directory if required
# Skip if target exists.  It should be moved on a later run.
archiveFile() {
	[ -n "$doCCclean" ] && cleanCC ${1}
	local file=$(basename $1)
	local baseDir=$(dirname $1)/history
	local subDir=${file%%.*}
	subDir=${subDir%-${STACK}d[1-9][-_]c[1-9]m[0-9]ms0[0-9]*}
	subDir=${subDir%_${STACK}d[1-9][-_]c[1-9]m[0-9]ms0[0-9]*}
	subDir=${subDir%AdminServer*}
	subDir=${subDir%$hostname*}
	if [ -z "${subDir}" ]; then
		suffix=${file#${STACK}d[1-9][-_]c[1-9]m[0-9]ms0[0-9]}
		suffix=${suffix#AdminServer}
		subDir=${file%$suffix}
	fi
	local targetDir=${baseDir}/${subDir}
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
		local prefix=${1%.log*}
		prefix=${prefix%.out*}
		if [[ ${prefix} = ${prefix/20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]/} ]]; then
			# Timestamp is modification date less 1 hours
			# This is to work around DST time shifts
			local mtime=$(perl -MPOSIX -e '$mt = (stat $ARGV[0])[9] - 3900; \
				print POSIX::strftime "%Y-%m-%d\n", localtime($mt)', ${1})

			local suffix=${1#$prefix}
			local suffix=.${suffix//[^a-z]/}
			local newName=${prefix}_${mtime}${suffix}
			if [[ -f ${newName} || -f ${newName}.gz ]]; then
				for x in {0..99}; do
					newName=${prefix}_${mtime}x${x}${suffix}
					if [[ ! -f ${newName} && ! -f ${newName}.gz ]]; then
						break
					fi
				done
			fi
			echo  ${1} $(basename ${newName})
			mv -i ${1} ${newName}
			loc			# Temporary fix to handle duplicated SSO lines
			if [[ ${newName} =~ /a1p1.d1-c1m.ms0._20 ]]; then
				nice uniq ${newName} ${newName}.uniq
				touch -mr ${newName} ${newName}.uniq
				mv ${newName}.uniq ${newName}
			fi
		fi
	else
		echo "Filename \"${1}\" is not a file"
	fi
}

# Compress files avoiding collisions
compressFile() {
	if [ -f "${1}" ]; then
		if [[ ${1} = ${1%.gz} && ${1} = ${1%.zip} ]]; then
			local file=${1}
			if [ -f ${file}.gz ]; then
				local filebase=${file%.*}
				local fileext=.${file##*.}
				for x in {0..9}; do
					local newfile=${filebase}x${x}${fileext}
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

echo "Executing $SCRIPT_NAME for $LOGNAME."

case "${LOGNAME:0:3}" in
	prd )
		ENVIRONMENT="p"
		MAX_DAYS=14
		if [ ${LOGNAME:0:4} == "prd1" ];then
			doCCclean=true
		fi
		;;
	stg )
		ENVIRONMENT="s"
		;;
	dev )
		ENVIRONMENT="d"
		;;
	* )
		echo "Run only from a stack userid"
		exit 1
		;;
esac

STACK="a${PROJECT}${ENVIRONMENT}${STACK_NUM}"
CPG_VAR=/cpg/cpo_var/${STACK}
CPG_APPS=/cpg/cpo_apps/${STACK}

if [ ! -d ${CPG_VAR} ]; then
	echo "Can not locate working directory ${CPG_VAR}"
	exit 99
fi
cd ${CPG_VAR} &>/dev/null


if [ ${COMPRESS_DAYS} -lt ${MIN_DAYS} ]; then
	echo "Adjusted compress days from ${COMPRESS_DAYS} to ${MIN_DAYS}"
	COMPRESS_DAYS=${MIN_DAYS}
elif [ ${COMPRESS_DAYS} -gt ${MAX_DAYS} ]; then
	echo "Adjusted compress days from ${COMPRESS_DAYS} to ${MAX_DAYS}"
	COMPRESS_DAYS=${MAX_DAYS}
fi


#### Move logs to history directories

# Server logs for inactive servers (contents and over 1 days old)
for server in ${STACK}*/servers/history/a*; do
	server=${server##*/}
	server_var=${CPG_VAR}/${server%-*}/servers/${server}
	server_apps=${CPG_APPS}/${server%-*}/servers/${server}
	server_lok=${server_apps}/tmp/${server}.lok

	if [ ! -f ${server_lok} ]; then
		for file in $(find ${server_var}*.log \
			${server_var}.out -mtime +1 -size +1 2>/dev/null); do
				mv -i ${file} ${file}00999
		done
	else
		echo ${server} appears to be running
	fi
done

# Recently rotated logs
# Use two digits for log files to skip rotated GC logs
for file in ${STACK}*/*/*.log*[0-9][0-9]* ${STACK}*/servers/*.out*[0-9]* \
		${STACK}*/*/*20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*; do
	if [ -f ${file} ]; then
		lockfile ${file} || continue
		archiveFile ${file}
		unlockfile ${file}
	fi
done

# Inactive log files
for file in $(find ${STACK}*/*/*.log -mtime +300); do
	if [ -f $file ]; then
		lockfile ${file} || continue
		archiveFile $file
		unlockfile ${file}
	fi
done


#### Rename logs in history directories

# Rename files for later compression
for file in $(find  ${STACK}*/*/history -type f \
		\( ! -name \*.gz -a ! -name \*.zip -a ! -name \*-gc.log* \
		-a ! -name \*20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]* \)  2>/dev/null); do

	lockfile ${file} || continue
	renameFile ${file}
	unlockfile ${file}
done


#### Begin compression
echo "Compressing..."

# Compress rotated domain logs after 1 day
for file in $(find ${STACK}*/servers/history/AdminServer \
		-name "${STACK}d?_20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*.log" \
		-mtime +1 2>/dev/null); do

	lockfile ${file} || continue
	compressFile ${file}
	unlockfile ${file}
done

# Compress remaining logs (logback format) and server files(.log, .out)
for file in $(find ${STACK}*/*/history ! -name \*gz ! -name \*zip -type f \
		-name \*20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]\* \
		-mtime +${COMPRESS_DAYS} 2>/dev/null); do

	lockfile ${file} || continue
	compressFile ${file}
	unlockfile ${file}
done

# Compress sso profile log files.
for file in $(find ${STACK}*/applications/ssoprofilelogs \
		! -name \*gz ! -name \*zip -type f \
		-name \*20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]\* \
		-mtime +${COMPRESS_DAYS} 2>/dev/null); do

	lockfile ${file} || continue
	compressFile ${file}
	unlockfile ${file}
done


#### Remove old garbage collection logs (after 4 weeks)
# Keeps rotated logs a reasonable amount of time.

for file in $(find ${STACK}*/servers/*-gc.log* \
		-mtime +28 2>/dev/null); do
	echo Removing ${file}
	rm ${file}
done


#### Skip SOA Cleanup for non-SOA stacks
if [ ${PROJECT} -lt 5 ]; then
	echo "Complete."
	exit 0
fi


#### SOA Cleanup

# SOA diagnostic logs
for file in ${STACK}*/servers/*/logs/*-diagnostic-[0-9]*.log; do
	if [ -f $file ]; then
		lockfile ${file} || continue
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
		unlockfile ${file}
	fi
done

# SOA owsm/msglogging logs
for file in ${STACK}*/servers/*/logs/owsm/msglogging/diagnostic-[0-9]*.log ; do
	if [ -f $file ]; then
		lockfile ${file} || continue
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
		unlockfile ${file}
	fi
done

# SOA syman logs
for file in ${STACK}*/servers/*/sysman/log/emoms-[0-9]*.log ; do
	if [ -f $file ]; then
		lockfile ${file} || continue
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
		unlockfile ${file}
	fi
done

echo "Complete."


# EOF
