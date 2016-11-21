#! /bin/bash
# Zip critical files in /etc and attempt to upload to jscape server

# Usage /cpg/3rdParty/scripts/cpg/utils/zip_etc.sh [user|'' [scp_host]]

# Make zip readable
umask 022

# Zip file
ZIP_FILE=${HOME}/$(hostname).zip

# Files to inclued
INCLUDE_FILES="
/etc/auto_homke
/etc/auto_master
/etc/bootparams
/etc/coreadm.conf
/etc/defaultrouter
/etc/defaultdomain
/etc/dumpadm.conf
/etc/ethers
/etc/groups
/etc/inetd.conf
/etc/logadm.conf
/etc/logrotate.conf
/etc/notrouter
/etc/nscd.conf
/etc/nsswitch.conf
/etc/pam.conf
/etc/pam.conf-winbind
/etc/password
/etc/release
/etc/resolv.conf
/etc/sudoers.conf
/etc/syslog.conf
/etc/system
/etc/TIMEZONE
/etc/vfstab
/etc/crond.d/*
/etc/default/*
/etc/inet/*
/etc/mail/*
/etc/security/*
/etc/init.d/*
/etc/rc?.d/*
"


# Create the zip file
echo
echo Creating ${ZIP_FILE}
zip -q -r -y ${ZIP_FILE} ${INCLUDE_FILES}
echo


# Determine upload host

echo Determining upload host
if [[ -n ${2} ]]; then 
	host=${2}
elif ping -c1 -t10 ip-l-00274-a5c.hs-cpggpc.ca > /dev/null; then
	host=ip-l-00274-a5c.hs-cpggpc.ca
elif ping -c1 -t10 ip-l-00272-a5c.hs-cpggpc.ca > /dev/null; then
	host=ip-l-00272-a5c.hs-cpggpc.ca
else
	host=
fi


# Upload the file

if [[ -n ${host} ]]; then
	echo Uploading to ${1}${1:+@}${host}:Solaris
	scp -P2022 ${ZIP_FILE}  ${1}${1:+@}${host}:Solaris
fi

echo Done
echo

# EOF
