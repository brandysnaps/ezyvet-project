import boto3
import botocore
import json
import os
import pprint

from lib.aws_ssm import AWS_SSM
from lib.aws_pricing import AWS_PRICING

MIN_CPU = 1
MAX_CPU = 4
MIN_MEM = 1
MAX_MEM = 8
SPOT = False
REGION = "ap-southeast-2"

EC2_CLIENT     = boto3.client("ec2", region_name = REGION)
EC2_RESOURCE   = boto3.resource("ec2", region_name = REGION)

def instance_types_file():
  return "/tmp/instance_types.json"

def update_instance_types():
  instance_types = EC2_CLIENT.describe_instance_types()

  with open(instance_types_file(), "w") as outfile:
      json.dump(instance_types, outfile)

def load_instance_types():
  with open(instance_types_file()) as json_file:
    return json.load(json_file)["InstanceTypes"]

def get_cpus(instance_type):
  return instance_type["VCpuInfo"]["DefaultVCpus"]

def get_mem(instance_type):
  return instance_type["MemoryInfo"]["SizeInMiB"] / 1024

def get_instance_type_name(instance_type):
  return instance_type["InstanceType"]

def get_instance_supported_usage_classes(instance_type):
  return instance_type["SupportedUsageClasses"]

def evaulate_instance_type(instance_type):
  valid                = True
  current_generation   = instance_type["CurrentGeneration"]
  architectures        = instance_type["ProcessorInfo"]["SupportedArchitectures"]
  cpu                  = get_cpus(instance_type)
  mem                  = get_mem(instance_type)

  # Current generation
  if not current_generation:
    valid = False

  # Supported architecture
  if "x86_64" not in architectures:
    valid = False

  # Number of vCPUs
  if not MIN_CPU <= cpu <= MAX_CPU:
    valid = False

  # Amount of RAM
  if not MIN_MEM <= mem <= MAX_MEM:
    valid = False

  return valid

def launch_spot_instance(instance_type, ami):
  return_value = ""

  # Only launch a spot instance if the instance type supports it
  if "spot" in get_instance_supported_usage_classes(instance_type):
    response = EC2_CLIENT.request_spot_instances(
      SpotPrice           = instance_type["Price"],
      LaunchSpecification = {
        "ImageId":      ami,
        "InstanceType": get_instance_type_name(instance_type)
      }
    )

    # Wait for spot instance request to be fulfilled
    request_id = response["SpotInstanceRequests"][0]["SpotInstanceRequestId"]
    request_fulfilled_waiter = EC2_CLIENT.get_waiter("spot_instance_request_fulfilled")

    try:
      request_fulfilled_waiter.wait(
        SpotInstanceRequestIds = [ request_id ]
      )

      return_value = EC2_CLIENT.describe_spot_instance_requests(
        SpotInstanceRequestIds = [ request_id ]
      )

      return return_value
    except botocore.exceptions.WaiterError:
      return return_value

  else:
    print(f"Spot instance not supported for '{get_instance_type_name(instance_type)}'")
    return return_value

def launch_on_demand_instance(instance_type, ami):
  print(f"Launching '{get_instance_type_name(instance_type)}' on-demand instance in '{REGION}'")

  response = EC2_RESOURCE.create_instances(
    ImageId      = ami,
    InstanceType = get_instance_type_name(instance_type),
    MaxCount     = 1,
    MinCount     = 1
  )

  instance_id = response[0].instance_id
  print(f"Successfully launched on-demand instance: '{instance_id}' in '{REGION}'")

def main():
  latest_ami = AWS_SSM(REGION).get_latest_ami_id()
  aws_pricing = AWS_PRICING(REGION)

  print(f"LOOKING FOR: {MIN_CPU}-{MAX_CPU} vCPU & {MIN_MEM}-{MAX_MEM} Memory (GiB)")

  # Get the current list of instance types provided by AWS
  # if we don't already have it
  if not os.path.exists(instance_types_file()):
    update_instance_types()

  # Load instance types
  instance_types = load_instance_types()

  # Find valid instances we can choose from
  valid_instance_types = []
  for instance_type in instance_types:
    if evaulate_instance_type(instance_type):
      valid_instance_types.append(instance_type)

  # Find the cheapest on-demand instance
  for instance_type in valid_instance_types:
    instance_type_name = get_instance_type_name(instance_type)
    instance_type["Price"] = aws_pricing.get_instance_type_price(instance_type_name)

  # Find the instance type with the cheapest price
  instance = min(valid_instance_types, key = lambda x:x["Price"])
      
  print(f"FOUND: {get_instance_type_name(instance)} - vCPU: {get_cpus(instance)} - Mem: {get_mem(instance)} GiB - Price: ${instance['Price']} USD")

  if SPOT:
    print(f"Attempting to launch '{get_instance_type_name(instance)}' spot instance in '{REGION}'")
    response = launch_spot_instance(instance, latest_ami)
    if response:
      instance_id = response["SpotInstanceRequests"][0]["InstanceId"]
      print(f"Successfully launched spot instance: '{instance_id}' in '{REGION}'")
    else:
      print("Could not create spot instance. Launching on-demand instance instead")
      launch_on_demand_instance(instance, latest_ami)
  else:
    launch_on_demand_instance(instance, latest_ami)

if __name__ == "__main__":
  main()