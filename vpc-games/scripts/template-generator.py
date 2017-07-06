# This script generates CF template for Jenkins stack of CBS project
# Version 1.1
# Kirill k
# This is my Git tests =))

import argparse
import json

from troposphere import Template, Ref, FindInMap, Parameter, Output, Tags, Join, GetAtt
from troposphere.s3 import Bucket
from troposphere.ec2 import SecurityGroup, SecurityGroupIngress
import troposphere.ec2 as ec2
import troposphere.iam as iam
import troposphere.elasticloadbalancing as elb

from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole

t = Template()


# Classes definition
class Input:
    def __init__(self):
        # Parse CLI arguments
        parser = argparse.ArgumentParser(description='Script to generate a CF template for Studios Jenkins.')
        parser.add_argument('--REGION', '-R', action='store', required=True)
        parser.add_argument('--STUDIONAME', '-S', action='store', required=True)
        parser.add_argument('--WINDOWS', '-W', action='store', required=True)
        parser.add_argument('--LINUX', '-L', action='store', required=True)
        parser.add_argument('--MAC', '-M', action='store', required=False)
        parser.add_argument('--PARAMETRS', '-P', action='store', required=True)
        parser.add_argument('--MASTERAMI', '-m', action='store', required=True)
        parser.add_argument('--WINDOWSAMI', '-w', action='store', required=True)
        args = parser.parse_args()

        # Assign aruments to a local variables
        self.Region = args.REGION
        self.STUDIONAME = args.STUDIONAME
        self.Windows = args.WINDOWS
        self.Linux = args.LINUX
        self.Mac = args.MAC
        self.Parametrs = args.PARAMETRS
        self.MASTERAMI = args.MASTERAMI
        self.WINDOWSAMI = args.WINDOWSAMI


class Parametrs:
    def __init__(self):
        # Creating parametrs
        self.VpcId = t.add_parameter(Parameter(
            "VpcId",
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
            Default="t2.small",
        ))
        self.Ec2TypeWindows = t.add_parameter(Parameter(
            "Ec2TypeJenkinsWindows",
            Type="String",
            Default="t2.small",
        ))
        self.WhiteIp1 = t.add_parameter(Parameter(
            "WhiteIp1",
            Type="String",
        ))
        self.WhiteIp2 = t.add_parameter(Parameter(
            "WhiteIp2",
            Type="String",
        ))
        self.GhosSslCert = t.add_parameter(Parameter(
            "GhosSslCert",
            Type="String",
        ))
        self.KeyName = t.add_parameter(Parameter(
            "KeyName",
            Type="AWS::EC2::KeyPair::KeyName",
        ))


class StaticResources:
    def __init__(self, STUDIONAME, PublicSubnet1Id, VpcId, InfraVpcCIDR, GamesVpcCIDR, Ec2TypeMaster,
                 KeyName, WhiteIp1, WhiteIp2, GhosSslCert):
        s = self

        # Creating SGs
        # ELB SG 
        s.SGElbName = STUDIONAME + "SgElb"
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
                    ec2.SecurityGroupRule(
                        IpProtocol="tcp",
                        FromPort="443",
                        ToPort="443",
                        CidrIp=Ref(WhiteIp2),
                    ),
                ],
                VpcId=Ref(VpcId),
                Tags=Tags(
                    Name=s.SGElbName,
                ),
            ))

        # Slave SG
        s.SGWindowsName = STUDIONAME + "SgEc2JenkinsWindows"
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
                        IpProtocol="tcp",
                        FromPort="3389",
                        ToPort="3389",
                        CidrIp=Ref(WhiteIp2),
                    ),
                    ec2.SecurityGroupRule(
                        IpProtocol="icmp",
                        FromPort="-1",
                        ToPort="-1",
                        CidrIp=Ref(GamesVpcCIDR),
                    ),
                ],
                VpcId=Ref(VpcId),
                Tags=Tags(
                    Name=s.SGWindowsName,
                ),
            ))

        # Master SG
        s.SGMasterName = STUDIONAME + "SgEc2JenkinsMaster"
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
                        CidrIp=Ref(InfraVpcCIDR),
                    ),
                    ec2.SecurityGroupRule(
                        IpProtocol="icmp",
                        FromPort="-1",
                        ToPort="-1",
                        CidrIp=Ref(GamesVpcCIDR),
                    ),
                ],
                VpcId=Ref(VpcId),
                Tags=Tags(
                    Name=s.SGMasterName,
                ),
            ))

        # Ingress rules
        s.SGIName = STUDIONAME + "SgIngressMasterSlaves"
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

        s.SGIName = STUDIONAME + "SgIngressSlavesMaster"
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
        s.JenkinsRoleName = STUDIONAME + "JenkinsRole"
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
        s.JenkinsProfileName = STUDIONAME + "InstanceProfileJenkins"
        s.JenkinsProfile = t.add_resource(iam.InstanceProfile(
            s.JenkinsProfileName,
            Path="/",
            Roles=[Ref(s.JenkinsRole)],
        ))

        # Creating Master Jenkins Instance
        s.JenkinsMasterName = STUDIONAME + "JenkinsMaster"
        s.JenkinsMaster = t.add_resource(ec2.Instance(
            s.JenkinsMasterName,
            ImageId=FindInMap("JenkinsMaster", Ref("AWS::Region"), "AMI"),
            InstanceType=Ref(Ec2TypeMaster),
            KeyName=Ref(KeyName),
            SecurityGroupIds=[Ref(s.SGMaster)],
            SubnetId=Ref(PublicSubnet1Id),
            IamInstanceProfile=Ref(s.JenkinsProfile),
            Tags=Tags(
                Name=s.JenkinsMasterName,
                Scheduler="WorkingDays",
            ),
        ))

        # Creating ELB for Jenkins
        s.ElbJenkinsName = STUDIONAME + "ElbJenkins"
        s.ElbJenkins = t.add_resource(elb.LoadBalancer(
            s.ElbJenkinsName,
            Subnets=[Ref(PublicSubnet1Id)],
            LoadBalancerName=s.ElbJenkinsName,
            SecurityGroups=[Ref(s.SGElbName)],
            Scheme="internet-facing",
            Instances=[Ref(s.JenkinsMaster)],
            Listeners=[
                elb.Listener(
                    LoadBalancerPort="443",
                    InstancePort="80",
                    Protocol="HTTPS",
                    SSLCertificateId=Ref(GhosSslCert)
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
        s.s3Name = STUDIONAME + 'S3'
        s.s3 = t.add_resource(Bucket(
            s.s3Name,
            AccessControl="Private",
        ))


class DynamicResources:
    def __init__(self, STUDIONAME, Windows, KeyName, Ec2TypeWindows, SGWindows, PublicSubnet1Id):
        s = self
        # Creating Windows slaves
        s.d = {}
        w = int(Windows)
        for i in range(0, w):
            Number = str(i)
            s.ec2name = STUDIONAME + "JenkinsWindows" + Number
            s.d["Windows{0}".format(i)] = t.add_resource(ec2.Instance(
                s.ec2name,
                ImageId=FindInMap("JenkinsWindows", Ref("AWS::Region"), "AMI"),
                InstanceType=Ref(Ec2TypeWindows),
                KeyName=Ref(KeyName),
                SecurityGroupIds=[Ref(SGWindows)],
                SubnetId=Ref(PublicSubnet1Id),
                Tags=Tags(
                    Name=s.ec2name,
                    Scheduler="WorkingDays",
                ),
            ))
            i += 1


# Functions to call classes
def get_input():
    return Input()


def get_parametrs():
    return Parametrs()


def get_static_resources(STUDIONAME, PublicSubnet1Id, VpcId, InfraVpcCIDR, GamesVpcCIDR,
                         Ec2TypeMaster, KeyName, WhiteIp1, WhiteIp2, GhosSslCert):
    return StaticResources(STUDIONAME, PublicSubnet1Id, VpcId, InfraVpcCIDR, GamesVpcCIDR,
                           Ec2TypeMaster, KeyName, WhiteIp1, WhiteIp2, GhosSslCert)


def get_dynamic_resources(STUDIONAME, Windows, KeyName, Ec2TypeWindows, SGWindows, PublicSubnet1Id):
    return DynamicResources(STUDIONAME, Windows, KeyName, Ec2TypeWindows, SGWindows, PublicSubnet1Id)


# Functions
def create_description(STUDIONAME):
    Description = "Python-generated template for " + STUDIONAME + " studio. Version new Windows AMI"
    t.add_description(Description)


def create_mapping(Region, MASTERAMI, WINDOWSAMI):
    t.add_mapping('JenkinsMaster', {
        Region: {"AMI": MASTERAMI}
    })
    t.add_mapping('JenkinsWindows', {
        Region: {"AMI": WINDOWSAMI}
    })


def get_static_outputs(*argv):
    for arg in argv:
        t.add_output([
            Output(
                arg[1],
                Value=Ref(arg[0]),
                ),
        ])


def get_adhoc_outputs(ElbJenkins, ElbJenkinsName):
    OutputName="DNSName" + ElbJenkinsName
    t.add_output(Output(
        OutputName,
        Value=GetAtt(ElbJenkins, "DNSName")
    ))



def get_dynamic_outputs(d):
    for key in list(d.keys()):
        print(key, d.values)
        t.add_output([
            Output(
                key,
                Value=Ref(d.values),
            ),
        ])


def main():
    i = get_input()
    p = get_parametrs()

    create_description(i.STUDIONAME)
    create_mapping(i.Region, i.MASTERAMI, i.WINDOWSAMI)

    sr = get_static_resources(i.STUDIONAME, p.PublicSubnet1Id, p.VpcId, p.InfraVpcCIDR, p.GamesVpcCIDR,
                             p.Ec2TypeMaster, p.KeyName, p.WhiteIp1, p.WhiteIp2, p.GhosSslCert)
    dr = get_dynamic_resources(i.STUDIONAME, i.Windows, p.KeyName, p.Ec2TypeWindows, sr.SGWindows, p.PublicSubnet1Id)

    get_static_outputs([sr.s3, sr.s3Name], [sr.SGElb, sr.SGElbName], [sr.SGWindows, sr.SGWindowsName],
                       [sr.SGMaster, sr.SGMasterName], [sr.JenkinsRole, sr.JenkinsRoleName],
                       [sr.JenkinsProfile, sr.JenkinsProfileName], [sr.JenkinsMaster, sr.JenkinsMasterName],
                       [sr.ElbJenkins, sr.ElbJenkinsName])

    # get_dynamic_outputs(dr.d)

    get_adhoc_outputs(sr.ElbJenkins, sr.ElbJenkinsName)

    # writes output to a file
    filename = i.STUDIONAME + "-Jenkins.json"
    output = t.to_json()
    with open(filename, 'w') as f:
        f.write(output)

main()
