#!/bin/bash
SCRIPT_DIR=`dirname $0`
SCRIPT_NAME=`basename $0`
OS_USERNAME=`id | cut -d'(' -f2 | cut -d')' -f1`
STACK_NUM=${OS_USERNAME:3:5}
PROJECT=${OS_USERNAME:3:1}

DELETE_DAYS=$1

usage() {
	echo
	echo "Usage examples..."
	echo "    ./logManagement_delete.sh 3"
	echo "    Delete .gz files older than 3 days"
	echo
	echo "    Production is limited to servers and introscope directores"
	echo "       and hard set to 400 days"
	echo
	exit -1
}

if [[ -z $DELETE_DAYS || $DELETE_DAYS != ${DELETE_DAYS//[^0-9]} ]];then
	usage
fi


echo "Executing $SCRIPT_NAME for $OS_USERNAME"

case "${OS_USERNAME:0:3}" in
	prd )
		ENVIRONMENT="prd"
		ENVIRONMENT_SHORT="p"
		DELETE_DAYS=400
		;;
	stg )
		ENVIRONMENT="stg"
		ENVIRONMENT_SHORT="s"
		if [ ${DELETE_DAYS} -lt 28 ]; then
			DELETE_DAYS=35
		fi
		;;
	dev )
		ENVIRONMENT=""
		ENVIRONMENT_SHORT="d"
		if [ "${OS_USERNAME}" == "dev60" ]; then
			 ENVIRONMENT="stg"
		fi
		if [ ${DELETE_DAYS} -lt 3 ]; then
			DELETE_DAYS=3
		fi
		;;
	* )
		echo "Unsupported user id ${OS_USERNAME}"
		usage
		USER_ID="" ;;
esac

STACK="a$PROJECT$ENVIRONMENT_SHORT$STACK_NUM"
if [[ "$ENVIRONMENT" != "" && -d "/$ENVIRONMENT/cpo" ]]; then
	CPO_VAR="/$ENVIRONMENT/cpo/cpo_var/$STACK"
else
	CPO_VAR="/cpo/cpo_var/$STACK"
fi

# Delete compressed files after delete period has expired.
echo "Deleting..."
find ${CPO_VAR}/${STACK}*/* -type f -mtime +${DELETE_DAYS} -name '*.gz' \
	-print -exec rm {} \;
find ${CPO_VAR}/${STACK}*/* -type f -mtime +${DELETE_DAYS} -name '*.zip' \
	-print -exec rm {} \;


# Cleanup http and compression logs
if [ $(date +%H) -eq 20 ]; then
	find ${CPO_VAR}/httpcheck -type f -mtime +35 -print -exec rm {} \;
	find ${CPO_VAR}/cleanup_logs -type f -mtime +189 -print -exec rm {} \;

	# Cleanup this directory (stack traces etc.)
	#HACK:  Uses two "-type f" arguments to limit list to files.
	# Order of arguments is important
	# Inner if is paranoid programming.
	for file in $( find ${CPO_VAR}/* -mtime +98 -type f -o \
			\( -type d -prune \) -type f  2>/dev/null ); do
		if [[ -f ${file} && "${CPO_VAR}" = "$(dirname ${file})" ]]; then
			echo ${file}
			rm ${file}
		fi
	done

	# Agressively cleanup compressed console logs (old format)
	find ${CPO_VAR}/${STACK}*/servers/history/AdminServer -mtime +7 \
		-name 'a????d?.log*[0-9].gz' -print -exec rm {} \; 2> /dev/null

	# Agressively cleanup compressed console logs (new format)
	find ${CPO_VAR}/${STACK}*/servers/history/AdminServer -mtime +7 \
		-name 'a????d?_20[0-9][0-9]-*.log.gz' -print -exec rm {} \; 2> /dev/null
fi

echo "Complete."

# EOF
