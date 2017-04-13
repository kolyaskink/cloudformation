#!/bin/bash

aws s3 sync . s3://cf-templates-nb-usw2-prod/kubeclusterinfra/
aws s3 sync components s3://cf-templates-nb-usw2-prod/kubeclusterinfra/components/
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2-prod/kubeclusterinfra/master.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2-prod/kubeclusterinfra/components/containerrepository.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2-prod/kubeclusterinfra/components/elasticsearch.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2-prod/kubeclusterinfra/components/rds.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2-prod/kubeclusterinfra/components/route53.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2-prod/kubeclusterinfra/components/security.yaml
aws cloudformation validate-template --template-url https://s3.amazonaws.com/cf-templates-nb-usw2-prod/kubeclusterinfra/components/vpc.yaml
aws cloudformation create-stack --stack-name=kubeclusterinfra --template-url https://s3.amazonaws.com/cf-templates-nb-usw2-prod/kubeclusterinfra/master.yaml --capabilities CAPABILITY_IAM --parameters file:///mnt/h/Repository/Local/CloudFormation/parameters.json