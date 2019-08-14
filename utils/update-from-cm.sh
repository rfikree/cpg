#!/bin/bash -u

SCRIPT=$(python -c "import os,sys; print os.path.abspath(sys.argv[1])" ${0})
DIRECTORY=${1:-''}
if [[ -n ${2:-''} ]]; then
    SUMFILE=$(python -c "import os,sys; print os.path.abspath(sys.argv[1])" ${2})
fi

usage() {
    if [[ -n "${@}" ]]; then
        echo
        echo ${@}
    fi

    cat <<EOF

Usage: ${0} [directoty [script-to-run]

Updates the-directory from the configuration manager it uses one.

Returns false if script-to-run is specified and gets updated.

EOF
    exit
}

# Ensure we have GIT installed
if ! which git >/dev/null; then
    echo
    echo WARN: Unable to locate git
    echo
fi

# Checksum the script, if specified, before we update.
if [[ -n ${SUMFILE:-''} ]]; then
    # Ensure we have CkSum installed
    if ! which cksum >/dev/null; then
        echo
        echo WARN: Unable to locate cksum
        echo
        exit
    fi

    CHKSUM_1=$(cksum ${SCRIPT})
fi

# Ensure the directory is updatable
if [[ -z ${DIRECTORY} ]]; then
    usage
elif [[ ! -d ${DIRECTORY} ]]; then
    usage FATAL: Directory ${DIRECTORY} not found
elif [[ ! -w ${DIRECTORY} ]]; then
    usage FATAL: Ubable to update ${DIRECTORY}
else
    cd ${DIRECTORY}
fi

# Do the update and display the status
if [[ -d .git ]]; then
    git pull | egrep '^ [^ ]'
    git status -s
    # Update the version file
    branch=$(git rev-parse --abbrev-ref HEAD)
    shorthash=$(git log --pretty=format:'%h' -n 1)
    revcount=$(git log --oneline | wc -l)
    latesttag=$(git describe --tags --abbrev=0 --always)
    echo "${branch}-${latesttag}-${revcount}-${shorthash}" > git_version

elif [[ -d .svn ]]; then
    svn update | egrep -v '^(Up|At)'
    svn status
    # TODO - Enable this once we have GIT installed
    #cd ..
    #SCRIPT_DIR=$(dirname ${SCRIPT})
    #${SCRIPT_DIR}/switch-to-git.sh ${DIRECTORY}
else
    usage WARNING: Directory ${DIRECTORY} is not using a configuration manager
fi

# Checksum the script, if specified, after the update.
if [[ -n ${SUMFILE:-''} ]]; then
   cd -
   CHKSUM_2=$(cksum ${SCRIPT})
   [[ ${CHKSUM_1} == ${CHKSUM_2} ]]
   exit $?
fi

# EOF
