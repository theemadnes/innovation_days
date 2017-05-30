#!/bin/bash
# Install CWL Agent on Amazon Linux EC2 instance

# get the region
AWS_REGION="$(curl http://169.254.169.254/latest/meta-data/placement/availability-zone)"
AWS_REGION=${AWS_REGION::-1}

# pull down CWL and bootstrap
curl https://s3.amazonaws.com//aws-cloudwatch/downloads/latest/awslogs-agent-setup.py -O
chmod +x ./awslogs-agent-setup.py
./awslogs-agent-setup.py -n -r $AWS_REGION -c s3://innovation-days/cwl_httpd_log.conf
rm awslogs-agent-setup.py
