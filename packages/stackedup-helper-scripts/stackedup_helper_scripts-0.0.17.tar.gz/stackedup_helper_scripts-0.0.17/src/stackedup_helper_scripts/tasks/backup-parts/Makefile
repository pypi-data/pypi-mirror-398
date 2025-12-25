.DEFAULT_GOAL := help

# Set Makefile variables from .env
# https://lithic.tech/blog/2020-05/makefile-dot-env/
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

AWS_ACCOUNT_ID := $$(aws sts get-caller-identity --output text --query 'Account' | tr -d '\r')

# ============================================================================ #
# VARS
# ============================================================================ #

AWS_DEFAULT_REGION ?= us-west-2

BUILD_SHA = $$(git rev-parse HEAD)
BUILD_TIME = $$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BUILD_TAG = $${TAG}

# ============================================================================ #
# HELPERS
# ============================================================================ #

## Command: Variable(s): assume-role: Description
## -------: -----------: -----------: -----------

## help: : : Print this help message
.PHONY: help
help:
	@echo 'Usage:'
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' |  sed -e 's/^/ /'

guard-%:
	@ if [ -z '${${*}}' ]; then echo 'ERROR: variable $* not set' && exit 1; fi

# ============================================================================ #
# BUILD
# ============================================================================ #

## build-images: TAG: : Build the Docker image(s)
.PHONY: build-images
build-images: guard-TAG
	docker build \
		--build-arg=BUILD_SHA=${BUILD_SHA} \
		-t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ombu/task/backup:${TAG} \
		-f Dockerfile.remote .
	@echo "Built ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ombu/task/backup:${TAG}"

## push-images: TAG: yes: Push image(s) to the registry
.PHONY: push-images
push-images: build-images
	aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com
	docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ombu/task/backup:${TAG}

## push-images-authenticated: TAG: : Push image(s) to the registry with an already authroized ECR token
.PHONY: push-images-authenticated
push-images-authenticated: guard-TAG build-images
	@docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ombu/task/backup:${TAG}

# ============================================================================ #
# BUILD LOCAL
# ============================================================================ #

## backup-local-build: : : Build the remote image
.PHONY: backup-local-build
backup-local-build:
	docker build -f Dockerfile . -t backup-task

## backup-local-test: BUCKET: : Bring up local test.
.PHONY: backup-local-test
backup-local-test: guard-BUCKET
	 @docker run --rm -it \
		-e FILE_PATH=/mnt/test \
		-e AWS_DEFAULT_REGION=us-west-2 \
		-e AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
		-e AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
		-e AWS_SESSION_TOKEN=$(AWS_SESSION_TOKEN) \
		-e BACKUP_BUCKET=${BUCKET} \
		-e EXCLUDE=skip_me/*,also_skip_me/* \
		-v "./test-files:/mnt/test" \
		backup-task
