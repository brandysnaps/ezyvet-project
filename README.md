# ezyVet Project

Refer to [scenario.md](doc/scenario.md) for project requirements.

---

## Prerequisites

### Docker

You will need to have Docker installed on your machine.

### IAM Permissions

If you do not have admin permissions for your AWS user, add the following IAM policy to your user:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ezyvet",
      "Effect": "Allow",
      "Action": [
        "ec2:RequestSpotInstances",
        "ec2:DescribeInstanceTypes",
        "ec2:RunInstances",
        "ec2:DescribeSpotInstanceRequests",
        "ssm:GetParameter",
        "pricing:GetProducts"
      ],
      "Resource": "*"
    }
  ]
}
```

## AWS Access Key

Grab your AWS access key and make sure you have the values for `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

---

## Usage

1. Open a Terminal and add environment varaibles which will be used by the Docker container

    ```
    $ export AWS_ACCESS_KEY_ID="<aws_access_key_id>"
    $ export AWS_SECRET_ACCESS_KEY="<aws_secret_access_key>"
    ```

2. Build the Docker image

    ```
    $ docker build -t ezyvet-project .
    ```

3. Run the Docker container to launch an EC2 instance

    ```
    $ docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ezyvet-project
    ```

### Script Default Arguments

| Argument | Value |
| --- | --- |
| `--region` | ap-southeast-2 |
| `--min_cpu` | 1 |
| `--max_cpu` | 2 |
| `--min_mem` | 1 |
| `--max_mem` | 2 |
| `--spot` | False |

---

## Examples

### See Script Usage

```
$ docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ezyvet-project --help
```

### Specify a Different Region

```
$ docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ezyvet-project --region 'us-west-2'
```

### Specify vCPU/memory Requirements

```
$ docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ezyvet-project --max_cpu 32 --min_mem 2
```

### Launch a Spot Instance

```
$ docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ezyvet-project --spot
```