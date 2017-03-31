#!/bin/bash
# This is very simple security test.
# It's parsing your parameters.json file and search for "SshFrom*" keys.
# Only certain vales allowed


white_list_ip=( "212.67.170.162/32", "159.100.80.174/32" )
parsed="$WORKSPACE/$gitfolder/tmp-parsed1"
varfile="$WORKSPACE/$gitfolder/tmp-varfile"
gitfolder="infra-vpc"
parameters_json="$WORKSPACE/$gitfolder/parameters.json"


cat /dev/null > $parsed
cat /dev/null > $varfile
var=0

cat $parameters_json | jq -c 'map(select(.ParameterKey | contains("SshFrom")))' | \
grep -E -o '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?/[0-9][0-9])' > $parsed

for ip in "${white_list_ip[@]}"
        do
                cat $parsed | while read line
                        do
                                if [[ "$ip" != "$line" ]]; then echo "$line is not allowed CIDR" && var=$(($var+1)) &&\
                                echo $var > $varfile ; fi
                        done
        done

var=$(cat $varfile)
if [[ "$var" -ne "0" ]]; then exit 1; else exit 0; fi