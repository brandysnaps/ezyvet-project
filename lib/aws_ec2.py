import boto3
import botocore

from lib.aws_pricing import AWS_PRICING
from lib.aws_ssm import AWS_SSM

class AWS_EC2:
  def __init__(self, region, min_cpu, max_cpu, min_mem, max_mem):
    self.client = boto3.client("ec2", region_name = region)
    self.resource = boto3.resource("ec2", region_name = region)
    self.region = region
    self.min_cpu = min_cpu
    self.max_cpu = max_cpu
    self.min_mem = min_mem
    self.max_mem = max_mem

  def evaulate_instance_type(self, instance_type):
    valid                = True
    current_generation   = instance_type["CurrentGeneration"]
    architectures        = instance_type["ProcessorInfo"]["SupportedArchitectures"]
    cpu                  = self.get_cpus(instance_type)
    mem                  = self.get_mem(instance_type)

    # Current generation
    if not current_generation:
      valid = False

    # Supported architecture
    if "x86_64" not in architectures:
      valid = False

    # Number of vCPUs
    if not self.min_cpu <= cpu <= self.max_cpu:
      valid = False

    # Amount of RAM
    if not self.min_mem <= mem <= self.max_mem:
      valid = False

    return valid

  def validate_instance_types(self, instance_types):
    valid = []
    for instance_type in instance_types:
      if self.evaulate_instance_type(instance_type):
        valid.append(instance_type)

    return valid

  def get_instance_prices(self, instance_types):
    aws_pricing = AWS_PRICING(self.region)
    for instance_type in instance_types:
      instance_type_name = self.get_instance_type_name(instance_type)
      instance_type["Price"] = aws_pricing.get_instance_type_price(instance_type_name)

    return instance_types

  def get_cpus(self, instance_type):
    return instance_type["VCpuInfo"]["DefaultVCpus"]

  def get_mem(self, instance_type):
    return instance_type["MemoryInfo"]["SizeInMiB"] / 1024

  def get_instance_type_name(self, instance_type):
    return instance_type["InstanceType"]

  def get_instance_supported_usage_classes(self, instance_type):
    return instance_type["SupportedUsageClasses"]

  def launch_spot_instance(self, instance_type):
    return_value = ""

    # Only launch a spot instance if the instance type supports it
    if "spot" in self.get_instance_supported_usage_classes(instance_type):
      response = self.client.request_spot_instances(
        SpotPrice           = instance_type["Price"],
        LaunchSpecification = {
          "ImageId":      AWS_SSM(self.region).get_latest_ami_id(),
          "InstanceType": self.get_instance_type_name(instance_type)
        }
      )

      # Wait for spot instance request to be fulfilled
      request_id = response["SpotInstanceRequests"][0]["SpotInstanceRequestId"]
      request_fulfilled_waiter = self.client.get_waiter("spot_instance_request_fulfilled")

      try:
        request_fulfilled_waiter.wait(
          SpotInstanceRequestIds = [ request_id ]
        )

        return_value = self.client.describe_spot_instance_requests(
          SpotInstanceRequestIds = [ request_id ]
        )

        return return_value
      except botocore.exceptions.WaiterError:
        return return_value

    else:
      print(f"Spot instance not supported for '{self.get_instance_type_name(instance_type)}'")
      return return_value

  def launch_on_demand_instance(self, instance_type):
    print(f"Launching '{self.get_instance_type_name(instance_type)}' on-demand instance in '{self.region}'")

    response = self.resource.create_instances(
      ImageId      = AWS_SSM(self.region).get_latest_ami_id(),
      InstanceType = self.get_instance_type_name(instance_type),
      MaxCount     = 1,
      MinCount     = 1
    )

    instance_id = response[0].instance_id
    print(f"Successfully launched on-demand instance: '{instance_id}' in '{self.region}'")