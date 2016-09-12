#! /bin/bash

URL_PATH='/web/iw/admin/JCS.jsp?action=clearAllRegions'

if [[ ${CPG_HOSTNAME} != prd-cpodeploy ]]; then
	echo
	echo This script only runs on prd-cpodeploy
	echo
	exit 1
fi

cat <<EOF

The content cache on all CPCP Production LSCS servers will be flushed.

Has the process been followed?

Please open an incident listing which content has not refreshed as expected.
This should include details on the process followed including a list of
deployments done to deploy the content.  There MUST be at lease two deployments:
- one for the compoents; and
- one for the pages containing the components.

If you don't have evidence of these deployments please cancel this script
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
