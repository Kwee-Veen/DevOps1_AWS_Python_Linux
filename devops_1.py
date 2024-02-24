# TODO: Logging. Print to the console (or log to a file) details of what is happening, including errors.
# TODO: Robustness & testing. Your code should do appropriate error handling (using exceptions) and output meaningful messages

import boto3, time, webbrowser
ec2 = boto3.resource('ec2')
new_instances = ec2.create_instances(
  # Note: ImageId from time to time becomes out of date. Please update; the current
  # ami can be found when launching an instance via the AWS web console.
  ImageId = 'ami-0e731c8a588258d0d',
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
  echo "<br>A: 2,271. Russia has the most satellites currently in orbit, with 1,324 satellites, followed by the U.S. with 658. This does not count orbiting debris, only spacecraft." >> index.html
  sudo mv index.html /var/www/html/index.html >> index.html
  """
)

# TODO: Step The start-up User Data script should also configure the web server index page to display the following
# instance metadata: instance ID, instance type, availability zone and some other content e.g. text or image.
print (new_instances[0].id)
new_instances[0].wait_until_running()
new_instances[0].reload()
inst0_ip = new_instances[0].public_ip_address
print ("Instance Running. Public IPv4 Address: " + inst0_ip)

# TODO: Step 4, create S3 bucket here; have one wait period, then both are opened at the same time.

# TODO: Step 5, write URLs of both EC2 & S3 to a file called carnott-websites.txt.
#       Then time.sleep(25) -> open both URLs in browser, showing both images.

time.sleep(35)
apache_url = 'http://' + inst0_ip
webbrowser.open_new_tab(apache_url)

