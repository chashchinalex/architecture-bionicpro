#!/bin/bash

/usr/bin/mc alias set s3 http://s3:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD --insecure;

set -e
for script in "$(dirname "$0")"/resources/**/*.sh; do
  sh "$script"
done    