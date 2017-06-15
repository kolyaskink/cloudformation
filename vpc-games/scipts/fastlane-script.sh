#!/bin/bash

BucketAssets="8911037875-gamesassets"
BucketOutput=""
GPAccessFile="/home/ec2-user/googlePlayApiAccess.json"
User="fastlane@gamehouse.com"
Pass="Fastlane170"
SnsTopic="arn:aws:sns:us-west-2:777556643132:GamesFastlaneResults"
AwsRegion="us-west-2"
Platform=$1
ProjectName=$2
BundleId=$3
Parameter=$4

function ExportEnvVar () {
	sudo mount -a
	export FASTLANE_PASSWORD=$Pass
	export LANG=en_US.UTF-8
	export LANGUAGE=en_US:en
}


# Pls send Status, Projectname and Comment to function below. 
function PushToSns () {
	aws sns publish --region=$AwsRegion --topic-arn $SnsTopic --message "Project $2 status is $1: $3"
}


function FastlaneErrorhandler () {
	ErrorFile="/tmp/FastlaneDeploymentError-$(date +%F_%R).txt"
	mv /tmp/FastlaneDeployment.log $ErrorFile

	aws s3 sync --region=$AwsRegion \
	--storage-class REDUCED_REDUNDANCY $ErrorFile "s3://$BucketOutput/$ErrorFile" 

	OutputText="Fastlane returned en error. Pls see logs "
	echo "ERROR! $OutputText"
	PushToSns ERROR $ProjectName "$OutputText"
}

function DeployAndroid () {
	ExportEnvVar
	cd /tmp/$ProjectName/android/
	/usr/local/bin/fastlane supply -p $BundleId --json_key $GPAccessFile --skip_upload_apk $Parameter > /tmp/FastlaneDeployment.log 2>&1
	if [[ "$?" != 0 ]]; then
		FastlaneErrorhandler
		exit 2
	fi
}

function DeployIOS () {
	ExportEnvVar
	cd /tmp/$ProjectName/ios/
	/usr/local/bin/fastlane deliver -u $User -a $BundleId --force true $Parameter > /tmp/FastlaneDeployment.log 2>&1
	if [[ "$?" != 0 ]]; then
		FastlaneErrorhandler
		exit 2
	fi	
}


function PreSyncTests () {

	# If var is empty - return error
	if [[ -z "$ProjectName" || -z "$Platform" || -z "$BundleId" ]]; then 
		OutputText="Some variable is empty"
		echo "ERROR! $OutputText"
		PushToSns ERROR $ProjectName "$OutputText"
		exit 2
	fi

	# Check if any --skip parameter is there
	if [[ -n "$Parameter" &&  ( "$Parameter" == "skip_screenshots" || "$Parameter" == "skip_metadata" ) ]]; then 
			Parameter=$(echo "--$Parameter true")
	elif [[ -z "$Parameter" ]]; then
		echo "It's just empty"
	else
		OutputText="$Parameter is a wrong value"
		echo "ERROR! $OutputText"
		PushToSns ERROR $ProjectName "$OutputText"
		exit 2
	fi

	# If folder is not there - print error
	Response=$(aws s3 ls "s3://$BucketAssets/$ProjectName/" | wc -l)
	if [[ "$Response" == 0 ]]; then
		OutputText="Folder for project $ProjectName does not exist"
		echo "ERROR! $OutputText"
		PushToSns ERROR $ProjectName "$OutputText"
		exit 2
	fi
}

function PostSyncTests () {

	# If sync not ok - print error, delete temp folder and exit
	if [[ "$?" != 0 ]]; then
		OutputText="Cant download project $ProjectName from S3"
    	echo "ERROR! $OutputText"
    	PushToSns ERROR $ProjectName "$OutputText"
    	mv /tmp/$ProjectName.log /tmp/$ProjectName.error
    	rm -rf /tmp/$ProjectName
    	exit 2
	fi
}

function CleanUp () {

	# Cleaning up
	rm -rf /tmp/$ProjectName/
	rm -f /tmp/$ProjectName.log
	rm -f /tmp/FastlaneDeployment.log
	rm -f /tmp/*.png
	rm -f /tmp/spaceship*
}

PreSyncTests

# Sync S3 to a temp folder 
aws s3 sync "s3://$BucketAssets/$ProjectName/" /tmp/$ProjectName/ > /tmp/$ProjectName.log 2>&1

PostSyncTests

# Deployment
if [[ "$Platform" = "android" ]]; then
	DeployAndroid
elif [[ "$Platform" = "ios" ]]; then
	DeployIOS
else
	OutputText="Wrong platform name."
	echo "$OutputText"
	PushToSns ERROR $ProjectName "$OutputText"
fi

CleanUp

OutputText="Platform is $Platform; BundleId is $BundleId"
PushToSns SUCCESS $ProjectName "$OutputText"
exit 0
