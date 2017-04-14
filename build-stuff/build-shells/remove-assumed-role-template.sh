#!/bin/bash

JenkinsHome="/var/lib/jenkins"
TempFile="/tmp/AssumeRoleToken"

cat /dev/null > $TempFile
rm -rf $JenkinsHome/.aws