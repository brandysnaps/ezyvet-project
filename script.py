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
    if evaulate_instance_type(instance_type): valid_instance_types.append(instance_type)

  # Find the cheapest on-demand instance
  for instance_type in valid_instance_types:
    instance_type_name = get_instance_type_name(instance_type)
    instance_type["Price"] = get_instance_type_price(instance_type_name)

  # Find the instance type with the cheapest price
  cheapest_instance_type = min(valid_instance_types, key = lambda x:x["Price"])
    
  print(f"TYPE: {get_instance_type_name(cheapest_instance_type)} - vCPU: {get_cpus(cheapest_instance_type)} - Mem: {get_mem(cheapest_instance_type)} GiB - Price: ${cheapest_instance_type['Price']} USD")

if __name__ == "__main__":
  main()