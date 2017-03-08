#This is a template!

#!/bin/bash

gitfolder="infra-vpc"
tempale="$WORKSPACE/$gitfolder/template.yaml"
testfile="$WORKSPACE/$gitfolder/test.sh"
parser="$WORKSPACE/$gitfolder/parse_yaml.sh"

chmod +x $WORKSPACE/$gitfolder/test.sh && \
chmod +x $WORKSPACE/$gitfolder/parse_yaml.sh


$testfile $tempale $parser
