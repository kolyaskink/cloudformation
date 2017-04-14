#!/bin/bash

TempFile="/tmp/AssumeRoleToken"
RoleArn="arn:aws:iam::061061380301:role/AdminAccessFromProd"
SessionName="Jenkins-Test"
JenkinsHome="/var/lib/jenkins"

aws sts assume-role --role-arn "$RoleArn" \
--role-session-name "$SessionName" > $TempFile

SecretAccessKey=$(grep "SecretAccessKey" $TempFile | gawk -F:  '{print $2}' | sed 's/\"\| \|,//g' )
AccessKeyId=$(grep "AccessKeyId" $TempFile | gawk -F:  '{print $2}' | sed 's/\"\| \|,//g' )
SessionToken=$(grep "SessionToken" $TempFile | gawk -F:  '{print $2}' | sed 's/\"\| \|,//g' )

mkdir $JenkinsHome/.aws && touch $JenkinsHome/.aws/credentials && touch $JenkinsHome/.aws/config

printf "#This is temporarily file for cross-account access \n" | tee $JenkinsHome/.aws/credentials > $JenkinsHome/.aws/config
echo "[default]" >> $JenkinsHome/.aws/credentials
echo "aws_access_key_id = $AccessKeyId" >> $JenkinsHome/.aws/credentials
echo "aws_secret_access_key = $SecretAccessKey" >> $JenkinsHome/.aws/credentials
echo "aws_session_token = $SessionToken" >> $JenkinsHome/.aws/credentials
echo "[default]" >> $JenkinsHome/.aws/config
echo "region = us-west-2" >> $JenkinsHome/.aws/config
echo "output = json" >> $JenkinsHome/.aws/config
