#!/bin/bash -x

# Version 2.0

Zone="gamehouseos.com."
ZoneId="Z2OLJMS5MY8APL"
ChangeSet="change-resource-record-sets.json"


cat /tmp/outputs-games.txt | grep DNSName > /tmp/outputs-games.parced

while read line; do
        RecordValue=$(echo $line | grep DNSName | gawk '{ print $3 }')
        RecordName=$(echo $line | grep DNSName | gawk '{ print $2 }' | sed 's/DNSName//g' | tr '[:upper:]' '[:lower:]')
        GetRecordValue=$(aws route53 list-resource-record-sets --hosted-zone-id=$ZoneId \
--query "ResourceRecordSets[?Name == '$RecordName.$Zone']" \
| grep Value | sed 's/\"\| //g' | gawk -F: '{ print $2 }')

        if [[ "$GetRecordValue" == "$RecordValue" ]]; then echo "Record is already there. Nothing to do" && exit 0
        else
                cp $WORKSPACE/$GITFOLDER/$ChangeSet /tmp/$ChangeSet
                sed -i "s/ChangeName/$RecordName/g" /tmp/$ChangeSet && \
                sed -i "s/ChangeValue/$RecordValue/g" /tmp/$ChangeSet && \
                aws route53 change-resource-record-sets --hosted-zone-id=$ZoneId \
                --change-batch file:////tmp/$ChangeSet
        fi

done < /tmp/outputs-games.parced
