#!/bin/bash

VFSTAB=/etc/fstab
TMPSCRIPT=/tmp/remounts.$$

if [ ! -w ${VFSTAB} ]; then
	echo
	echo FATAL: Unable to write to ${VFSTAB}
	echo
	exit 1
fi


if grep vers=3 ${VFSTAB}; then
	echo
	echo Version already set
	echo
	exit 0
fi

# Backup
if [ ! -f ${VFSTAB}.orig ]; then
	cp ${VFSTAB} ${VFSTAB}.orig
fi

# Update the file in place
perl -pi -e 's/-$/vers=3/ if (/nfs/)' ${VFSTAB}
perl -pi -e 's/intr,rsize/intr,vers=3,rsize/ if (/nfs/)' ${VFSTAB}

# EOF
