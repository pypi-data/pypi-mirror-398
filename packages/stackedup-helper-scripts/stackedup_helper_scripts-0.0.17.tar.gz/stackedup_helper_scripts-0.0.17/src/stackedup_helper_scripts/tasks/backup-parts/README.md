This container backs up local files in a backup path to a S3 bucket using 
`aws s3 sync`. Before backing up files, the script enforces group ownership and 
file permissions on the back up path. See `backup.sh` for the details.

This container is designed to be used as a task on AWS ECS. A sample task
definition is provided in `task-sample.yaml`.

The image uses the following environment variables:

**Required** 
- FILE_PATH  
    The path to backup
- BACKUP_BUCKET  
    The S3 bucket to sync to

**Optional**  
- EXCLUDE  
        A comma delimited list of paths inside of FILE_PATH to exclude backing up
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION  
    AWS credentials, no needed if the container is ran in an environment 
    otherwise configured access, such as ECS 


Available tasks
---------------

Running `make` will output the list of available tasks

Test the image locally
---------------------

    docker run -e FILE_PATH=/mnt/test \
        -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
        -e BACKUP_BUCKET=mr-test-bucket-what \
        -e EXCLUDE=skip_me/*,also_skip_me/* \
        -v $PWD/test-files:/mnt/test backup-task
        
