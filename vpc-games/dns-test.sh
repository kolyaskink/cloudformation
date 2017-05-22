#!/bin/bash -x

ChangeSet="change-resource-record-sets.json"
RecordValue=$(cat /tmp/outputs.txt | grep DNSName | gawk '{ print $3 }')
RecordName=$(cat /tmp/outputs.txt | grep DNSName | gawk '{ print $2 }' | sed 's/DNSName//g' | tr '[:upper:]' '[:lower:]')

GetRecordValue=$(aws route53 list-resource-record-sets --hosted-zone-id=Z34FSVFASXMJN9 \
--query "ResourceRecordSets[?Name == '$RecordName.test.gamehouseos.com.']" \
| grep Value | sed 's/\"\| //g' | gawk -F: '{ print $2 }')


if [[ "$GetRecordValue" == "$RecordValue" ]]; then echo "Record is already there. Nothing to do" && exit 0
        else
        		cp $WORKSPACE/$GITFOLDER/$ChangeSet /tmp/$ChangeSet.json
                sed -i "s/ChangeName/$RecordName/g" /tmp/$ChangeSet && \
                sed -i "s/ChangeValue/$RecordValue/g" /tmp/$ChangeSet && \
                aws route53 change-resource-record-sets --hosted-zone-id=Z34FSVFASXMJN9 \
                --change-batch file:////tmp/$ChangeSet && exit $?
fi
