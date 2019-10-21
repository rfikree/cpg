#! /bin/bash

if [[ $1 == cpc || $2 == web ]]; then
    URL_PATH='/$1/iw/admin/JCS.jsp?action=clearAllRegions'
else
    cat <<EOF

    Usage: $0 cpc|web

    Clears the cache content for all producton servers for the
    specified context root.


EOF
fi

export CLASSPATH=/cpg/3rdParty/scripts/cpg/testing

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
            java URLReader http://${host}.cpggpc.ca:${port}${URL_PATH} \
                &> /dev/null && sleep 10
        done
    done
done

# EOF
