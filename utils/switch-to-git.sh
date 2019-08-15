#!/bin/bash

DIRECTORY=${1:-''}
URL_BASE='MYYUX://wvzE-nq7-1JGQLNH-nob:vAKEvjDq%xz@LNY.HULLUH.HF'
URL_BASE=$(echo ${URL_BASE} | tr 'A-Z0-9a-z' '5-9a-zA-Z0-4')
GIT_URL_BASE=${URL_BASE}/scm/devcoe-weblogic-automation
GIT_URL_BASE=${2:-$GIT_URL_BASE}

usage() {
    if [[ -n "${@}" ]]; then
        echo
        echo ${@}
    fi

    cat <<EOF

Usage: ${0} [repository] [repository_url_base]

    repository: Name of the repository to be pulled. It will be pulled
        to a sub-directory of the same name.
    repository_url_base: URL path up to the repository name.

    Replaces directory checked out from SVN with the same directory
    checked out from GIT. Run this script from the parent directory
    of the directory checked out from SVN. The old directory will be
    renamed with a ".svn" suffix after the directory is cloned from GIT.

    If the specified directory does not exist, it will
    be pulled from GIT and no SVN related activities will occur.

EOF
    exit 99
}

# Remove configuraton files for other stacks and enviroments
trim_automation() {
    # Skip if we aren't running as service account
    if ! [[ ${LOGNAME} =~ ^(dev|loc|stg|prd)[1-5][0-9]$ ]]; then
        return
    fi

    echo
    echo INFO: Trimming stack configuration tree
    echo

    cd automation/stacks
    PREFIX=a${CPG_LOGNAME:3:1}${CPG_LOGNAME:0:1}
    #echo PREFIX ${PREFIX}

    for dir in *; do
        if ! [[ ${dir} =~ ${PREFIX}[1-5][0-9] ]]; then
            echo Removing configuration for: ${dir}
            git update-index --assume-unchanged ${dir}/*/*
            rm ${dir}/*/*
        fi
    done

    find . -depth -empty -delete
    echo
}

# Check for and parse the specified directory
if [[ -z ${DIRECTORY} ]]; then
    usage
fi
DIRECTORY=$(python -c "import os,sys; print os.path.abspath(sys.argv[1])" ${DIRECTORY})
PARENT=$(dirname ${DIRECTORY})
REPO_DIR=$(basename ${DIRECTORY})
GIT_URL=${GIT_URL_BASE}/${REPO_DIR}.git


# Ensure we have GIT installed
if ! which git >/dev/null; then
    echo
    echo WARN: Unable to locate git
    echo
fi


# Ensure we can access git repoisitoy
if ! git ls-remote -q -h ${GIT_URL} > /dev/null; then
    echo FATAL: Can not reach GIT repository
    exit
fi


# Check the parent directory
if [[ -z ${PARENT} ]]; then
    usage
elif [[ ! -d ${PARENT} ]]; then
    usage FATAL: Directory ${PARENT} was not found
elif [[ ! -w ${PARENT} ]]; then
    usage FATAL: Ubable to update ${PARENT}
else
    cd ${PARENT}

fi


# Setup clone command
if ! [[ ${CPG_HOSTNAME:-''} =~ (stg|prd)-cpodeploy ]]; then
    echo INFO: Cloning dev branch
    CLONE='git clone -q --branch develop'
else
    CLONE='git clone -q --branch master'
fi


# Process the requested directory, if possible
if [[ ! -d ${REPO_DIR} ]]; then
    echo INFO: Doing initial checkout of ${REPO_DIR}
    ${CLONE} ${GIT_URL} ./${REPO_DIR}
    chmod go-rwx ${REPO_DIR}/.git ${REPO_DIR}/.git/config

elif [[ -d ${REPO_DIR}/.git ]]; then
    echo INFO: Directory ${REPO_DIR} has already been updated
    exit

elif [[ -d ${REPO_DIR}/.svn ]]; then
    echo
    echo INFO: Replacing ${REPO_DIR} with version from GIT

    if ${CLONE} ${GIT_URL} ./${REPO_DIR}.new; then
        mv ${REPO_DIR}{,.svn}
        mv ${REPO_DIR}{.new,}
        chmod go-rwx ${REPO_DIR}/.git ${REPO_DIR}/.git/config
    else
        echo
        echo FATAL: Initial pull of ${REPO_DIR} failed
        exit
    fi
    echo

else
    usage FATAL: ${REPO_DIR} is not under configuration management
    exit
fi

if [[ ${REPO_DIR} = automation ]]; then
    trim_automation
fi


# EOF
