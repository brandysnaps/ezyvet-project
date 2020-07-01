import boto3
import json

from lib.aws_regions import AWS_REGIONS

class AWS_PRICING:
  def __init__(self, region):
    self.client = boto3.client("pricing", region_name = "us-east-1")
    self.region = region

  def get_instance_type_price(self, instance_type):
    # Filter assumes we only want:
    #  - Linux OS
    #  - No pre-installed software
    #  - Shared tenancy

    response = self.client.get_products(
      ServiceCode = "AmazonEC2",
      Filters = [
        { 'Type' :'TERM_MATCH', 'Field':'capacitystatus', 'Value': 'UnusedCapacityReservation' },
        { 'Type' :'TERM_MATCH', 'Field':'instanceType', 'Value': instance_type },
        { 'Type' :'TERM_MATCH', 'Field':'location', 'Value': AWS_REGIONS[self.region] },
        { 'Type' :'TERM_MATCH', 'Field':'operatingSystem', 'Value':'Linux' },
        { 'Type' :'TERM_MATCH', 'Field':'preInstalledSw', 'Value':'NA' },
        { 'Type' :'TERM_MATCH', 'Field':'tenancy', 'Value':'Shared' },
      ]
    )

    product          = json.loads(response["PriceList"][0])
    price_dimensions = next(iter(product["terms"]["OnDemand"].values()))["priceDimensions"]
    price_per_unit   =  next(iter(price_dimensions.values()))["pricePerUnit"]["USD"]
    return price_per_unit