import boto3
from botocore.exceptions import ClientError

public = 'AKIARCYSPMAXUZLQ5PGR'
secret = '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'

servers = {'us-east-1': 'ami-0a8b4cd432b1c3063',
           'us-east-2': 'ami-0231217be14a6f3ba',
           'us-west-1': 'ami-01163e76c844a2129',
           'us-west-2': 'ami-06cffe063efe892ad',
           'af-south-1': 'ami-0c9530c0167bd0229',
           'ap-east-1': 'ami-05f0c9ef3b5df7af2',
           'ap-southeast-3': 'ami-026f5d12b2bc13847',
           'ap-south-1': 'ami-03fa4afc89e4a8a09',
           'ap-northeast-3': 'ami-0b01a0d777348ca26',
           'ap-northeast-2': 'ami-0f66bf23ed74d9284',
           'ap-southeast-1': 'ami-07f179dc333499419',
           'ap-southeast-2': 'ami-0c635ee4f691a2310',
           'ap-northeast-1': 'ami-03d79d440297083e3',
           'ca-central-1': 'ami-0cd73cc497a2d6e69',
           'eu-central-1': 'ami-04c921614424b07cd',
           'eu-west-1': 'ami-00ae935ce6c2aa534',
           'eu-west-2': 'ami-055c6079e3f65e9ac',
           'eu-south-1': 'ami-088fcfcc77750fd5c ',
           'eu-west-3': 'ami-0d1533530bc7a81ba',
           'eu-north-1': 'ami-00dff27dd99d89d89',
           'me-south-1': 'ami-0e23497a51667b042',
           'sa-east-1': 'ami-0420311e572d1298d'
           }

for region in servers:
    print(region)
    ec2 = boto3.client('ec2', region_name=region, aws_access_key_id=public, aws_secret_access_key=secret)

    response = ec2.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

    try:
        response = ec2.create_security_group(GroupName='bandwidth_02',
                                             Description='for bandwidth testing',
                                             VpcId=vpc_id)
        security_group_id = response['GroupId']
        print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

        data = ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 5201,
                 'ToPort': 5201,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp',
                 'FromPort': 22,
                 'ToPort': 22,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp',
                 'FromPort': 22,
                 'ToPort': 22,
                 'IpRanges': [{'CidrIp': '73.16.241.87/32'}]}
            ])
        print('Ingress Successfully Set %s' % data)
    except ClientError as e:
        print(e)
