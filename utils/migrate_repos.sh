#!/bin/bash

LOG_FILE=${HOME}/rsync_logs/$(date +%Y%m%d%-H%M)

$(
# Synchronize production manifests back to dev/staging
/usr/bin/rsync -azi /cpg/repos/deployment_manifests/prd*properties \
    10.237.116.162:/cpg/repos/deployment_manifests

# Synchoronize all manifiests fron dev/staging
/usr/bin/rsync -azi 10.237.116.162:/cpg/repos/deployment_manifests/ \
     /cpg/repos/deployment_manifests

# Sychronize the artifacts from staging/prodution
/usr/bin/rsync -azi --delete 10.237.116.162:/cpg/repos/maven/release_repo/ \
    /cpg/repos/maven/release_repo/ &> /$HOME/rsync.logs/rsync-log.``

) &> ${LOG_FILE}


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

