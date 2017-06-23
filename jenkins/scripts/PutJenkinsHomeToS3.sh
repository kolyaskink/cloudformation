#!/bin/bash

bucket_name="9181961191-infrajenkins"
dir="/var/lib/jenkins"
region="us-west-2"

aws s3 sync /$dir s3://$bucket_name  --region $region --exclude "*/config.xml" --exclude "*/credentials.xml" \
--exclude "config.xml" --exclude "credentials.xml"
