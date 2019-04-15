#!/bin/bash
#set -x

####TODO Modify to run from cpg scripts directory

# Report errors
err_report() {
    rc=$?
    echo FATAL: Error at line ${1}; status ${rc}
    exit ${rc}
}

# Debug function
debug() {
    echo DEBUG: $@
}

trap 'error_report() $LINENO' ERR

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
SELECTED_ACTION=redeploy    # Hardcoded action
SELECTED_TARGET=${1}        # Target section in Deploy.properties
SELECTED_REL=${2}		    # Release to delpoy (e.g. 1902.0.8)
SELECTED_BUILD=${SELECTED_REL%.*}
SELECTED_APP=${SELECTED_TARGET}
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
    exit 99
}


# Setup Properties



## Functions

# Handle copies
# Params: FQ_Source, FQ_Destination; FQ = full file path
doCopy() {
    debug doCopy ${1} ${2}
    local COPY_SOURCE=${1}
    local COPY_TARGET=${2}
    local COPY_DIR=${COPY_TARGET%/*}
    if [ ! -f ${COPY_SOURCE} ]; then
        echo 'ERROR: Copy source missing' ${COPY_SOURCE}
        exit 2
    fi

    if [ ! -d ${COPY_DIR} ]; then
        echo 'INFO: Setting up target directory structure'
        [ -f ${COPY_DIR} ] && rm -f ${COPY_DIR}
        mkdir -p ${COPY_DIR}
    fi

    if [ ! -f ${COPY_TARGET} ]; then
        echo "INFO: Copying ${COPY_SOURCE} to ${COPY_TARGET}"
        cp ${COPY_SOURCE} ${COPY_TARGET}
    fi

    if [ ! -f ${COPY_TARGET} ]; then
        echo 'ERROR: Failed copy to ${PWD}/${COPY_TARGET}'
        exit 2
    fi
}

copyBuild() {
    debug copyBuild ${SELECTED_APP} ${SELECTED_REL}
    local appFile=${SELECTED_APP}-${SELECTED_REL}.${SELECTED_APP##*-}
    # Handle -shop and -preview suffixes to artifact names
    if [[ ! ${SELECTED_APP} =~ ar$ ]]; then
        local appBase=${SELECTED_APP%ar-*}ar
        local appSuffix=${SELECTED_APP##*ar-}
        appFile=${appBase}-${SELECTED_REL}-${appSuffix}.${appBase##*-}
    fi
    local REPO_PATH=${REPO_DIR}/${SELECTED_APP}/${SELECTED_BUILD}
    local SRC_FILE=${REPO_PATH}/${appFile}
    local TARGET_BASE=applications/${SELECTED_APP}
    TARGET_PATH=${TARGET_BASE}/${SELECTED_REL}/${SRC_FILE##*/}

    doCopy ${SRC_FILE} ${TARGET_PATH}

    local REMOVABLES=$(ls -1td ${TARGET_BASE}/* | tail -n +5)
    if [ -n "${REMOVABLES}" ]; then
        echo "INFO: Removing old deployments: ${REMOVABLES}"
        echo ${REMOVABLES} | xargs -L1 rm -rf
    fi
}

copyWLLibrary() {
    debug copyWLLibrary ${SELECTED_APP} ${SELECTED_REL}
    if [[ -z ${deployablePath} ]]; then
        local appFile=${SELECTED_APP}-${SELECTED_REL}.war
        local REPO_PATH=${REPO_DIR}/${SELECTED_APP}/${SELECTED_BUILD}
        local SRC_FILE=${REPO_PATH}/${appFile}
        local TARGET_BASE=applications/${SELECTED_APP}
        TARGET_PATH=${TARGET_BASE}/${SELECTED_REL}/${appFile}

        doCopy ${SRC_FILE} ${TARGET_PATH}

        local REMOVABLES=$(ls -1td ${TARGET_BASE}/* | tail -n +5)
        if [ -n "${REMOVABLES}" ]; then
            echo "INFO: Removing old deployments: ${REMOVABLES}"
            echo ${REMOVABLES} | xargs -L1 rm -rf
        fi
    else
        TARGET_PATH=${deployablePath}
    fi
}


processServerLibrary() {
    debug processServerLibrary ${SELECTED_APP} ${SELECTED_REL}
    local REPO_PATH=${REPO_DIR}/${SELECTED_APP}/${SELECTED_BUILD}
    local SRC_FILE=${REPO_PATH}/${SELECTED_APP}-${SELECTED_REL}.jar
    local TARGET_PATH=${TARGET_DIR:-lib}/${SRC_FILE##*/}

    doCopy ${SRC_FILE} ${TARGET_PATH}
    find ${TARGET_PATH} -name ${SELECTED_APP}\* \
        ! -name \*${SELECTED_REL}.jar -print -delete
}

extractResources() {
    debug extractResources ${SELECTED_ENV} ${SELECTED_REL}
    local REPO_PATH=${REPO_DIR}/${SELECTED_ENV}/${SELECTED_BUILD}
    local SRC_FILE=${REPO_PATH}/${SELECTED_ENV}*${SELECTED_REL}.jar
    local RESOURCE_DIR=${envTarget:-classpath-ext}

    [[ -d ${RESOURCE_DIR} ]] || mkdir -p ${RESOURCE_DIR}
    (
        cd ${RESOURCE_DIR}
        jar -xvf ${SRC_FILE} ${envDirectory:-resources}
    )
}

# TODO: verify if this is used - likely obsolete
extractFile() {
    debyg extractFile ${SELECTED_APP} ${SELECTED_CFG}
    local TARGET_SRC=${REPO_DIR}/${SELECTED_APP}/${REPO_DIRECTORY}/${SELECTED_CFG}

    (
        unzip -j ${TARGET_SRC} ${sourceFile} ${sourceFile2}
        mv ${sourceFile##*/} ${targetFile}
        [[ -n ${sourceFile2} ]] && mv ${sourceFile2##*/} ${targetFile2}
    )
}


# Apply changes to WebLogic Domain

invokeDispatcher() {
    local DISPATCH_ACTION=${1:-invalid}
    local DISPATCH_APP=${2:-invalid}
    local DISPATCH_VER=${3:-invalid}
    echo "You have selected the ${DISPATCH_ACTION} action for ${DISPATCH_APP}."

    local JYTHON_DIR=~/.jythonDir
    local JYTHON_CACHE=${JYTHON_DIR}/cache2
    local JYTHON_LOG=${JYTHON_DIR}/jython.log
    if [ ! -d ${JYTHON_CACHE} ]; then
        mkdir -p ${JYTHON_CACHE}
    fi

    export WLST_PROPERTIES="-Dweblogic.security.TrustKeyStore=CustomTrust
    -Dweblogic.security.CustomTrustKeyStoreFileName=/cpg/3rdParty/security/CPGTrust.jks
    -Dweblogic.security.SSL.enableJSSE=true
    -Dweblogic.ssl.JSSEEnabled=true
    -Dweblogic.security.SSL.minimumProtocolVersion=TLSv1.2
    -Dweblogic.security.allowCryptoJDefaultJCEVerification=true
    -Dweblogic.security.allowCryptoJDefaultPRNG=true
    -Dweblogic.security.SSL.ignoreHostnameVerification=true
    -Djdk.tls.client.protocols=TLSv1,TLSv1.1,TLSv1.2"

    # Using JDK version as a proxy for WebLogic version
    case ${jdkVer:-x} in
    jdk1.8)
        #HACK: Use Domain files to get login credentials.
        PROP_ARG=${PROP_FILE},${DOMAIN_PROP_DIR}/Domain.properties.configure
        PROP_ARG=${PROP_ARG},${DOMAIN_PROP_DIR}/Domain.properties

        WLST=${WL_HOME}/../oracle_common/common/bin/wlst.sh
        export CLASSPATH=${JAVA_HOME}/lib/tools.jar
        CLASSPATH=${CLASSPATH}:${WL_HOME}/modules/features/wlst.wls.classpath.jar
        CLASSPATH=${CLASSPATH}:${WL_HOME}/common/wlst/modules/jython-modules.jar
        CLASSPATH=${CLASSPATH}:${WL_HOME}/common/wlst/modules/jython-modules.jar/Lib
        CLASSPATH=${CLASSPATH}:${automation}
        #CLASSPATH=${CLASSPATH}:${automation}/wlst
        #CLASSPATH=${CLASSPATH}:${automation}/wlst/modules
        # TODO: evaluate

        #Dweblogic.wlstHome=<another-directory containing common/wlst>
        #oracle_common/plugins/fmwplatform/actions/standardactions.jar
        #wlserver/modules/com.oracle.webligc.management.scripting.jar

        #WLST="java -Dpython.path=${CLASSPATH}
        WLST="${JAVA_HOME}/bin/java -Dpython.path=${CLASSPATH}
            -Dwlst.offline.log=${HOME}/wlst_offline.log
            -Dweblogic.security.allowCryptoJDefaultJCEVerification=true
            -Dweblogic.security.allowCryptoJDefaultPRNG=true
            -DORACLE_HOME=${BEA_HOME}/oracle_common
            ${WLST_PROPERTIES} weblogic.WLST"
        DISPATCHER=${automation}/wlst/cpo_dispatcher.py
        #   -Dwlst.offline.log=stdout
        ;;
    *)
        PROP_ARG=${PROP_FILE}

        # Required modules for WLST support
        SERVER_MODULES='wls-api.jar weblogic.jar'
        WLST_MODULES='jython-modules.jar jython-modules.jar/Lib .'

        # Setup Classpath
        for module in ${SERVER_MODULES}; do
            SERVER_PATH=${SERVER_PATH}:${WL_HOME}/server/lib/${module}
        done
        for module in ${WLST_MODULES}; do
            WLST_PATH=${WLST_PATH}:${WL_HOME}/common/wlst/modules/${module}
        done

        export CLASSPATH=${JAVA_HOME}/lib/tools.jar
        CLASSPATH=$CLASSPATH}:${SERVER_PATH#:}${WLST_PATH}
        PYTHON_PATH=${CLASSPATH}:${automation}

        #WLST="java -Dpython.path=${automation}/wlst/modules
        WLST="${JAVA_HOME}/bin/java -Dpython.path=${PYTHON_PATH} \
            -Dwlst.offline.log=${JYTHON_LOG} \
            -Dpython.cachedir=${JYTHON_CACHE} \
            ${WLST_PROPERTIES} weblogic.WLST"
        #    org.python.util.jython"
        DISPATCHER=${automation}/wlst/cpo_dispatcher.py
      ;;
    esac

    #set -x
    ${WLST} ${DISPATCHER} \
        propPath=${DOMAIN_PROP_DIR} \
        action=${DISPATCH_ACTION} \
        category=${DISPATCH_APP} \
        appVersion=${DISPATCH_VER} \
        deployablePath=${TARGET_PATH} \
        deployTimeout=${DEPLOY_TIMEOUT_MILLISECONDS} #2>>${JYTHON_DIR}/deploy.err
    #set +x
}

# Safely cleanup temp directories from deployment(s)
cleanupDeploy() {
    debug cleanupDeploy ${DOMAIN_HOME}
    for dir in ${SCRIPT_DIR} ${DOMAIN_HOME}; do
        (cd ${dir}  # Use subshell so shell retains location
        for facesCache in */.faces_cache; do
            if [ -d ${facesCache} ]; then
                rmDir=$(dirname ${facesCache})
                echo "INFO: Removing temporary directory ${dir}/${rmDir}"
                rm -rf ${rmDir}/.faces_cache ${rmDir}/.tld_cache
                rmdir ${rmDir}
            fi
        done)
    done
}

# Deploy an appplications environment config
processAppEnv() {
    debug processAppEnv ${envConfig} - ${envDirectory} - ${envTarget}
    if [[ -n "${envDirectory}" && -n "${envTarget}" ]]; then
        debug proccessAppEnv: ${SELECTED_APP} ${envConfig}
        local SELECTED_ENV=${envConfig}
        extractResources
    else
        echo "ERROR: Skipping enviroment configuration of ${envConfig}"
        echo 'Required variable(s) "envDirectory" and/or "envTarget"'
        echo 'have not been specified'
    fi
}


# Configure the environment: Set BEA_HOME, JAVA_HOME, WL_HOME
configureEnvironment() {
    eval $(egrep '^(jdk|bea)(Path|Ver) *=' \
        ${DOMAIN_PROP_DIR}/Domain.properties | tr -d ' ')
    export BEA_HOME=${beaPath}
    #JAVA_HOME2=${jdkPath}
    local JAVA_BASE=/usr/java
    for JAVA_HOME in $(ls -drt ${JAVA_BASE}/${jdkVer}* 2>/dev/null); do
        : Just finding latest JAVA version
    done
    if [ ! -d ${JAVA_HOME} ]; then
        echo FATAL: ${JAVA_VERSION} is invalid
        exit 2 # No such file or directory
    fi
    export WL_HOME=$(echo ${BEA_HOME}/wlserver*)
    export automation=${DOMAIN_HOME}/automation
    export JAVA_HOME jdkVer
    unset beaPath jdkPath
}


# Perform the requested action (possibly recursively)
processRequest() {
    debug processRequest ${SELECTED_APP}
    cd ${DOMAIN_HOME}
    eval $(gawk '/\['${SELECTED_APP}'\]/ {while \
        (getline && ! /^\[/) {if (! /[-.].*=/) {print;}}}' \
        ${DOMAIN_PROP_DIR}/Deploy.properties)
    local CURRENT_ACTION=${SELECTED_ACTION}
    case "${deploymentType}" in
    deployGroup)
        deploymentType=unknown
        local C=0
        for SELECTED_APP in ${deployGroup}; do
            debug deployGroup: ${deployGroup}
            debug deployGroup $((++COUNT)) ${SELECTED_APP}
            ( processRequest )
        done
        return
        ;;
    deploy|redeploy|sharedLibrary|wlLibrary)
        CURRENT_ACTION=${deploymentType}
        ;;
    fileExtract|resourceRoot|serverLibrary|serverMBean)
        CURRENT_ACTION=${deploymentType}
        ;;
    esac

    debug processRequest ${SELECTED_APP} ${CURRENT_ACTION}
    case ${CURRENT_ACTION} in
    deploy|redeploy)
        copyBuild
        if [ -n "${envConfig}" ]; then
            processAppEnv
        fi
        invokeDispatcher ${CURRENT_ACTION} ${SELECTED_APP} ${SELECTED_REL}
        cleanupDeploy
        ;;
    sharedLibrary)
        copyWLLibrary
        invokeDispatcher deploy ${SELECTED_APP} ${SELECTED_REL}
        ;;
    wlLibrary)
        TARGET_PATH=${deployablePath}
        invokeDispatcher deploy ${SELECTED_APP} ${specVersion}
        ;;
    fileExtract)
        extractFile
        ;;
    resourceRoot)
        SELECTED_ENV=${SELECTED_APP}
        extractResources
        ;;
    serverLibrary)
        TARGET_DIR=lib
        processServerLibrary
        ;;
    serverMBean)
        TARGET_DIR=lib/mbeantypes
        processServerLibrary
        ;;
    *)
        echo "FATAL: Unknown action ${CURRENT_ACTION} selected"
        exit -1
        ;;
    esac
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
            else
                echo INFO: removing ${app_path}
                rm -rf ${app_path}
           fi
        done
    fi
}


## TODO Process both stacks
# Process a stack
function processStacks {
    debug procesStacks
    for domain in d2 d1; do
        DOMAIN_HOME=/cpg/cpo_apps/${STACK}/${STACK}${domain}
        DOMAIN_PROP_DIR=${DOMAIN_HOME}/automation/stacks/${STACK}/${STACK}${domain}

        if grep -q [[]${SELECTED_TARGET}] ${DOMAIN_PROP_DIR}/Deploy.properties; then
            echo INFO: Deploying to ${STACK}${domain}

            # Configure Environment
            debug Calling configureEnvironment
            configureEnvironment

            # Process the request
            debug Calling processRequest
            ( processRequest )

            # Cleanup old deployments
            debug Calling processRequest
            ( cleanOldDeployments )
        fi

    done
}


#### Mainline

if [[ ! -w ${STACK_DIR} ]]; then
    echo FATAL: Unable to write to ${STACK_DIR}
    exit 13     # EACCES Permission denied
fi

# Process the request for all stacks
processStacks


# EOF
