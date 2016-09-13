#! /bin/bash

URL_PATH='/web/iw/admin/JCS.jsp?action=clearAllRegions'

if [[ ${CPG_HOSTNAME} != prd-cpodeploy ]]; then
	echo
	echo This script only runs on prd-cpodeploy
	echo
	exit 1
fi

cat <<EOF

The content cache on all CPC Production LSDS servers will be flushed.

Has the VPO content process been followed?

See: http://cpowiki.cpggpc.ca/wiki/index.php/Recycling_OLC_Servers

If you don't have an appropriate instance please cancel this script
in the next 30 seconds.

Ctrl-C to cancel

EOF
sleep 30

for host in prd-a-uicpo prd-b-uicpo prd-c-uicpo; do
	for port in 10301 10302 11301 11302; do
		java URLReader http://${host}.cpggpc.ca:${port}${URL_PATH}
	done
done

# EOF