#!/bin/bash
# This are very simple tests to check out golven-vpc template.
# Pls send tempate file as the first parameter and parser as the second.

parsed="/tmp/parsed"

cat $1 | $2 > $parsed

#1. Let's see if you have a VPC. 
vpc=$(grep "\"AWS::EC2::VPC\"" $parsed | wc -l)
if [[ "$vpc" -ne 1 ]] ; then
	echo "ERROR! You are tring  to create $vpc VPCs. What's wrong with you?" && exit 2
fi


#2. Let's see if you have at least 2 public and 2 private subnets
countPublicSubnet=$(grep "\"AWS::EC2::Subnet\"" $parsed | gawk -F__ '{print $2}' | grep "PublicSubnet" | uniq | wc -l)
countPrivateSubnet=$(grep "\"AWS::EC2::Subnet\"" $parsed | gawk -F__ '{print $2}' | grep "PrivateSubnet" | uniq | wc -l)

if [[ "$countPublicSubnet" -lt 2 ]] || [[ "$countPrivateSubnet" -lt 2 ]] ; then
    echo "ERROR! Should be 2 private and 2 public subnets. You have $countPrivateSubnet private and $countPublicSubnet public!" && exit 2
fi


#3. Checking if IG has been attached to VPC. We are not cheking if IG has been created, anyway it would violent template.
igvpcatt=$(grep -A 2 "\"AWS::EC2::VPCGatewayAttachment\"" /tmp/parsed | grep -v VPN | gawk -F\" '{print $2}')
igvpcatt=$(echo $igvpcatt | sed 's/ //g')

if [[ "$igvpcatt" != "AWS::EC2::VPCGatewayAttachment!RefInternetGateway!RefVPC" ]] ; then
	echo "ERROR! It looks like you didn't connect IG to VPC" && exit 2
fi



#101. Clean up temp file
cat /dev/null > $parsed


echo "Everything looks good." && exit 0
