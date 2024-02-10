# TODO: Logging. Print to the console (or log to a file) details of what is happening, including errors.
# TODO: Robustness & testing. Your code should do appropriate error handling (using exceptions) and output meaningful messages

import boto3
ec2 = boto3.resource('ec2')
new_instances = ec2.create_instances(
  # Note: ImageId from time to time becomes out of date. Please update; the current
  # ami can be found when launching an instance via the AWS web console.
  ImageId = 'ami-0e731c8a588258d0d',
  MinCount = 1,
  MaxCount = 1,
  InstanceType = 't2.nano',
  # Note: update the name of this security group to any security group you've created that
  # permits HTTP traffic from the internet - see 'Network Settings' in the AWS web console for reference.
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
  # Note: KeyName should refer to your own key; you should save a local copy of it once created.
  # You will need include this key file as a parameter whenever using SSH to access that EC2 instance.
  KeyName = 'carnottKey',
  UserData="""#!/bin/bash
  yum update -y
  yum install httpd -y
  systemctl enable httpd
  systemctl start httpd"""
)
# TODO: The start-up User Data script should also configure the web server index page to display the following
# instance metadata: instance ID, instance type, availability zone and some other content e.g. text or image.


print (new_instances[0].id)
new_instances[0].wait_until_running()
new_instances[0].reload()
print ("Public IPv4 Address: " + new_instances[0].public_ip_address)

