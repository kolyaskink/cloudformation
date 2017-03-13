# This is a tempale!


#!/bin/bash

stackname=""
region=""
gitfolder=""


#Let's see if CF stack exist or not

function check_stack_existence {
        aws cloudformation describe-stacks --region=$region --stack-name=$stackname --output=text >/dev/null 2>&1
        if [[ $? -eq 0 ]]; then stack_exist=true; else stack_exist=false; fi
        echo $stack_exist
}

#Let's update CF stack

function update_stack {
        aws cloudformation validate-template --region=$region \
--template-body file:////$WORKSPACE/$gitfolder/template.yaml
        if [[ $? -ne 0 ]]; then echo "Validation error" && exit 1; fi
        aws cloudformation update-stack --region=$region --stack-name=$stackname \
--template-body file:////$WORKSPACE/$gitfolder/template.yaml \
--parameters file:////$WORKSPACE/$gitfolder/parameters.json --capabilities CAPABILITY_IAM
		if [[ $? -ne 0 ]]; then echo "Update has been interrupted" && exit 1; fi
		aws cloudformation wait stack-update-complete --region=$region --stack-name=$stackname 
        if [[ $? -ne 0 ]]; then echo "Update error" && exit 1; \
        else echo "Stack $stackname has been updated"; fi

}

#Let's create a new CF stack

function create_stack {
        aws cloudformation validate-template --region=$region \
--template-body file:////$WORKSPACE/$gitfolder/template.yaml
		if [[ $? -ne 0 ]]; then echo "Validation error" && exit 1; fi
        aws cloudformation create-stack --region=$region --stack-name=$stackname \
--template-body file:////$WORKSPACE/$gitfolder/template.yaml \
--parameters file:////$WORKSPACE/$gitfolder/parameters.json --capabilities CAPABILITY_IAM
		if [[ $? -ne 0 ]]; then echo "Deployment has been nterrupted" && exit 1; fi
		aws cloudformation wait stack-create-complete --region=$region --stack-name=$stackname
        if [[ $? -ne 0 ]]; then echo "Deployment error" && exit 1; \
        else echo "Stack $stackname has been created"; fi
        
}


#Main part starts here

check_stack_existence

if [[ "$stack_exist" == true ]]; then update_stack; else create_stack; fi
exit 0