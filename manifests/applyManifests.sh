#!/usr/bin/bash

MANIFEST_BASE=/var/svc/manifest
SCRIPT=$(python -c "import os,sys; print os.path.realpath(sys.argv[1])" ${0})
SOURCE_BASE=$(dirname ${SCRIPT})

PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
if [ -f ${CPG_ALIAS_LOOKUP_FILE} ]; then
    export CPG_HOSTNAME=$(egrep    -i "^$(hostname)," ${CPG_ALIAS_LOOKUP_FILE})
    CPG_HOSTNAME=$(echo ${CPG_HOSTNAME} | cut -d, -f2)
    CPG_HOSTNAME=${CPG_HOSTNAME#?-}
else                # Not an OLC host ??
    export CPG_HOSTNAME=$(hostname | tr 'A-Z' 'a-z')
fi

# Function to update or install configs only if missing or changed
applyManifest() {
    manifest_dir=${MANIFEST_BASE}/application/${1}
    manifest_site=${MANIFEST_BASE}/site
    manifest_src=${SOURCE_BASE}/${2}/${3}
    manifest_dst=${manifest_site}/${4}
    manifest_mv=${manifest_dir}/${4}
    manifest_name=${4}

    if [ ! -f ${manifest_src} ]; then
        echo FATAL: Source file ${manifest_src} is missing
        return 1
    elif [ -f ${manifest_mv} ]; then
        echo Need to move: ${manifest_mv}
        cp ${manifest_src} /tmp/${manifest_name}
        perl -pi -e "s|/site/|/${1}/|" /tmp/${manifest_name}
        if ! diff ${manifest_dir}/${manifest_name} ${manifest_mv} >/dev/null; then
            mv /tmp/${manifest_name} ${manifest_mv}
            #cd ${manifest_dir}
            # svccfg import ${manifest_name}
            svcadm restart svc:/system/manifest-import
            return 0
        else
            rm /tmp/${manifest_name}
        fi
        return 1
    elif [ ! -f ${manifest_dst} ]; then
        echo Installing: ${manifest_dst}
        cp ${manifest_src} ${manifest_dst}
    elif diff ${manifest_src} ${manifest_dst} >/dev/null; then
        echo ${manifest_dst} is up to date
        return 0
    else
        echo Updating: ${manifest_dst}
        cp ${manifest_dst}{,.$(date +%Y%m%dT%H%M)}
        cp ${manifest_src} ${manifest_dst}
    fi

    cd ${manifest_site}
    if svccfg validate ${manifest_name}; then
        svccfg import ${manifest_name}
    else
        echo ${manifest_name} failed to validate
        return 1
    fi
}


# Define the manifests to apply
# CPG_HOSTNAME will be the hostname if the map file does not exist.
case ${CPG_HOSTNAME:-''} in
    *-appadm)
        epa_manifest="epagent.xml"
        wl_manifest="nodemanagerAppAdm.xml nodemanager.xml"
        ;;
    *-blwscpo)
        epa_manifest="epagent.xml"
        wl_manifest="nodemanager1x.xml nodemanager.xml"
        ;;
    *-cpodeploy)
        epa_manifest="epagentCpodeploy.xml"
        wl_manifest=""
        ;;
    *-soaz0)
        epa_manifest="epagent.xml"
        wl_manifest="nodemanager5x.xml nodemanager.xml"
        ;;
    *-soaz1)
        epa_manifest="epagent.xml"
        wl_manifest="nodemanager6x.xml nodemanager.xml"
        ;;
    *-uicpo)
        epa_manifest="epagent.xml"
        wl_manifest="nodemanager1x.xml nodemanager.xml"
        ;;
    *-wladm)
        epa_manifest="epagent.xml"
        wl_manifest="weblogicAdmin.xml weblogic.xml"
        ;;
    *)
        echo Unknown host ${HOSTNAME} ${CPG_HOSTNAME}
        exit 99
        ;;
esac


# Apply the standard manifests
if [[ ${CPG_HOSTNAME%%-*} != l-dev ]]; then
    applyManifest introscope general ${epa_manifest} "epagent.xml"
fi
if [[ -n ${wl_manifest} ]]; then
    applyManifest weblogic ${CPG_HOSTNAME%%-*} ${wl_manifest}
fi

# Apply test manifest
if [[ ! -f /usr/local/bin/olctest ]]; then
    cp ${SOURCE_BASE}/general/olctest /usr/local/bin
elif ! diff ${SOURCE_BASE}/general/olctest /usr/local/bin/olctest >/dev/null; then
    cp ${SOURCE_BASE}/general/olctest /usr/local/bin
fi
applyManifest olctest general olctest.xml olctest.xml


# EOF
