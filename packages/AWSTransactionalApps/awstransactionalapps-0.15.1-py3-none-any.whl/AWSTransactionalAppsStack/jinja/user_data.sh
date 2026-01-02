#!/bin/bash
aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/setup/setup.sh /tmp/setup.sh
chmod +x /tmp/setup.sh
/tmp/setup.sh
