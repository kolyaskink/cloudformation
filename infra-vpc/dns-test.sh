#!/bin/bash -x

# Version 1.2

Zone="gamehouseos.com."
ZoneId="Z2OLJMS5MY8APL"
ChangeSet="change-resource-record-sets.json"
RecordValue=$(cat /tmp/outputs-infra.txt | grep DNSName | gawk '{ print $3 }')
RecordName=$(cat /tmp/outputs-infra.txt | grep DNSName | gawk '{ print $2 }' | sed 's/DNSName//g' | tr '[:upper:]' '[:lower:]')

GetRecordValue=$(aws route53 list-resource-record-sets --hosted-zone-id=$ZoneId \
--query "ResourceRecordSets[?Name == '$RecordName.$Zone']" \
| grep Value | sed 's/\"\| //g' | gawk -F: '{ print $2 }')


if [[ "$GetRecordValue" == "$RecordValue" ]]; then echo "Record is already there. Nothing to do" && exit 0
        else
        		cp $WORKSPACE/$GITFOLDER/$ChangeSet /tmp/$ChangeSet
                sed -i "s/ChangeName/$RecordName/g" /tmp/$ChangeSet && \
                sed -i "s/ChangeValue/$RecordValue/g" /tmp/$ChangeSet && \
                aws route53 change-resource-record-sets --hosted-zone-id=$ZoneId \
                --change-batch file:////tmp/$ChangeSet && exit $?
fi
