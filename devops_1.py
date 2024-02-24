# TODO: Logging. Print to the console (or log to a file) details of what is happening, including errors.
# TODO: Robustness & testing. Your code should do appropriate error handling (using exceptions) and output meaningful messages


import boto3, time, webbrowser, json
ec2 = boto3.resource('ec2')
new_instances = ec2.create_instances(
  # Note: ImageId from time to time becomes out of date. Please update; the current
  # ami can be found when launching an instance via the AWS web console.
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
new_instances[0].wait_until_running()
new_instances[0].reload()
inst0_ip = new_instances[0].public_ip_address
print ("Instance Running. Public IPv4 Address: " + inst0_ip)


# TODO: Step 4, create S3 bucket here; have one wait period, then both are opened at the same time.

s3 = boto3.resource("s3")
now = time.strftime("%H.%M.%S", time.localtime())
bucketName = (f'big-ole-bucket-made-at-{now}')
try:
    response = s3.create_bucket(Bucket=(f'{bucketName}'))
    print (response)
except Exception as error:
    print (error)

website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'},
}

bucket_website = s3.BucketWebsite(f'{bucketName}')
response = bucket_website.put(WebsiteConfiguration=website_configuration)

# TODO: push an index.html file to the s3 bucket
# <img> tag > index.html   ....   then grab the code to push that to the s3 bucket.
# I'm assuming this has to be done before you invoke the below policy change, but if it doesn't work, put this after the policy change, or experiment with waiters

# TODO: use subprocess.run or something to download the image, then some code to upload it to the bucket. Implement this after the above TODO though.

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
time.sleep(2)

# Consider opening both sites at the same time? Particularly if waiting is needed for s3 image upload etc.

print (f'Opening {bucketName} endpoint in browser')
s3_endpoint = f'http://{bucketName}.s3-website-us-east-1.amazonaws.com'
webbrowser.open_new_tab(s3_endpoint)


# TODO: Step 5, write URLs of both EC2 & S3 to a file called carnott-websites.txt.
#       Then time.sleep(25) -> open both URLs in browser, showing both images.
print ("Waiting 25 sec for ec2 installation to complete")
time.sleep(25)
print ("Launching ec2 static website in browser")
apache_url = 'http://' + inst0_ip
webbrowser.open_new_tab(apache_url)

