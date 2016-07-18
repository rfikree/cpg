#! /bin/bash

SLEEP_TIME=30

while getopts :n: OPT; do
	case ${OPT} in
	n)	SLEEP_TIME=${OPTARG}
		echo 'Matched: -'${OPT} ${OPTARG}
		;;
	*)	echo 'Invalid option -'${OPT} ${OPTARG}
		exit -1
		;;
	esac
done
shift $((OPTIND-1))

while true; do
	clear
	date
	echo
	eval "${@}"
	sleep ${SLEEP_TIME}
done

# EOF
