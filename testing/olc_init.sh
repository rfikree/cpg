#!/sbin/sh
# Test file for init.d environment

LOGFILE=/var/tmp/init.sh.log

echo 				>> ${LOGFILE}
/bin/date 			>> ${LOGFILE}
echo PATH: $PATH 	>> ${LOGFILE}
echo $0 $@ 			>> ${LOGFILE}

echo 				>> ${LOGFILE}
echo env: 			>> ${LOGFILE}
/bin/env 			>> ${LOGFILE}

echo 				>> ${LOGFILE}
echo set: 			>> ${LOGFILE}
set 				>> ${LOGFILE}

echo 				>> ${LOGFILE}
/bin/df -h /cpg/*	>> ${LOGFILE}
echo 				>> ${LOGFILE}

# EOF
