#!/bin/bash

LOG_FILE=${HOME}/rsync.logs/rsync-$(date +%Y%m%d-%H%M).log


# Synchronize production manifests back to staging
/usr/bin/rsync -azi --no-owner /cpg/repos/deployment_manifests/prd*properties \
    10.237.116.162:/cpg/repos/deployment_manifests 2>&1 >> ${LOG_FILE}

# Synchoronize all manifiests fron staging
/usr/bin/rsync -azi --no-owner --exclude 'prd*properties' --exclude 'dev*properties'\
    10.237.116.162:/cpg/repos/deployment_manifests/*properties \
    /cpg/repos/deployment_manifests 2>&1 >> ${LOG_FILE}

# Sychronize the artifacts from staging
/usr/bin/rsync -azi --delete 10.237.116.162:/cpg/repos/maven/release_repo/ \
    /cpg/repos/maven/release_repo 2>&1 >> ${LOG_FILE}


# Remove the log file if empty
if [[ ! -s ${LOG_FILE} ]]; then
    rm ${LOG_FILE}
fi

exit

# EOF

