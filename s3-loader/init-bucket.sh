#!/bin/bash

if /usr/bin/mc ls "s3/${BUCKET_NAME}" > /dev/null 2>&1; then
    echo "Bucket '${BUCKET_NAME}' already exists."
else
    # Create the bucket if it doesn't exist
    /usr/bin/mc mb "s3/${BUCKET_NAME}"
    echo "Bucket '${BUCKET_NAME}' created."
fi