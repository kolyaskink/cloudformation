#!/bin/bash

gitfolder=""
bucket_name="9799998836-cf-templates"
region="us-west-2"

cd $WORKSPACE/$gitfolder/ &&\
aws s3 sync ./components/ s3://$bucket_name/$gitfolder/components/ --region $region

exit $?