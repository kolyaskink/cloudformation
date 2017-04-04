#!/bin/bash

#Static variables 
region="us-west-2"
zoneid="Z1Y4RZKMU0CNOZ"
account="777556643132"
batchtemplate="/usr/local/bin/dns/batchfile-update.template"
batchfile="/tmp/route53-batch-change.json"

#EC2's variables 
ip=$(curl http://169.254.169.254/latest/meta-data/local-ipv4)
ec2id=$(curl http://169.254.169.254/latest/meta-data/instance-id)
dnstag=$(aws ec2 describe-tags --region $region --filters \
"Name=resource-id,Values=$ec2id" "Name=key,Values=DNS" | jq '.Tags[0] .Value' | sed 's/\"//g')

#If tag is presented, search for existing A record
if [[ -n $dnstag ]]; then
	recordvalue=$(aws route53 list-resource-record-sets --hosted-zone-id $zoneid \
	| grep -B 4 "$dnstag.$region.$account.gamehouseos.internal." | head -1 | sed 's/\"\| //g' | gawk -F: '{print $2}')
		
		#If A record is there, check that IP is correct, if not - change
		if [[ -n $recordvalue ]]; then
				if [[ "$recordvalue" == "$ip" ]]; then exit 0;
					else
						sed "s/ChangeAction/UPSERT/g; s/ChangeValue/$ip/g; s/ChangeName/$dnstag.$region.$account.gamehouseos.internal./g" \
						$batchtemplate > $batchfile && \
						aws route53 change-resource-record-sets --hosted-zone-id $zoneid \
						--change-batch file://$batchfile && exit 0
				fi
		else
				sed "s/ChangeAction/CREATE/g; s/ChangeValue/$ip/g; s/ChangeName/$dnstag.$region.$account.gamehouseos.internal./g" \
				$batchtemplate > $batchfile && \
				aws route53 change-resource-record-sets --hosted-zone-id $zoneid \
				--change-batch file://$batchfile exit 0

	else

		echo "No dns tag found" && exit 0

fi

exit 1