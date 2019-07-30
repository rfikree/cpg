#!/bin/bash

LOG_FILE=${HOME}/rsync.logs/rsync-$(date +%Y%m%d%-$H%M).log


# Synchronize production manifests back to staging
/usr/bin/rsync -azi --no-owner /cpg/repos/deployment_manifests/prd*properties \
    10.237.116.162:/cpg/repos/deployment_manifests 2>&1 >> ${LOG_FILE}

# Synchoronize all manifiests fron staging
/usr/bin/rsync -azi --no-owner 10.237.116.162:/cpg/repos/deployment_manifests/*s \
     /cpg/repos/deployment_manifests 2>&1 >> ${LOG_FILE}

# Sychronize the artifacts from staging
/usr/bin/rsync -azi --delete 10.237.116.162:/cpg/repos/maven/release_repo/ \
    /cpg/repos/maven/release_repo 2>&1 >> ${LOG_FILE}`


# Remove the log file if empty
if [[ ! -s ${LOG_FILE} ]]; then
    rm ${LOG_FILE}
fi

exit

# EOF


[root@l-03382-c5a ~]# crontab -l -u teamcity
# ===========================================================
# rsync release repo from staging to prd cpodeploy:/cpg/repos, Bob Ritchie
#
6,16,26,36,46,56 * * * * /usr/bin/rsync -avz --delete 10.237.116.162:/cpg/repos/maven/release_repo/ /cpg/repos/maven/release_repo/ >> /$HOME/rsync.logs/rsync-log.`date +\%Y\%m\%d\%H\%M` 2>&1
#
# remove rsync.logs over 5 days old
29 19 * * * /usr/bin/find $HOME/rsync.logs/rsync* -ctime +5 -exec rm {} \;
#
# remove rsync.logs where there were no files updated
35 20 * * * /usr/bin/find $HOME/rsync.logs/rsync* -size  -155c -exec rm {} \;
#
# ===========================================================

