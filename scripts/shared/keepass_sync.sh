#!/bin/bash

# Settings
USER_CAPITALIZED="${USER^}"
REMOTE_PATH="/mnt/media"
LOCAL_DB=$HOME/Data/KeePass/$USER_CAPITALIZED.kdbx
REMOTE_DB=$REMOTE_PATH/Data/$USER_CAPITALIZED/KeePass/$USER_CAPITALIZED.kdbx
LOG_FILE=/tmp/$USER_keepass_sync.log

# Params
RSYNC_PARAMS="--update -rltoDz --progress"
WAIT_TIMEOUT=300

sync()
{
    # local to remote
    rsync $RSYNC_PARAMS $LOCAL_DB $REMOTE_DB 2>&1 | tee -a $LOG_FILE

    # remote to local
    rsync $RSYNC_PARAMS $REMOTE_DB $LOCAL_DB 2>&1 | tee -a $LOG_FILE
}

# Remove old log file
rm $LOG_FILE > /dev/null 2>&1

# Force sync
sync

# Sync
while :
do
    # Monitor
    inotifywait $LOCAL_DB -t $WAIT_TIMEOUT -e modify,create,delete 2>&1 | tee -a $LOG_FILE

    # Sync
    sync

    # Sleep
    sleep 5
done

