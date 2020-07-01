import boto3
import json
import os

from lib.aws_ec2 import AWS_EC2

MIN_CPU = 1
MAX_CPU = 4
MIN_MEM = 1
MAX_MEM = 8
SPOT = True
REGION = "ap-southeast-2"

# EC2_CLIENT     = boto3.client("ec2", region_name = REGION)
# EC2_RESOURCE   = boto3.resource("ec2", region_name = REGION)

def instance_types_file():
  return "/tmp/instance_types.json"

def update_instance_types(ec2_client):
  instance_types = ec2_client.describe_instance_types()

  with open(instance_types_file(), "w") as outfile:
      json.dump(instance_types, outfile)

def load_instance_types():
  with open(instance_types_file()) as json_file:
    return json.load(json_file)["InstanceTypes"]

def main():
  aws_ec2 = AWS_EC2(REGION, MIN_CPU, MAX_CPU, MIN_MEM, MAX_MEM)

  print(f"LOOKING FOR: {MIN_CPU}-{MAX_CPU} vCPU & {MIN_MEM}-{MAX_MEM} Memory (GiB)")

  # Get the current list of instance types provided by AWS
  # if we don't already have it
  if not os.path.exists(instance_types_file()):
    update_instance_types(aws_ec2.client)

  # Load instance types
  instance_types = load_instance_types()

  # Find valid instances we can choose from
  valid_instance_types = aws_ec2.validate_instance_types(instance_types)

  # Find the price for valid instances
  valid_instance_types = aws_ec2.get_instance_prices(valid_instance_types)

  # Find the instance type with the cheapest price
  instance           = min(valid_instance_types, key = lambda x:x["Price"])
  instance_type_name = aws_ec2.get_instance_type_name(instance)
  instance_cpu       = aws_ec2.get_cpus(instance)
  instance_mem       = aws_ec2.get_mem(instance)
  instance_price     = instance["Price"]

  print(f"FOUND: {instance_type_name} - vCPU: {instance_cpu} - Mem: {instance_mem} GiB - Price: ${instance_price} USD")

  if SPOT:
    print(f"Attempting to launch '{instance_type_name}' spot instance in '{REGION}'")
    response = aws_ec2.launch_spot_instance(instance)
    if response:
      instance_id = response["SpotInstanceRequests"][0]["InstanceId"]
      print(f"Successfully launched spot instance: '{instance_id}' in '{REGION}'")
    else:
      print("Could not create spot instance. Launching on-demand instance instead")
      aws_ec2.launch_on_demand_instance(instance)
  else:
    aws_ec2.launch_on_demand_instance(instance)

if __name__ == "__main__":
  main()