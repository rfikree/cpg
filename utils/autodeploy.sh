#!/bin/bash
#set -x

# Parse out environment
SCRIPT=$(python -c "import os,sys; print os.path.abspath(sys.argv[1])" ${0})
SCRIPT_DIR=$(cd $(dirname $0) >/dev/null; echo ${PWD})
SCRIPT_NAME=$(basename ${SCRIPT})


# Usage function

usage() {
    cat <<EOF

Application deployment script with command line access.
This script will automatically select he domain's automation directory.

  usage:
    ${0} Deploy_Section Release_Version [Deploy_Options]
    ${0} [deploy|envonly|undeploy] Deploy_Section Release_Version [Deploy_Options]
    ${0} migrate [Source_Stack/Release] [Deploy_Options]

    First option is action which defaults to deploy.

    Deploy_Section is a section from Deploy.properties
    Release_Version is the version being deployed 1907.0.99
    Source_Stack is the user_id from which deployments are being applied
    Relase is the release for which deployments are being applied
    Deploy_Options are additional options to pass to the deployer application

EOF
    exit ${1:-99}
}


# Report errors
error_report() {
    rc=$?
    echo FATAL: Error at line ${1}: status ${rc}
    exit ${rc}
}

# Debug function
debug() {
    : echo DEBUG: $@
}

trap 'error_report ${LINENO}' ERR


# Default source and branch for stg10 through stg13
setupSource() {
    if ! [[ ${LOGNAME} =~ stg1[0-3] ]]; then
        echo FATAL: Default migrate source is valid only for Staging 10-13
        usage 1
    fi

    local source=dev${LOGNAME:3:2}
    if ! [[ -d /cpg/repos/deployment_manifests/${source}.properties ]]; then
        local branch=$(awk '/=/ && $NF ~/[0-9]{4,4}\.[0-9]/ {print $NF}' \
                       /cpg/repos/deployment_manifests/${source}.properties | \
                       sort -u | tail -1)
       branch=${branch%.*}
       SELECTED_OPTIONS="-s ${source} -b ${branch}"
    else
        echo FATAL: Properties file not found for ${source}
        usage 1
    fi
}


# Respoitory setup
REPO_DIR=/cpg/repos/maven/release_repo

# Application globals
case ${1} in
  deploy|envonly|undeploy)
    SELECTED_ACTION=${1}
    shift
    SELECTED_OPTIONS="-t ${1} -v ${2}"
    shift; shift
    ;;
  migrate)
    SELECTED_ACTION=${1}
    shift
    if [[ ${#} -eq 0 || ${1:-} =~ ^- ]]; then
        setupSource
    else
        SELECTED_OPTIONS="-s ${1}"
        shift
    fi
    ;;
  h*|H*)
    usage
    ;;
  *)
    SELECTED_ACTION=deploy
    SELECTED_OPTIONS="-t ${1} -v ${2}"
    shift; shift
    ;;
esac

EXTRA_OPTIONS=${@}              # Save remaining command line options

# Ensure CPG_LOGINAME is configured
if [[ -z ${CPG_LOGNAME:-''} ]]; then
    if [[ ${LOGNAME} =~ ^(dev|stg|prd|loc)[156][0-9]$ ]]; then
        export CPG_LOGNAME=${LOGNAME}
    else
        DEFAULTS="loc10:a1l10 dev11:a1d11 stg11:a1s11 prd10:a1p10"
        for default in ${DEFAULTS}; do
            if [[ -r /cpg/cpo_apps/${default#*:} ]]; then
                echo INFO: Using default stack ${default%:*} '('${default#*:}')'
                export CPG_LOGNAME=${default%:*}
                break
            fi
        done
        unset default DEFAULTS
    fi
fi
if [[ -z ${CPG_LOGNAME:-''} ]]; then
    echo "WARNING: unable to find usable stack"
    usage
fi


STACK=a1${CPG_LOGNAME:0:1}${CPG_LOGNAME:3:2}
STACK_DIR=/cpg/cpo_apps/${STACK}
automation=${STACK_DIR}/automation

if [[ -z ${automation} || ! -w ${automation} ]]; then
    echo 'FATAL: This script must be run as a stack user'
    exit 99
fi
${SCRIPT_DIR}/update-from-cm.sh ${automation}


# Remove old exploded applications from server directories
function cleanOldDeployments {
    debug cleanOldDeployments ${DOMAIN_HOME}
    cd ${DOMAIN_HOME}
    local config=config/config.xml

    if [ -f ${config} ]; then
        for app_path in servers/a1*/tmp/_WL_user/*[ew]ar*; do
            local app_name=${app_path##*/}
            local app_base=${app_name%_*}
            local app_version=${app_name#*_}

            if grep -q ${app_base}.${app_version} ${config}; then
                debug Found ${app_path}
                continue
            elif [[ -d ${app_path} ]]; then
                echo INFO: removing ${app_path}
                rm -rf ${app_path}
            fi
        done
    fi
}


#### Mainline

if [[ ! -w ${STACK_DIR} ]]; then
    echo FATAL: Unable to write to ${STACK_DIR}
    usage    # EACCES Permission denied
fi

if [[ -z ${SELECTED_ACTION} || -z ${SELECTED_OPTIONS} ]]; then
    usage
fi


# Execute the deployer script
cd ${STACK_DIR}
automation/run_wlst.sh automation/wlst/deployer.py -a ${SELECTED_ACTION} \
    ${SELECTED_OPTIONS} ${EXTRA_OPTIONS}
STATUS=$?


# Cleanup old deploys from the managed server exploded artifact directories
for DOMAIN_HOME in /cpg/cpo_apps/${STACK}/${STACK}d?; do
    cleanOldDeployments
done


# Exit with status
exit ${STATUS}


# EOF
