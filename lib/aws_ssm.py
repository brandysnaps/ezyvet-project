import boto3

class AWS_SSM:
  def __init__(self, region):
    self.client = boto3.client("ssm", region_name = region)

  def get_latest_ami_id(self):
    # Assume we just want the latest Amazon Linux 2 AMI
    response = self.client.get_parameter(
      Name = "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
    )
    return response["Parameter"]["Value"]