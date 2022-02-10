import socket
import time
import boto3
import paramiko
import datetime
from geopy.distance import geodesic as gd


def main():
    access_key =
    secret_key =

    servers = {'us-east-1': ['ami-0a8b4cd432b1c3063', 'sg-024f8a033f5d4499e', (38.8051, -77.0470)],
               'us-east-2': ['ami-0231217be14a6f3ba', 'sg-039cdf5305a9721de', (40.4173, -82.9071)],
               'us-west-1': ['ami-01163e76c844a2129', 'sg-034e8622c6d9e9a87', (38.8374, -120.8958)],
               'us-west-2': ['ami-06cffe063efe892ad', 'sg-0e052facfd34bcdfa', (43.8041, -120.5542)],
               'ap-south-1': ['ami-03fa4afc89e4a8a09', 'sg-01515a9f3319bf590', (33.9249, 18.4241)],
               'ap-northeast-3': ['ami-0b01a0d777348ca26', 'sg-06f31a1f12fcef2c1', (34.6937, 135.5023)],
               'ap-northeast-2': ['ami-0f66bf23ed74d9284', 'sg-05f7189e1141ae0a4', (37.5665, 126.9780)],
               'ap-southeast-1': ['ami-07f179dc333499419', 'sg-0da7f917d95d06e03', (1.2903, 103.8520)],
               'ap-southeast-2': ['ami-0c635ee4f691a2310', 'sg-0d3d22e2796f6bea2', (-33.8688, 151.2093)],
               'ap-northeast-1': ['ami-03d79d440297083e3', 'sg-0a823ba5460a12953', (35.6762, 139.6503)],
               'ca-central-1': ['ami-0cd73cc497a2d6e69', 'sg-071c4854867207c21', (44.8280, -79.6345)],
               'eu-central-1': ['ami-04c921614424b07cd', 'sg-06962833ab1e49e0d', (50.1109, 8.68)],
               'eu-west-1': ['ami-00ae935ce6c2aa534', 'sg-08d1b87850b51329d', (53.1424, -7.6921)],
               'eu-west-2': ['ami-055c6079e3f65e9ac', 'sg-0d62a093d51b5ea12', (51.5072, -0.1276)],
               'eu-west-3': ['ami-0d1533530bc7a81ba', 'sg-04d12621c6ee5b388', (48.8566, 2.3522)],
               'sa-east-1': ['ami-0420311e572d1298d', 'sg-0d1aa3eb5fb2fcded', (-23.5558, -46.6396)]
               }

    with open('bandwidth_output.csv', 'w') as file:
        file.write('region1, region2, sender bandwidth, receiver bandwidth, distance (km), time, date\n')

    for region1 in servers:
        for region2 in servers:
            print(f'iperf3 test between {region1} and {region2}')
            sender_bandwidth, receiver_bandwidth = calculate_bandwidth(region1, servers[region1][0], region2,
                                                                       servers[region2][0], servers[region1][1],
                                                                       servers[region2][1], access_key, secret_key)
            print(sender_bandwidth[0], receiver_bandwidth[0])
            distance = gd(servers[region1][2], servers[region2][2]).km
            print(distance)
            with open('bandwidth_output.csv', 'a') as file:
                file.write(f'{region1}, {region2}, {sender_bandwidth[0]}, {receiver_bandwidth[0]}, {distance}, '
                           f'{datetime.datetime.now().strftime("%H:%M:%S")},'
                           f'{datetime.datetime.now().strftime("%m/%d/%Y")}\n')


def create_instance(region: str, image_id: str, sg: str, public: str, secret: str):
    ec2_client = boto3.client('ec2', region_name=region, aws_access_key_id=public, aws_secret_access_key=secret)
    response = ec2_client.run_instances(
        InstanceType='t2.micro',
        MaxCount=1,
        MinCount=1,
        ImageId=image_id,
        KeyName=region,
        SecurityGroupIds=[sg]
    )
    instance_id = response["Instances"][0]["InstanceId"]
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    return response


def terminate_instance(region: str, instance_id: str, public: str, secret: str):
    ec2_client = boto3.client('ec2', region_name=region, aws_access_key_id=public, aws_secret_access_key=secret)
    response = ec2_client.terminate_instances(InstanceIds=[instance_id])


def ssh_to_ec2(ip: str, key_pair: str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while True:
        try:
            ssh.connect(ip, port=22, username='ec2-user',
                        key_filename=f"D:\Documents\Classes\Year 4\ECE 499Y\EC2\{key_pair}.pem")
            break
        except Exception:
            print('Could not reconnect. Retrying...')
    return ssh


def run_command(ssh, cmd: str, timeout: int):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        output = stdout.readlines()
        print(output)
        return output
    except socket.timeout or paramiko.ssh_exception.SSHException:
        print('took a while')
        pass
    return stdout


def calculate_bandwidth(region1: str, image_id1: str, region2: str, image_id2: str, sg1: str, sg2: str,
                        public: str, secret: str):
    receiver_instance = create_instance(region1, image_id1, sg1, public, secret)
    #time.sleep(5)
    sender_instance = create_instance(region2, image_id2, sg2, public, secret)

    receiver_id = receiver_instance["Instances"][0]["InstanceId"]
    sender_id = sender_instance["Instances"][0]["InstanceId"]

    region1_resources = boto3.resource(service_name='ec2',
                                       region_name=region1,
                                       aws_access_key_id=public,
                                       aws_secret_access_key=secret)

    region2_resources = boto3.resource(service_name='ec2',
                                       region_name=region2,
                                       aws_access_key_id=public,
                                       aws_secret_access_key=secret)

    for i in region1_resources.instances.all():
        if i.id == receiver_id:
            receiver_ip = i.public_ip_address
    #print('receiver ip:', receiver_ip)

    for i in region2_resources.instances.all():
        if i.id == sender_id:
            sender_ip = i.public_ip_address
    #print('sender ip:', sender_ip)

    while True:
        try:
            ssh = ssh_to_ec2(receiver_ip, region1)
            run_command(ssh, 'sudo yum install iperf3 -y', 1)
            ssh = ssh_to_ec2(receiver_ip, region1)
            run_command(ssh, 'iperf3 -s -p 5201', 1)
            ssh.close()

            ssh = ssh_to_ec2(sender_ip, region2)
            run_command(ssh, 'sudo yum install iperf3 -y', 1)
            ssh = ssh_to_ec2(sender_ip, region2)
            if region1 == 'us-east-1':
                raw_output = run_command(ssh, f'iperf3 -c ec2-{receiver_ip.replace(".", "-")}.compute-1.amazonaws.com -t 10', 15)
            else:
                raw_output = run_command(ssh, f'iperf3 -c ec2-{receiver_ip.replace(".", "-")}.{region1}.compute.amazonaws.com -t 10', 15)
            ssh.close()

            for line in raw_output:
                if 'sender' in line:
                    sender_bandwidth = line.split()[6:8]
                    print(sender_bandwidth)
                elif 'receiver' in line:
                    receiver_bandwidth = line.split()[6:8]
                    print(receiver_bandwidth)

            if sender_bandwidth[1] == 'Gbits/sec':
                sender_bandwidth[0] = float(sender_bandwidth[0]) * 1000
                sender_bandwidth[1] = 'Mbits/sec'
            else:
                sender_bandwidth[0] = float(sender_bandwidth[0])

            if receiver_bandwidth[1] == 'Gbits/sec':
                receiver_bandwidth[0] = float(receiver_bandwidth[0]) * 1000
                receiver_bandwidth[1] = 'Mbits/sec'
            else:
                receiver_bandwidth[0] = float(receiver_bandwidth[0])
            break
        except UnboundLocalError:
            time.sleep(10)

    terminate_instance(region1, receiver_id, public, secret)
    terminate_instance(region2, sender_id, public, secret)

    return sender_bandwidth, receiver_bandwidth


if __name__ == '__main__':
    main()