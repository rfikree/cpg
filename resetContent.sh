#! /bin/bash

URL_PATH='/web/iw/admin/JCS.jsp?action=clearAllRegions'
                  
export CLASSPATH=/cpg/3rdParty/scripts/cpg/testing
for JAVA_BIN in /cpg/3rdParty/installs/java/jdk1*/bin; do continue; done
PATH=$JAVA_BIN:$PATH

if [[ ${CPG_HOSTNAME} != prd-cpodeploy ]]; then
	echo
	echo This script only runs on prd-cpodeploy
	echo
	exit 1
fi

cat <<EOF

The content cache on all CPC Production LSDS servers will be flushed.

Has the VPO content update process been followed?

See: http://cpowiki.cpggpc.ca/wiki/index.php/Recycling_OLC_Servers

If you don't have an appropriate incident please cancel this script
in the next 30 seconds.

Ctrl-C to cancel

EOF
sleep 30

for ms in {1..6}; do
	for host in prd-a-uicpo prd-b-uicpo prd-c-uicpo; do
		for stack in 10 11; do
			port=${stack}30${ms}
			java URLReader http://${host}.cpggpc.ca:${port}${URL_PATH}
			sleep 20
		done
	done
done

# EOF
