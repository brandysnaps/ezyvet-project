import argparse

from lib.aws_regions import AWS_REGIONS

class ARG_PARSER:
  def __init__(self):
    self.parser = argparse.ArgumentParser(description = "Launch a single spot/on-demand instance")
    self.parser.add_argument("--min_cpu", type=int, default=1, help="Minimum number of vCPUs")
    self.parser.add_argument("--max_cpu", type=int, default=2, help="Maximum number of vCPUs")
    self.parser.add_argument("--min_mem", type=int, default=1, help="Minimum amount of Memory (GiB)")
    self.parser.add_argument("--max_mem", type=int, default=2, help="Maximum amount of Memory (GiB)")
    self.parser.add_argument("--region", type=str, default="ap-southeast-2", help="AWS region", choices=list(AWS_REGIONS.keys()))
    self.parser.add_argument("--spot", action="store_true", default=False, help="Create a spot instance instead of on-demand")
    self.args = self.parser.parse_args()