#!/bin/bash

BucketName="8911037875-gamesassets"
GPAccessFile="/home/ec2-user/googlePlayApiAccess.json"
User="fastlane@gamehouse.com"
Pass="Fastlane170"
SnsTopic="arn:aws:sns:us-west-2:777556643132:GamesFastlaneResults"
AwsRegion="us-west-2"
Platform=$1
ProjectName=$2
BundleId=$3

function ExportEnvVar () {
	export FASTLANE_PASSWORD=$Pass
	export LANG=en_US.UTF-8
	export LANGUAGE=en_US:en
}


# Pls send Status, Projectname and Comment to function below. 
function PushToSns () {
	aws sns publish --region=$AwsRegion --topic-arn $SnsTopic --message "Project $2 status is $1: $3"
}

function DeployAndroid () {
	ExportEnvVar
	cd /tmp/$ProjectName/android/
	/usr/local/bin/fastlane supply -p $BundleId --json_key $GPAccessFile --skip_upload_apk > /tmp/FastlaneDeployment.log 2>&1
	if [[ "$?" != 0 ]]; then
		OutputText="Fastlane returned en error"
		echo "ERROR! $OutputText"
		PushToSns ERROR $ProjectName $OutputText
		mv /tmp/FastlaneDeployment.log /tmp/FastlaneDeployment.error 
		tail -30 /tmp/FastlaneDeployment.error
		exit 2
	fi
}

function DeployIOS () {
	ExportEnvVar
	cd /tmp/$ProjectName/ios/
	/usr/local/bin/fastlane deliver -u $User -a $BundleId --force true > /tmp/FastlaneDeployment.log 2>&1
	if [[ "$?" != 0 ]]; then
		OutputText="Fastlane returned en error"
		echo "ERROR! $OutputText"
		PushToSns ERROR $ProjectName $OutputText
		mv /tmp/FastlaneDeployment.log /tmp/FastlaneDeployment.error
		tail -30 /tmp/FastlaneDeployment.error
		exit 2
	fi	
}


# If var is empty - return error
if [[ -z "$ProjectName" ]] || [[ -z "$Platform" ]] || [[ -z "$BundleId" ]]; then 
	OutputText="Some variable is empty"
	echo "ERROR! $OutputText"
	PushToSns ERROR $ProjectName $OutputText
	exit 2
fi

# If folder is not there - print error
Response=$(aws s3 ls "s3://$BucketName/$ProjectName/" | wc -l)
if [[ "$Response" == 0 ]]; then
	OutputText="Folder for project $ProjectName does not exist"
	echo "ERROR! $OutputText"
	PushToSns ERROR $ProjectName $OutputText
	exit 2
fi

# Sync S3 to a temp folder 
aws s3 sync "s3://$BucketName/$ProjectName/" /tmp/$ProjectName/ > /tmp/$ProjectName.log 2>&1

# If sync not ok - print error, delete temp folder and exit
if [[ "$?" != 0 ]]; then
	OutputText="Cant download project $ProjectName from S3"
    echo "ERROR! $OutputText"
    PushToSns ERROR $ProjectName $OutputText
    mv /tmp/$ProjectName.log /tmp/$ProjectName.error
    rm -rf /tmp/$ProjectName
    exit 2
fi

# Deployment
if [[ "$Platform" = "android" ]]; then
	DeployAndroid
elif [[ "$Platform" = "ios" ]]; then
	DeployIOS
else
	OutputText="Wrong platform name."
	echo "$OutputText"
	PushToSns ERROR $ProjectName $OutputText
fi

# Cleaning up
rm -rf /tmp/$ProjectName/
rm -f /tmp/$ProjectName.log
rm -f /tmp/FastlaneDeployment.log
rm -f /tmp/*.png
rm -f /tmp/spaceship*

OutputText="Platform is $Platform; BundleId is $BundleId"
PushToSns SUCCESS $ProjectName $OutputText
exit 0
