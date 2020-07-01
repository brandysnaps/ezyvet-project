import boto3
import json
import os
import pprint

from constants import AWS_REGIONS

MIN_CPU = 1
MAX_CPU = 4
MIN_MEM = 1
MAX_MEM = 8
ON_DEMAND = True
SPOT = False
REGION = "ap-southeast-2"

EC2_CLIENT     = boto3.client("ec2", region_name = REGION)
EC2_RESOURCE   = boto3.resource("ec2", region_name = REGION)
PRICING_CLIENT = boto3.client("pricing", region_name = "us-east-1")
SSM_CLIENT     = boto3.client("ssm", region_name = REGION)

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

def get_instance_type_price(instance_type):
  # Filter assumes we only want:
  #  - Linux OS
  #  - No pre-installed software
  #  - Shared tenancy

  response = PRICING_CLIENT.get_products(
    ServiceCode = "AmazonEC2",
    Filters = [
      { 'Type' :'TERM_MATCH', 'Field':'capacitystatus', 'Value': 'UnusedCapacityReservation' },
      { 'Type' :'TERM_MATCH', 'Field':'instanceType', 'Value': instance_type },
      { 'Type' :'TERM_MATCH', 'Field':'location', 'Value': AWS_REGIONS[REGION] },
      { 'Type' :'TERM_MATCH', 'Field':'operatingSystem', 'Value':'Linux' },
      { 'Type' :'TERM_MATCH', 'Field':'preInstalledSw', 'Value':'NA' },
      { 'Type' :'TERM_MATCH', 'Field':'tenancy', 'Value':'Shared' },
    ]
  )

  product          = json.loads(response["PriceList"][0])
  price_dimensions = next(iter(product["terms"]["OnDemand"].values()))["priceDimensions"]
  price_per_unit   =  next(iter(price_dimensions.values()))["pricePerUnit"]["USD"]
  return price_per_unit

def get_latest_ami_id():
  # Assume we just want the latest Amazon Linux 2 AMI
  response = SSM_CLIENT.get_parameter(
    Name = "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
  )
  return response["Parameter"]["Value"]

def launch_spot_instance(instance_type):
  response = EC2_CLIENT.request_spot_instances(
    SpotPrice           = instance_type["Price"],
    LaunchSpecification = {
      "ImageId":      get_latest_ami_id(),
      "InstanceType": get_instance_type_name(instance_type)
    }
  )

  print(response)

def launch_on_demand_instance(instance_type):
  response = EC2_RESOURCE.create_instances(
    ImageId      = get_latest_ami_id(),
    InstanceType = get_instance_type_name(instance_type),
    MaxCount     = 1,
    MinCount     = 1
  )

  print(response)

def main():
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
    instance_type["Price"] = get_instance_type_price(instance_type_name)

  # Find the instance type with the cheapest price
  instance = min(valid_instance_types, key = lambda x:x["Price"])
      
  print(f"FOUND: {get_instance_type_name(instance)} - vCPU: {get_cpus(instance)} - Mem: {get_mem(instance)} GiB - Price: ${instance['Price']} USD")

  # Lauch spot instance if requested and instance type supports it
  if SPOT and "spot" in get_instance_supported_usage_classes(instance):
    print(f"Attempting to launch '{get_instance_type_name(instance)}' spot instance")
    # launch_spot_instance(instance)
  else:
    print(f"Launching '{get_instance_type_name(instance)}' on-demand instance")
    # launch_on_demand_instance(instance)

if __name__ == "__main__":
  main()