#!/bin/bash

VFSTAB=/etc/vfstab
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


#### Build a remounte script and execute it
echo <<EOT  > ${TMPSCRIPT}
#!/bin/bash

sleep 10

EOT

for MOUNT in awk '/nfs/ {print $3}' ${VFSTAB}; do
	echo umount ${MOUNT} >>  ${TMPSCRIPT}
	echo mount ${MOUNT} >>  ${TMPSCRIPT}
done


echo <<EOT  >> ${TMPSCRIPT}

sleep 2
nfsstat -m

# EOF
EOT

bash ${TMPSCRIPT} &

# EOF
