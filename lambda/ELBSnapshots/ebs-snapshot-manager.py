import boto3
import re
import datetime

ec = boto3.client('ec2')
iam = boto3.client('iam')


def lambda_handler(event, context):
    account_ids = list()
    try:
        iam.get_user()
    except Exception as e:
       
        account_ids.append(re.search(r'(arn:aws:sts::)([0-9]+)', str(e)).groups()[1])


    delete_on = datetime.date.today().strftime('%Y-%m-%d')

    filters = [
        { 'Name': 'tag:DeleteOn', 'Values': [delete_on] },
        { 'Name': 'tag:Type', 'Values': ['Automated'] },
    ]
    snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters)

    for snap in snapshot_response['Snapshots']:
        for tag in snap['Tags']:
            if tag['Key'] != 'KeepForever':
                skipping_this_one = False
                continue
            else:
                skipping_this_one = True

        if skipping_this_one == True:
            print "Skipping snapshot %s (marked KeepForever)" % snap['SnapshotId']
            
        else:
            print "Deleting snapshot %s" % snap['SnapshotId']
            ec.delete_snapshot(SnapshotId=snap['SnapshotId'])
            MessageText = "Snapshot %s has been deleted" % snap['SnapshotId']
            client = boto3.client('sns')
            response = client.publish (
                    TopicArn='arn:aws:sns:us-west-2:777556643132:LambdaEBSSnapshots',
                    Message= MessageText
            )