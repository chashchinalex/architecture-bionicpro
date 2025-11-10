#!/bin/bash

/usr/bin/mc admin user info s3 $USER_NAME &>/dev/null
if [ $? -ne 0 ]; then
    echo "User $USER_NAME does not exist. Adding user..."
    /usr/bin/mc admin user add s3 $USER_NAME $USER_NAME;
    echo "User $USER_NAME added successfully."
else
    echo "User $USER_NAME already exists. No action taken."
fi

/usr/bin/mc admin policy info s3 $POLICY_NAME &>/dev/null
if [ $? -ne 0 ]; then
    echo "Policy $POLICY_NAME does not exist. Adding policy..."
    /usr/bin/mc admin policy create s3 $POLICY_NAME $POLICY_FILE;
    echo "Policy $POLICY_NAME added successfully."
else
    echo "Policy $POLICY_NAME already exists. No action taken."
fi

/usr/bin/mc admin policy attach s3 $POLICY_NAME --user $USER_NAME;

/usr/bin/mc admin accesskey info s3 $ACCESS_KEY &>/dev/null
if [ $? -ne 0 ]; then
    echo "Access key $ACCESS_KEY does not exist. Adding access key..."
    /usr/bin/mc admin accesskey create s3 $USER_NAME --access-key $ACCESS_KEY --secret-key $SECRET_KEY
    echo "Access key $ACCESS_KEY added successfully."
else
    echo "Access key $ACCESS_KEY already exists. No action taken."
fi
