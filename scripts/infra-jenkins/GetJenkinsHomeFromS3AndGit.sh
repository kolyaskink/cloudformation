#!/bin/bash

dir="/var/lib"
url="git@bitbucket.org:gamehouse-dev/infrajenkins.git"
bucket="9181961191-infrajenkins"
region="us-west-2"

mkdir $dir/jenkins && chown jenkins:jenkins $dir/jenkins && ln -s $dir/jenkins $dir/infrajenkins
cd $dir && git clone $url
aws s3 sync s3://$bucket $dir/infrajenkins/ --region $region
chown -R jenkins:jenkins $dir/jenkins
/etc/init.d/jenkins restart