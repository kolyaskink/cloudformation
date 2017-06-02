#!/bin/bash

BucketName="8911037875-gamesassets"
GPAccessFile="/home/ec2-user/googlePlayApiAccess.json"
User="fastlane@gamehouse.com"
Pass="Fastlane170"
Platform=$1
ProjectName=$2
BundleId=$3

function DeployAndroid {
	cd /tmp/$ProjectName/android/
	export FASTLANE_PASSWORD=$Pass
	/usr/local/bin/fastlane supply -p $BundleId --json_key $GPAccessFile --skip_upload_apk > /tmp/FastlaneDeployment.log 2>&1
	if [[ "$?" != 0 ]]; then
		echo "ERROR! Fastlane problem"
		mv /tmp/FastlaneDeployment.log /tmp/FastlaneDeployment.error 
		tail -30 /tmp/FastlaneDeployment.error
		exit 2
	fi
}

function DeployIOS {
	cd /tmp/$ProjectName/ios/
	export FASTLANE_PASSWORD=$Pass
	/usr/local/bin/fastlane deliver -u $User -a $BundleId --force true > /tmp/FastlaneDeployment.log 2>&1
	if [[ "$?" != 0 ]]; then
		echo "ERROR! Fastlane problem"
		mv /tmp/FastlaneDeployment.log /tmp/FastlaneDeployment.error
		tail -30 /tmp/FastlaneDeployment.error
		exit 2
	fi	
}


# If var is empty - return error
if [[ -z "$ProjectName" ]] || [[ -z "$Platform" ]] || [[ -z "$BundleId" ]]; then 
	echo "ERROR! Some variable is empty" 
	exit 2
fi

# If folder is not there - print error
Response=$(aws s3 ls "s3://$BucketName/$ProjectName/" | wc -l)
if [[ "$Response" == 0 ]]; then
	echo "ERROR! Folder for project $ProjectName does not exist"
	exit 2
fi

# Sync S3 to a temp folder 
aws s3 sync "s3://$BucketName/$ProjectName/" /tmp/$ProjectName/ > /tmp/$ProjectName.log 2>&1

# If sync not ok - print error, delete temp folder and exit
if [[ "$?" != 0 ]]; then
    echo "ERROR! Cant download project $ProjectName from S3"
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
	echo "Wrong platform name. Fix your typos bitch"
fi

# Cleaning up
rm -rf /tmp/$ProjectName/
rm -f /tmp/$ProjectName.log
rm -f /tmp/FastlaneDeployment.log
rm -f /tmp/*.png
rm -f /tmp/spaceship*

exit 0
