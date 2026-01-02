# config.py
# Centralized default configuration for AWSTransactionalApps

DEFAULTS = {
    # AWS region
    "region": "ca-central-1",

    # Platform names – if None, defaults will be calculated
    "platform_name": None,     # defaults to project_name
    "state_name": None,        # defaults to platform_name

    # EC2 / Compute
    "instance_type": "t4g.medium",
    "disk_size": 100,

    # AMI — replace this with your custom AMI ID later
    "ami_id": "ami-0c2b8ca1dad447f8a",

    # Deployment bucket (stores docker-compose.yml)
    # If None, defaults to "<platform_name>-deployments"
    "deployment_bucket": None,

    # Storage bucket (general-purpose app storage)
    # If None, defaults to project_name
    "storage_bucket": None,

    # RDS Support
    "enable_rds": False,
    "rds_name": None,          # defaults to project_name

    # ECR settings
    "private_ecr": True,

    # Networking
    "traffic_restriction": [], # list of CIDR blocks allowed to access EC2
    "allowList": [],           # list of IPs allowed to access EC2 on HTTP/HTTPS (empty = allow all)
}
