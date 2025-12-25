#!/bin/sh

# database-dump.sh is a script to create on demand mysql database dumps from
# an ECS service. When the database dump task is request this script will call
# mariadb-dump to create a custom compressed dump file and be uploaded to an
# encrypted S3 bucket. Then the script will notify the configured SNS topic with
# a presigned S3 link.

# Container Environment Variables
# ${APPLICATION_NAME}
# ${AWS_DEFAULT_REGION}
# ${ENVIRONMENT_TYPE}
# ${DB_HOST}
# ${DB_DB}
# ${DB_PW}
# ${DB_USER}
# ${DB_PORT}
# ${NOTIFICATION_ARN}
# ${BUCKET}

set -e

export FILE_NAME="${APPLICATION_NAME}-${ENVIRONMENT_TYPE}-$(date +%F_%H-%M-%S).sql.gz"

aws sns publish --topic-arn ${NOTIFICATION_ARN} --message "gear_icon Started database dump for ${APPLICATION_NAME} instance ${ENVIRONMENT_TYPE}"

echo "mariadb-dump -u -p -h ${DB_HOST} -P ${DB_PORT} --databases ${DB_DB} --skip-ssl --no-tablespaces > /tmp/${FILE_NAME}"

mariadb-dump -u ${DB_USER} -p${DB_PW} -h ${DB_HOST} -P ${DB_PORT} --databases ${DB_DB} --skip-ssl --no-tablespaces | gzip > "/tmp/${FILE_NAME}"

echo "aws s3 cp --sse AES256 "/tmp/${FILE_NAME}" s3://${BUCKET}"

aws s3 cp --sse AES256 "/tmp/${FILE_NAME}" s3://${BUCKET}

echo "export PRE_SIGN_URL=$(aws s3 presign s3://${BUCKET}/${FILE_NAME} --expires-in 7200 --region ${AWS_DEFAULT_REGION})"

export PRE_SIGN_URL=$(aws s3 presign s3://${BUCKET}/${FILE_NAME} --expires-in 7200 --region ${AWS_DEFAULT_REGION})

aws sns publish --topic-arn ${NOTIFICATION_ARN} --subject "white_check_mark_icon Completed database dump for ${APPLICATION_NAME} instance ${ENVIRONMENT_TYPE}" --message "white_check_mark_icon Completed database dump for ${APPLICATION_NAME} instance ${ENVIRONMENT_TYPE}: <a href=\"${PRE_SIGN_URL}\">${FILE_NAME}</a>"

echo "Database dump task completed"
