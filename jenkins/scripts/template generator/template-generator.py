import boto3
import argparse
import json
from troposphere import Template, Ref, FindInMap, Base64, Parameter
from troposphere.s3 import Bucket, PublicRead
import troposphere.ec2 as ec2
from troposphere.ec2 import SecurityGroup

t = Template()

class Input:
    def __init__(self):
        # Parse CLI arguments
        parser = argparse.ArgumentParser(description='Script to generate a CF template for Studios Jenkins')
        parser.add_argument('--REGION', '-R', action='store', required=True)
        parser.add_argument('--STUDIONAME', '-S', action='store', required=True)
        parser.add_argument('--WINDOWS', '-W', action='store', required=True)
        parser.add_argument('--LINUX', '-L', action='store', required=True)
        parser.add_argument('--MAC', '-M', action='store', required=False)
        parser.add_argument('--PARAMETRS', '-P', action='store', required=True)
        parser.add_argument('--MasterAMI', '-m', action='store', required=True)
        parser.add_argument('--WindowsAMI', '-w', action='store', required=True)
        args = parser.parse_args()

        #Assign aruments to a local variables
        self.Region = args.REGION
        self.StudioName = args.STUDIONAME
        self.Windows = args.WINDOWS
        self.Linux = args.LINUX
        self.Mac = args.MAC
        self.Parametrs = args.PARAMETRS
        self.MasterAMI = args.MasterAMI
        self.WindowsAMI = args.WindowsAMI

def GetInput():
    return Input()

def CreateDescription(StudioName):
    Description =  "Python-generated template for " + StudioName + " studio"
    t.add_description(Description)

def CreateMapping(Region, MasterAMI, WindowsAMI):

    t.add_mapping('JenkinsMaster', {
        Region: {"AMI": MasterAMI}
    })
    t.add_mapping('JenkinsWindows', {
        Region: {"AMI": WindowsAMI}
    })

def CreateStaticResources(Windows, StudioName):

    # Creating S3 bucket
    s3Name = StudioName + 'S3'
    t.add_resource(Bucket(s3Name, AccessControl=PublicRead, ))

    # Creating SGs for instances
    # Master
    SGMasterName = StudioName + "SgEc2JenkinsMaster"
    t.add_resource(
        SecurityGroup(
            SGMasterName,
            GroupDescription='Jenkins Master EC2 SG',
            VpcId="111",
        ))

    # Slave
    SGWindowsName = StudioName + "SsEc2JenkinsWindows"
    t.add_resource(
        SecurityGroup(
            SGWindowsName,
            GroupDescription='Jenkins Windows Slave EC2 SG',
            VpcId="111",
        ))

def CreateDynamicResources(Windows, StudioName):
    # Creating Windows slaves
    W = int(Windows)
    for i in range(0, W):
        Number = str(i)
        ec2name = StudioName + "JenkinsWindows" + Number
        t.add_resource(ec2.Instance(
            ec2name,
            ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
            InstanceType="t1.micro",
            KeyName="TestKey",
            SecurityGroups=["default"],
            UserData=Base64("80")
        ))
        i += 1



def CreateParameters(Parametrs):
    # Parse CloudFormation parametrs
    with open(Parametrs) as data_file:
        data = json.load(data_file)
        for record in data:
            ParameterKey = (record["ParameterKey"])

            t.add_parameter(Parameter(
                record["ParameterKey"],
                Type="String"
            ))

            # ParameterValue = (record["ParameterValue"])
            # print(ParameterValue)


def main():

    i = GetInput()

    #CreateParameters(i.Parametrs)
    #CreateDescription(i.StudioName)
    #CreateMapping(i.Region, i.MasterAMI, i.WindowsAMI)
    CreateStaticResources(i.Windows, i.StudioName)
    CreateDynamicResources(i.Windows, i.StudioName)
    print(t.to_json())

main()