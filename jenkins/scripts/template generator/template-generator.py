import boto3
import argparse
import json
from troposphere import Template, Ref, FindInMap, Base64, Parameter, Join, GetAZs
from troposphere.s3 import Bucket, PublicRead
from troposphere.ec2 import SecurityGroup, SecurityGroupIngress
from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole
import troposphere.ec2 as ec2
import troposphere.iam as iam
import troposphere.elasticloadbalancing as elb



t = Template()


#Classes definition
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

class Parametrs:
    def __init__(self):
        # Creating parametrs
        self.VPCid = t.add_parameter(Parameter(
            "VPCid",
            Type="String",
        ))
        self.PublicSubnet1Id = t.add_parameter(Parameter(
            "PublicSubnet1Id",
            Type="String",
        ))
        self.InfraVpcCIDR = t.add_parameter(Parameter(
            "InfraVpcCIDR",
            Type="String",
        ))
        self.GamesVpcCIDR = t.add_parameter(Parameter(
            "GamesVpcCIDR",
            Type="String",
        ))
        self.Ec2TypeMaster = t.add_parameter(Parameter(
            "Ec2TypeJenkinsMaster",
            Type="String",
        ))
        self.KEYName = t.add_parameter(Parameter(
            "KeyName",
            Type="AWS::EC2::KeyPair::KeyName",
        ))

# Functions to call classes
def GetInput():
    return Input()

def Getparametrs():
    return Parametrs()

# Functions
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

def CreateStaticResources(StudioName, PublicSubnet1Id, VPCid, InfraVpcCIDR, GamesVpcCIDR, Ec2TypeMaster, KEYName):

    # Creating SGs
    # ELB SG
    SGElbName = StudioName + "SgElb"
    SGElb = t.add_resource(
        SecurityGroup(
            SGElbName,
            GroupDescription='Enable access to the Jenkins LB',
            VpcId=Ref(VPCid),
        ))

    # Slave SG
    SGWindowsName = StudioName + "SgEc2JenkinsWindows"
    SGWindows = t.add_resource(
        SecurityGroup(
            SGWindowsName,
            GroupDescription='Jenkins Windows Slave EC2 SG',
            VpcId=Ref(VPCid),
        ))

    # Master SG
    SGMasterName = StudioName + "SgEc2JenkinsMaster"
    SGMaster = t.add_resource(
        SecurityGroup(
            SGMasterName,
            GroupDescription='Jenkins Master EC2 SG',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="80",
                    ToPort="80",
                    SourceSecurityGroupId=Ref(SGElb),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="80",
                    ToPort="80",
                    SourceSecurityGroupId=Ref(SGWindows),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="22",
                    ToPort="22",
                    SourceSecurityGroupId=Ref(InfraVpcCIDR),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="icmp",
                    FromPort="-1",
                    ToPort="-1",
                    CidrIp=Ref(GamesVpcCIDR),
                ),
            ],
            VpcId=Ref(VPCid),
        ))

    # Ingress rules
    SGIName = StudioName + "IngressMasterSlaves"
    t.add_resource(
        SecurityGroupIngress(
            SGIName,
            GroupId=Ref(SGMaster),
            SourceSecurityGroupId=Ref(SGWindows),
            IpProtocol="tcp",
            FromPort="0",
            ToPort="65535",
        )
    )

    # Creating Master Jenkins Role
    JenkinsMasterRoleName = StudioName + "JenkinsMasterRole"
    JenkinsMasterRole = t.add_resource(iam.Role(
        JenkinsMasterRoleName,
        Path="/",
        AssumeRolePolicyDocument=Policy(
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service", ["ec2.amazonaws.com"])
            )
        ]),
        Policies=[
            iam.Policy(
                PolicyName="logs",
                PolicyDocument={
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": "logs:*",
                        "Resource": "arn:aws:logs:*:*:*"
                    }],
                }
            ),
            iam.Policy(
                PolicyName="dnsupdate",
                PolicyDocument={
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [
                            "ec2:DescribeTags",
                            "route53:GetHostedZone",
                            "route53:ListHostedZones",
                            "route53:ListResourceRecordSets",
                            "route53:ChangeResourceRecordSets",
                            "route53:GetChange",
                            ],
                        "Resource": "*"
                    }],
                }
            )
        ],
    ))

    # Creating Master Jenkins Instance Profile
    JenkinsMasterProfileName = StudioName + "InstanceProfileJenkinsMaster"
    JenkinsMasterProfile = t.add_resource(iam.InstanceProfile(
        JenkinsMasterProfileName,
        Path="/",
        Roles=[Ref(JenkinsMasterRole)],
    ))

    # Creating Master Jenkins Instance
    JenkinsMasterName = StudioName + "JenkinsMaster"
    JenkinsMaster = t.add_resource(ec2.Instance(
        JenkinsMasterName,
        ImageId=FindInMap("JenkinsMaster", Ref("AWS::Region"), "AMI"),
        InstanceType=Ref(Ec2TypeMaster),
        KeyName=Ref(KEYName),
        SecurityGroups=[Ref(SGMaster)],
        SubnetId=Ref(PublicSubnet1Id),
        IamInstanceProfile=Ref(JenkinsMasterProfile)
    ))

    # Creating ELB for Jenkins
    ElbJenkinsName = StudioName + "ElbJenkins"
    ElbJenkins = t.add_resource(elb.LoadBalancer(
        ElbJenkinsName,
        Subnets=[Ref(PublicSubnet1Id)],
        SecurityGroups=[Ref(SGElbName)],
        Scheme="internet-facing",
        Instances=[Ref(JenkinsMaster)],
        Listeners=[
            elb.Listener(
                LoadBalancerPort="443",
                InstancePort="80",
                Protocol="HTTPS",
            ),
        ],
        HealthCheck=elb.HealthCheck(
            Target="HTTP:80/static/19c0b418/images/headshot.png",
            HealthyThreshold="3",
            UnhealthyThreshold="5",
            Interval="30",
            Timeout="5",
        )
    ))

    # Creating S3 bucket
    s3Name = StudioName + 'S3'
    t.add_resource(Bucket(s3Name, AccessControl=PublicRead, ))


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



def main():

    i = GetInput()
    p = Getparametrs()

    CreateDescription(i.StudioName)
    CreateMapping(i.Region, i.MasterAMI, i.WindowsAMI)
    CreateStaticResources(i.StudioName, p.PublicSubnet1Id, p.VPCid, p.InfraVpcCIDR, p.GamesVpcCIDR, p.Ec2TypeMaster, p.KEYName)
    CreateDynamicResources(i.Windows, i.StudioName)
    print(t.to_json())

main()