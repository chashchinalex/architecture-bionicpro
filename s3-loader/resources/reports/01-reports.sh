#!/bin/bash

BUCKET_NAME="reports" /opt/s3-loader/init-bucket.sh
USER_NAME="reports-user" POLICY_NAME="reports-policy" ACCESS_KEY="reports-access" SECRET_KEY="reports-secret" POLICY_FILE="/opt/s3-loader/resources/reports/reports-policy.json" /opt/s3-loader/init-user.sh