#!/usr/bin/bash

MANIFEST_BASE=/var/svc/manifest/application
SOURCE_BASE=/cpg/3rdParty/scripts/cpg/manifests

PROFILE_DIR=/cpg/3rdParty/scripts/cpg/profiles
CPG_ALIAS_LOOKUP_FILE=${PROFILE_DIR}/hostname.map
CPG_HOSTNAME=$(egrep -i "^$(hostname)," ${CPG_ALIAS_LOOKUP_FILE})
CPG_HOSTNAME=$(CPG_HOSTNAME##*,}

# Function to update or install configs only if missing or changed
applyManifest() {
	manifest_dir=${MANIFEST_BASE}/${1}
	manifest_src=${SOURCE_BASE}/${2}/${3}
	manifest_dst=${manifest_dir}/${4}
	manifest_name=${4}

	if [ ! -d ${manifest_dir} ]; then
		echo Creating ${manifest_dir}
		mkdir -m 0755 ${manifest_dir}
	fi
	if [ ! -f ${manifest_src} ]; then
		echo FATAL: Source file ${manifest_src} is missing
		return 1
	elif [ ! -f ${manifest_dst} ]; then
		echo Installing: ${manifest_dst}
		cp ${manifest_src} ${manifest_dst}
	elif diff ${manifest_src} ${manifest_dst} >/dev/null; then
		echo ${manifest_dst} is up to datecd
		return 0
	else
		echo Updating: ${manifest_dst}
		cp ${manifest_dst}{,.$(date +%Y%m%dT%H%M)}
		cp ${manifest_src} ${manifest_dst}
	fi

	cd ${manifest_dir}
	if svccfg validate ${manifest_name}; then
		svccfg import ${manifest_name}
	else
		echo ${manifest_name} failed to validate
		return 1
	fi
}


# Define the manifests to apply
case ${CPG_HOSTNAME:-''} in
        *-appadm)
        		epa_manifest="epagent.xml epagent.xml"
                wl_manifest="nodemanagerAppAdm.xml nodemanager.xml"
                ;;
        *-bdt)
        		epa_manifest="epagent.xml epagent.xml"
        		wl_manifest=""
                ;;
        *-blcpo)
        		epa_manifest="epagent.xml epagent.xml"
                wl_manifest="nodemanager1x.xml nodemanager.xml"
                ;;
        *-cpodeploy)
        		epa_manifest="epagentCpodeploy.xml epagent.xml"
        		wl_manifest=""
                ;;
        *-soaz0)
        		epa_manifest="epagent.xml epagent.xml"
                wl_manifest="nodemanager5x.xml nodemanager.xml"
                ;;
        *-soaz1)
        		epa_manifest="epagent.xml epagent.xml"
                wl_manifest="nodemanager6x.xml nodemanager.xml"
                ;;
        *-uicpo)
        		epa_manifest="epagent.xml epagent.xml"
                wl_manifest="nodemanager1x.xml nodemanager.xml"
                ;;
        *-wladm)
        		epa_manifest="epagent.xml epagent.xml"
                wl_manifest="weblogicAdmin.xml weblogic.xml"
                ;;
        *-ws)
        		epa_manifest="epagent.xml epagent.xml"
                wl_manifest="nodemanager3x.xml nodemanager.xml"
                ;;
        *)
        		echo Unknown host ${HOSTNAME} ${CPG_HOSTNAME}
        		exit 99
        		;;
esac

if [[ ${CPG_HOSTNAME%%-*} != dev ]]; then
	applyManifest introscope general ${epa_manifest}
fi
if [[ -n ${wl_manifest} ]]; then
	applyManifest weblogic ${CPG_HOSTNAME%%-*} ${wl_manifest}
fi

# EOF
