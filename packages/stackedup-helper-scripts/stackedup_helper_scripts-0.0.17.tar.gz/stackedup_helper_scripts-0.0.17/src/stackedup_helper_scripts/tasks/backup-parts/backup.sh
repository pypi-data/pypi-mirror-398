#!/bin/sh

# This script backs up local files in a backup path to a S3 bucket using 
# `aws s3 sync`. Before backing up files, the script enforces group ownership 
# and file permissions on the back up path.

# Container Environment Variables
# ${FILE_PATH}
# ${EXCLUDE}
# ${BACKUP_BUCKET}

set -e

echo "Backup task started"

if [ -z "${FILE_PATH}" ]; then
  echo "Backup task failed"
  exit 1
fi

exclude_paths=""
if [ -n "${EXCLUDE}" ]; then
  exclude_paths="--exclude ${EXCLUDE//,/ --exclude }"
fi

if [ "${BACKUP_BUCKET}" ]; then
  aws s3 sync --delete --sse AES256 ${exclude_paths} ${FILE_PATH} s3://${BACKUP_BUCKET}
fi

echo "Backup task completed"
