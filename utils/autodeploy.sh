#!/bin/bash
#set -x


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

# Parse out environment
SCRIPT=$(python -c "import os,sys; print os.path.abspath(sys.argv[1])" ${0})
SCRIPT_DIR=$(cd $(dirname $0) >/dev/null; echo ${PWD})
SCRIPT_NAME=$(basename ${SCRIPT})

# Define and verify version control commands
SVN_CMD=${SVN_CMD:-svn}
SVN_UPDATE=${SVN_UPDATE:-$SVN_CMD update}

# Respoitory setup
REPO_DIR=/cpg/repos/maven/release_repo


# Application globals
SELECTED_ACTION=${3:-deploy}    # Hardcoded action
SELECTED_TARGET=${1}            # Target section in Deploy.properties
SELECTED_REL=${2}               # Release to delpoy (e.g. 1902.0.8)
STACK=a1${LOGNAME:0:1}${LOGNAME:3:2}
STACK_DIR=/cpg/cpo_apps/${STACK}

DEPLOY_TIMEOUT_MILLISECONDS=900000


# Update configurations
${SVN_UPDATE} ${STACK_DIR}/automation


# Other Utilities

usage() {
    cat <<EOF

Application deployment script with command line access.
This sript should be run from the domain's automation directory.

  usage:
    ${0} Deploy_Section Release_Version

EOF
    exit ${1:-99}
}


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
            elif [[ -d {app_path} ]]; then
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

if [[ -z {SELECTED_ACTION} || -z ${SELECTED_TARGET} ]]; then
    usage
fi


# Execute the deployer script
cd ${STACK_DIR}
automation/run_wlst.sh automation/wlst/deployer.py -a ${SELECTED_ACTION} \
    -t ${SELECTED_TARGET} -v ${SELECTED_REL}


# Cleanup old deploys from the managed server exploded artifact directories
for DOMAIN_HOME in /cpg/cpo_apps/${STACK}/${STACK}d?; do
    cleanOldDeployments
done


# EOF
