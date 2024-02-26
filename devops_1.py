# TODO: Logging. Print to the console (or log to a file) details of what is happening, including errors.
# TODO: Robustness & testing. Your code should do appropriate error handling (using exceptions) and output meaningful messages

import boto3, webbrowser, time, json, requests, uuid, subprocess
ec2 = boto3.resource('ec2')

# Creating ec2 instance with UserData script to initiate apache server, displaying current instance metadata
new_instances = ec2.create_instances(
  ImageId = 'ami-0440d3b780d96b29d',
  MinCount = 1,
  MaxCount = 1,
  InstanceType = 't2.nano',
  SecurityGroups = [
    'launch-wizard-1'
  ],
  TagSpecifications = [
    {
      'ResourceType': 'instance',
      'Tags': [
        {
          'Key': 'Name',
          'Value': 'Script-generated web server'
        },
      ]
    },
  ],
  KeyName = 'carnottKey',
  UserData="""#!/bin/bash
  yum update -y
  yum install httpd -y
  systemctl enable httpd
  systemctl start httpd
  TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
  echo "This instance is running in availability zone:" > index.html
  curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone >> index.html
  echo "<hr>The instance ID is: " >> index.html
  curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id >> index.html
  echo "<hr>The instance type is: " >> index.html
  curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type >> index.html
  echo "<hr>The instance AMI ID is: " >> index.html
  curl -H "X-aws-ec2-metadata-token: $TOKEN" -v http://169.254.169.254/latest/meta-data/ami-id >> index.html
  echo "<hr>The instance's public IPv4 address is: " >> index.html
  curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 >> index.html
  echo "<hr><br>Want a useless fact?" >> index.html
  echo "<br>Course you do!" >> index.html
  echo "<br><br>Q: How many satellites are in space?" >> index.html
  echo "<br>A: 2,271. Russia has the most in orbit at 1,324 satellites, followed by the U.S. with 658. This does not count orbiting debris, just spacecraft." >> index.html
  sudo mv index.html /var/www/html/index.html >> index.html
  """
)
print (new_instances[0].id)

# Creating s3 bucket
s3 = boto3.resource("s3")
bigRandom = uuid.uuid4()
bigRandomString = str(bigRandom)
randomSixCharacters = bigRandomString[0:6]
bucketName = (f'{randomSixCharacters}-carnott')
try:
    response = s3.create_bucket(Bucket=(f'{bucketName}'))
    print (response)
except Exception as error:
    print (error)

# Saving logo.jpg locally
img_url = 'http://devops.witdemo.net/logo.jpg'
path = 'logo.jpg'
response = requests.get(img_url)
if response.status_code == 200:
    with open(path, 'wb') as f:
        f.write(response.content)

# Pushing logo.jpg to the s3 bucket
try:
    s3.Object(bucketName, "logo.jpg").put(Body=open("logo.jpg", 'rb'), ContentType="image/jpeg")
    print (f'Saved logo.jpg to {bucketName}')
except Exception as error:
    print (error)

# Creating index.html file
print ('<!DOCTYPE html>', file=open('index.html', 'w'))
print ('<html>', file=open('index.html', 'a'))
print ('<img src="logo.jpg" alt="SETU Logo">', file=open('index.html', 'a'))
print ('</html>', file=open('index.html', 'a'))

# Pushing index.html to the s3 bucket
try:
    s3.Object(bucketName, "index.html").put(Body=open("index.html", 'rb'), ContentType="text/html")
    print (f'Saved index.html to {bucketName}')
except Exception as error:
    print (error)

# Configuring s3 bucket to use index.html
website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'},
}
bucket_website = s3.BucketWebsite(f'{bucketName}')
response = bucket_website.put(WebsiteConfiguration=website_configuration)

# Deleting s3 bucket's public access block, creating & uploading a new policy permitting public traffic
s3client = boto3.client("s3")
s3client.delete_public_access_block(Bucket=(f'{bucketName}'))
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
    {
        "Sid": "PublicReadGetObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": ["s3:GetObject"],
        "Resource": f"arn:aws:s3:::{bucketName}/*"
    }
    ]
}
s3.Bucket(f'{bucketName}').Policy().put(Policy=json.dumps(bucket_policy))
print ("s3 Policy amended")
time.sleep(1)

# Opening s3 bucket endpoint in browser
print (f'Opening {bucketName} endpoint in browser')
s3_endpoint = f'http://{bucketName}.s3-website-us-east-1.amazonaws.com'
webbrowser.open_new_tab(s3_endpoint)

# Saving s3 bucket link to a local file
print (f'Saving {s3_endpoint} link to local file "carnott-websites.txt"')
print ('Generated s3 bucket link:', file=open('carnott-websites.txt', 'w'))
print (s3_endpoint, file=open('carnott-websites.txt', 'a'))

# Waiting until ec2 instance is running, then saving the IPv4 address as inst0_ip
print ("Waiting until ec2 instance is running")
new_instances[0].wait_until_running()
new_instances[0].reload()
inst0_ip = new_instances[0].public_ip_address
print ("EC2 instance running. Public IPv4 Address: " + inst0_ip)

# Saving ec2 instance link to a local file
apache_url = 'http://' + inst0_ip
print (f'Saving {apache_url} link to local file "carnott-websites.txt"')
print ('Generated ec2 instance link:', file=open('carnott-websites.txt', 'a'))
print (apache_url, file=open('carnott-websites.txt', 'a'))

# Waiting for ec2 installation completion
print ("Waiting 35 sec for ec2 installation to complete")
time.sleep(35)

# Copy the monitoring.sh script to the ec2 instance via scp
print (f'Copying monitoring.sh to {inst0_ip}')
ec2_ipv4 = f'ec2-user@{inst0_ip}'
scp_cmd = f'scp -o StrictHostKeyChecking=no -i carnottKey.pem monitoring.sh {ec2_ipv4}:.'
subprocess.call(scp_cmd.split())

# Modify monitoring.sh in the ec2 instance via ssh remote command execution
print (f'Changing monitoring.sh permissions in {inst0_ip}')
ssh_permissions_command = "chmod 700 monitoring.sh"
ssh_permissions_full = f'ssh -i carnottKey.pem {ec2_ipv4} {ssh_permissions_command}'
subprocess.call(ssh_permissions_full.split())

# Execute monitoring.sh in the ec2 instance via ssh remote command execution
print (f'Executing monitoring.sh in {inst0_ip}:')
ssh_execute = f'ssh -i carnottKey.pem {ec2_ipv4} "./monitoring.sh"'
subprocess.call(ssh_execute.split())

# Opening ec2 instance link in browser
print ("Launching ec2 static website in browser")
webbrowser.open_new_tab(apache_url)
