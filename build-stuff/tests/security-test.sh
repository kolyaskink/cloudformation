#This is a template


#!/bin/bash
# This is very simple security test.
# It's parsing your parameters.json file and search for "SshFrom*" keys.
# Only certain vales allowed


white_list_ip=( "212.67.170.162/32" )
parsed="/tmp/parsed1"
parameters_json="/tmp/parameters.json"


cat $parameters_json | jq -c 'map(select(.ParameterKey | contains("SshFrom")))' | grep -E -o '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?/[0-9][0-9])' > $parsed

for ip in "${white_list_ip[@]}"
        do
                cat $parsed | while read line
                        do
                                if [[ "$ip" != "$line" ]]; then echo "$line is not allowed CIDR" && exit 1; fi
                        done
        done

exit 0
