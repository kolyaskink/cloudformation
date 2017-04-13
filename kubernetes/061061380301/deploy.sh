#!/bin/bash

aws s3 sync . s3://cf-templates-nb-usw2/kubeclusterinfra/
aws s3 sync components s3://cf-templates-nb-usw2/kubeclusterinfra/components/
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2/kubeclusterinfra/master.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2/kubeclusterinfra/components/containerrepository.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2/kubeclusterinfra/components/elasticsearch.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2/kubeclusterinfra/components/rds.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2/kubeclusterinfra/components/route53.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2/kubeclusterinfra/components/security.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2/kubeclusterinfra/components/vpc.yaml
aws cloudformation create-stack --stack-name=kubeclusterinfra --template-url https://s3.amazonaws.com/cf-templates-nb-usw2/kubeclusterinfra/master.yaml --capabilities CAPABILITY_IAM --parameters file:///mnt/h/Repository/Local/CloudFormation/parameters.json