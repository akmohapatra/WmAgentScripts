#!/bin/bash
SCRIPT="$1"
echo "EXE $SCRIPT"
export X509_USER_PROXY=/tmp/x509up_u50337
echo "------------------------- $(date)" > /afs/cern.ch/user/c/cmst2/mc/logs/$SCRIPT.log.tmp && (/usr/bin/python2.6 /afs/cern.ch/user/c/cmst2/mc/cron/$SCRIPT.py >> /afs/cern.ch/user/c/cmst2/mc/logs/$SCRIPT.log.tmp 2>&1 ) && (cat /afs/cern.ch/user/c/cmst2/mc/logs/$SCRIPT.log.tmp >> /afs/cern.ch/user/c/cmst2/mc/logs/$SCRIPT.log ) && rm -f /afs/cern.ch/user/c/cmst2/mc/logs/$SCRIPT.log.tmp 

