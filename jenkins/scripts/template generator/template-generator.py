import boto3
import argparse
import json

from troposphere import Template, Ref, FindInMap, Base64, Parameter, Join, GetAZs
from troposphere.s3 import Bucket, PublicRead
from troposphere.ec2 import SecurityGroup, SecurityGroupIngress
import troposphere.ec2 as ec2
import troposphere.iam as iam
import troposphere.elasticloadbalancing as elb

from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole



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
        self.Ec2TypeWindows = t.add_parameter(Parameter(
            "Ec2TypeJenkinsWindows",
            Type="String",
        ))
        self.WhiteIp1 = t.add_parameter(Parameter(
            "WhiteIp1",
            Type="String",
        ))
        self.KEYName = t.add_parameter(Parameter(
            "KeyName",
            Type="AWS::EC2::KeyPair::KeyName",
        ))

class StaticResources:
    def __init__(self, StudioName, PublicSubnet1Id, VPCid, InfraVpcCIDR, GamesVpcCIDR, Ec2TypeMaster, KEYName, WhiteIp1):
        s = self

        # Creating SGs
        # ELB SG
        s.SGElbName = StudioName + "SgElb"
        s.SGElb = t.add_resource(
        SecurityGroup(
            s.SGElbName,
            GroupDescription='Enable access to the Jenkins LB',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="443",
                    ToPort="443",
                    CidrIp=Ref(WhiteIp1),
                ),
            ],
            VpcId=Ref(VPCid),
        ))

        # Slave SG
        s.SGWindowsName = StudioName + "SgEc2JenkinsWindows"
        s.SGWindows = t.add_resource(
        SecurityGroup(
            s.SGWindowsName,
            GroupDescription='Jenkins Windows Slave EC2 SG',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="3389",
                    ToPort="3389",
                    CidrIp=Ref(WhiteIp1),
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

        # Master SG
        s.SGMasterName = StudioName + "SgEc2JenkinsMaster"
        s.SGMaster = t.add_resource(
        SecurityGroup(
            s.SGMasterName,
            GroupDescription='Jenkins Master EC2 SG',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="80",
                    ToPort="80",
                    SourceSecurityGroupId=Ref(s.SGElb),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="80",
                    ToPort="80",
                    SourceSecurityGroupId=Ref(s.SGWindows),
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
        s.SGIName = StudioName + "IngressMasterSlaves"
        t.add_resource(
            SecurityGroupIngress(
            s.SGIName,
            GroupId=Ref(s.SGMaster),
            SourceSecurityGroupId=Ref(s.SGWindows),
            IpProtocol="tcp",
            FromPort="0",
            ToPort="65535",
            )
        )

        s.SGIName = StudioName + "IngressSlavesMaster"
        t.add_resource(
            SecurityGroupIngress(
            s.SGIName,
            GroupId=Ref(s.SGWindows),
            SourceSecurityGroupId=Ref(s.SGMaster),
            IpProtocol="tcp",
            FromPort="0",
            ToPort="65535",
            )
        )


        # Creating Jenkins Role
        s.JenkinsRoleName = StudioName + "JenkinsRole"
        s.JenkinsRole = t.add_resource(iam.Role(
            s.JenkinsRoleName,
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

        # Creating Jenkins Instance Profile
        s.JenkinsProfileName = StudioName + "InstanceProfileJenkins"
        s.JenkinsProfile = t.add_resource(iam.InstanceProfile(
            s.JenkinsProfileName,
            Path="/",
            Roles=[Ref(s.JenkinsRole)],
        ))

        # Creating Master Jenkins Instance
        s.JenkinsMasterName = StudioName + "JenkinsMaster"
        s.JenkinsMaster = t.add_resource(ec2.Instance(
            s.JenkinsMasterName,
            ImageId=FindInMap("JenkinsMaster", Ref("AWS::Region"), "AMI"),
            InstanceType=Ref(Ec2TypeMaster),
            KeyName=Ref(KEYName),
            SecurityGroups=[Ref(s.SGMaster)],
            SubnetId=Ref(PublicSubnet1Id),
            IamInstanceProfile=Ref(s.JenkinsProfile)
        ))

        # Creating ELB for Jenkins
        s.ElbJenkinsName = StudioName + "ElbJenkins"
        s.ElbJenkins = t.add_resource(elb.LoadBalancer(
            s.ElbJenkinsName,
            Subnets=[Ref(PublicSubnet1Id)],
            SecurityGroups=[Ref(s.SGElbName)],
            Scheme="internet-facing",
            Instances=[Ref(s.JenkinsMaster)],
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
        s.s3Name = StudioName + 'S3'
        s.s3 = t.add_resource(Bucket(
            s.s3Name,
            AccessControl = "Private",
        ))




class DynamicResources:
    def __init__(self, StudioName, Windows, KEYName, Ec2TypeWindows, SGWindows):
        s = self
        # Creating Windows slaves
        W = int(Windows)
        for i in range(0, W):
            Number = str(i)
            s.ec2name = StudioName + "JenkinsWindows" + Number
            t.add_resource(ec2.Instance(
                s.ec2name,
                ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
                InstanceType=Ref(Ec2TypeWindows),
                KeyName=Ref(KEYName),
                SecurityGroups=[Ref(SGWindows)],
                UserData=Base64("80")
            ))
            i += 1




# Functions to call classes
def GetInput():
    return Input()

def GetParametrs():
    return Parametrs()

def GetStaticResources(StudioName, PublicSubnet1Id, VPCid, InfraVpcCIDR, GamesVpcCIDR, Ec2TypeMaster, KEYName, WhiteIp1):
    return StaticResources(StudioName, PublicSubnet1Id, VPCid, InfraVpcCIDR, GamesVpcCIDR, Ec2TypeMaster, KEYName, WhiteIp1)

def GetDynamicResources(StudioName, Windows, KEYName, Ec2TypeWindows, SGWindows):
    return DynamicResources(StudioName, Windows, KEYName, Ec2TypeWindows, SGWindows)





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





def main():

    i = GetInput()
    p = GetParametrs()


    CreateDescription(i.StudioName)
    CreateMapping(i.Region, i.MasterAMI, i.WindowsAMI)


    sr = GetStaticResources(i.StudioName, p.PublicSubnet1Id, p.VPCid, p.InfraVpcCIDR, p.GamesVpcCIDR, p.Ec2TypeMaster, p.KEYName, p.WhiteIp1)
    dr = GetDynamicResources(i.StudioName, i.Windows, p.KEYName, p.Ec2TypeWindows, sr.SGWindows)

    print(t.to_json())

main()