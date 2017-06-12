#!/bin/bash

SnsTopic="arn:aws:sns:us-west-2:777556643132:GamesFastlaneResults"
AwsRegion="us-west-2"

CurrentVersion=$(gem list --local | grep fastlane | grep -v commander-fastlane \
| sed 's/\,\|(//g' | gawk '{ print $2 }')


function PushToSns () {
	aws sns publish --region=$AwsRegion --topic-arn $SnsTopic --message "$1"
}

function GetUpdate () {
	NewVersion=$(cat ./FastlaneUpdate.log | grep "Successfully installed" | gawk -F- '{ print $2 }')
	if [[ "$NewVersion" == "$CurrentVersion" ]]; then
		exit 0
	else 
		OutputText="New Fastlane version installed. Current version - $NewVersion."
		PushToSns "$OutputText"
		exit 0
	fi		
}

function Installation () {
	gem install fastlane > ./FastlaneUpdate.log 2>&1
	if [[ "$?" != 0 ]]; then
		OutputText="Gem return an error during Fastlane update. You better to take a look."
		PushToSns "$OutputText"
		exit 2
	else GetUpdate
	fi
}


Installation

OutputText="Unexpected error during Fastlane update"
PushToSns "$OutputText"
exit 2