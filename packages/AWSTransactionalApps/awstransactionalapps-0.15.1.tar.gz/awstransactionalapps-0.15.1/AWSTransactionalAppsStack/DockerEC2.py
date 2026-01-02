
import os
import json
import boto3
import subprocess
import base64
from constructs import Construct
from cdktf import TerraformStack, S3Backend, TerraformOutput
from imports.aws.provider import AwsProvider
from imports.aws.iam_role import IamRole
from imports.aws.iam_role_policy import IamRolePolicy
from imports.aws.iam_instance_profile import IamInstanceProfile
from imports.aws.s3_object import S3Object
from imports.aws.secretsmanager_secret import SecretsmanagerSecret
from imports.aws.secretsmanager_secret_version import SecretsmanagerSecretVersion
from imports.aws.data_aws_secretsmanager_secret import DataAwsSecretsmanagerSecret
from imports.aws.ecr_repository import EcrRepository
from imports.aws.data_aws_ecr_repository import DataAwsEcrRepository
from imports.aws.data_aws_ecr_authorization_token import DataAwsEcrAuthorizationToken
from imports.aws.db_instance import DbInstance
from imports.aws.data_aws_db_instance import DataAwsDbInstance
from imports.aws.instance import Instance
from imports.aws.security_group import SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
from imports.aws.key_pair import KeyPair
from imports.aws.data_aws_key_pair import DataAwsKeyPair
from .config import DEFAULTS
from .uploader import upload_runtime_files
from .ArchitectureHelpers import ArchitectureHelpers
from AWSArchitectureBaseStack.AWSArchitectureBase import AWSArchitectureBase


class ArchitectureFlags: 
    SKIP_DATABASE = "skip_database"
    SKIP_ECR = "skip_ecr"
    PRIVATE_EC2 = "private_ec2"

class DockerEC2(AWSArchitectureBase):

    @staticmethod
    def get_architecture_flags():
        """ Return architecture flags for this stack. Replace with your actual architecture flags. """
        return ArchitectureFlags
    
    @staticmethod
    def get_archetype(product, app, tier, organization, region):
         """ Get the BuzzerboyArchetype instance for advanced configuration. 
            :param product: Product name :param app: Application name
            :param tier: Environment tier (dev, staging, prod)
            :param organization: Organization name 
            :param region: AWS region 
            
            :returns: BuzzerboyArchetype instance 
            :rtype: BuzzerboyArchetype ..
             note:: This method requires the BuzzerboyArchetypeStack module to be available. 
    """
         
         from BuzzerboyArchetypeStack.BuzzerboyArchetype import BuzzerboyArchetype
         return BuzzerboyArchetype(product=product, app=app, tier=tier, organization=organization, region=region)



    def set_defaults(self, **kwargs):
        #Loop through kwargs and set provided values in self. For example, if we have a key region, then self.region = kwargs['region']
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __init__(self, scope: Construct, id: str, *, project_name: str, **kwargs):
        # Prepare kwargs for parent class
        # Extract config values early
        temp_config = dict(DEFAULTS)
        temp_config.update(kwargs)
        
        platform_name = temp_config.get("platform_name") or project_name
        state_name = temp_config.get("state_name") or platform_name
        
        parent_kwargs = {
            'project_name': project_name,
            'region': temp_config.get('region', DEFAULTS.get('region', 'us-east-1')),
            'environment': temp_config.get('environment', 'dev'),
            'profile': temp_config.get('profile', 'default'),
            'flags': temp_config.get('architecture_flags', []),
            'state_bucket_name': f"{state_name}-tfstate",  # Provide explicit state bucket name
        }
        
        # Call parent class constructor
        super().__init__(scope, id)

        self.set_defaults(**parent_kwargs)

        # ==========================================================
        # Load defaults + merge in user-provided kwargs
        # ==========================================================
        self.config = dict(DEFAULTS)
        self.config.update(kwargs)

        # Override project_name from parent if needed
        self.project_name = project_name

        self.architecture_flags = self.config.get("architecture_flags", [])

        # Determine feature flags based on architecture flags
        self.enable_rds = ArchitectureFlags.SKIP_DATABASE not in self.architecture_flags
        self.is_private_ec2 = ArchitectureFlags.PRIVATE_EC2 in self.architecture_flags

        # Get allowList for security group (defaults to everywhere if not provided)
        self.allow_list = self.config.get("allowList", [])

        # Handle dependent defaults
        self.platform_name = self.config["platform_name"] or self.project_name
        self.state_name = self.config["state_name"] or self.platform_name
        self.rds_name = self.config["rds_name"] or project_name
        # Use region from parent class if not specified in config
        if "region" not in self.config or not self.config["region"]:
            self.config["region"] = self.region

        # Bucket names
        self.deployment_bucket = (
            self.config["deployment_bucket"]
            or f"{self.platform_name}-deployments"
        )
        self.storage_bucket = (
            self.config["storage_bucket"]
            or self.project_name
        )

        # Note: S3Backend and AwsProvider are already configured by AWSArchitectureBase

        # ==========================================================
        # 2. IAM Role + Policy for EC2
        # ==========================================================
        self.iam_role = self.create_iam_role()

        self.iam_profile = IamInstanceProfile(
            self,
            "ec2InstanceProfile",
            name=f"{self.project_name}-instance-profile",
            role=self.iam_role.name
        )

        # ==========================================================
        # 3. ECR — always created as Terraform resource
        # ==========================================================
        self.ecr_repo = self.get_or_create_ecr()
        self.ecr_repository_url = f"{self.get_account_id()}.dkr.ecr.{self.region}.amazonaws.com/{self.project_name}"
        self.ecr_registry = f"{self.get_account_id()}.dkr.ecr.{self.region}.amazonaws.com"
        # Skipping boto3 ECR existence check; image build/push should be handled after deployment

        # ==========================================================
        # 4. RDS — conditional creation
        # ==========================================================
        self.rds = self.get_or_create_rds()

        # ==========================================================
        # 5. Deployment bucket — created as Terraform resource
        # ==========================================================
        self.deployment_bucket_resource = self.create_s3_bucket(self.deployment_bucket)

        # 5b. Upload runtime scripts to S3 (after bucket creation)
        self.uploaded_scripts = self.upload_runtime_files()

        # 6. Storage bucket — created as Terraform resource
        # ==========================================================
        self.storage_bucket_resource = self.create_s3_bucket(self.storage_bucket)

        # ==========================================================
        # 7. Secrets Manager Secret
        # ==========================================================
        self.secret = SecretsmanagerSecret(
            self,
            "projectConfigSecret",
            name=f"{self.platform_name}/{self.project_name}/{self.project_name}-config"
        )

        # ==========================================================
        # 7b. SSH Keypair and Keypair Secret
        # ==========================================================
        self.keypair, self.keypair_secret = self.create_keypair_and_secret()

        # ==========================================================
        # 8. Security Group for EC2
        # ==========================================================
        self.security_group = self.create_security_group()

        # ==========================================================
        # 9. EC2 instance
        # ==========================================================
        self.ec2_instance = self.create_ec2_instance()

        # ==========================================================
        # 10. Output: List of all resources to be created
        # ==========================================================
        self.create_resource_list_output()


    # =====================================================================
    # Create Terraform Output listing all resources
    # =====================================================================
    def create_resource_list_output(self):
        """
        Create a Terraform output that lists all resource names expected to be created.
        """
        resource_names = []

        # IAM Resources
        resource_names.append(f"IAM Role: {self.project_name}-role")
        resource_names.append(f"IAM Policy: {self.project_name}-policy")
        resource_names.append(f"IAM Instance Profile: {self.project_name}-instance-profile")

        # ECR Repository
        if isinstance(self.ecr_repo, EcrRepository):
            resource_names.append(f"ECR Repository: {self.project_name}")
        else:
            resource_names.append(f"ECR Repository (existing): {self.project_name}")

        # RDS Instance
        if self.rds is not None:
            if isinstance(self.rds, DbInstance):
                resource_names.append(f"RDS Instance: {self.rds_name}")
            else:
                resource_names.append(f"RDS Instance (existing): {self.rds_name}")

        # S3 Buckets (created via boto3)
        resource_names.append(f"S3 Deployment Bucket (boto3): {self.deployment_bucket}")
        resource_names.append(f"S3 Storage Bucket (boto3): {self.storage_bucket}")

        # Secrets Manager
        resource_names.append(f"Secrets Manager Secret: /{self.project_name}/config")
        if isinstance(self.keypair_secret, SecretsmanagerSecret):
            resource_names.append(f"Secrets Manager Secret: {self.platform_name}/{self.project_name}/{self.project_name}-keypair")
        else:
            resource_names.append(f"Secrets Manager Secret (existing): {self.platform_name}/{self.project_name}/{self.project_name}-keypair")

        # SSH Keypair
        if isinstance(self.keypair, KeyPair):
            resource_names.append(f"EC2 Key Pair: {self.project_name}-keypair")
        else:
            resource_names.append(f"EC2 Key Pair (existing): {self.project_name}-keypair")

        # Security Group
        resource_names.append(f"Security Group: {self.project_name}-sg")

        # EC2 Instance
        resource_names.append(f"EC2 Instance: {self.project_name}")

        # Create the Terraform output
        TerraformOutput(
            self,
            "resource_list",
            value=resource_names,
            description="List of all resources expected to be created by this stack"
        )


    # =====================================================================
    # Create state bucket outside Terraform (S3Backend requirement)
    # =====================================================================
    def ensure_state_bucket(self):
        bucket_name = f"{self.state_name}-tfstate"
        s3 = boto3.client("s3", region_name=self.region)

        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"[INFO] State bucket '{bucket_name}' already exists.")
        except s3.exceptions.NoSuchBucket:
            print(f"[INFO] Creating state bucket '{bucket_name}'.")
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self.region}
            )
        except Exception as e:
            print(f"[WARNING] Could not check state bucket '{bucket_name}': {e}")
            print(f"[INFO] Attempting to create state bucket '{bucket_name}'.")
            try:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": self.region}
                )
            except Exception as create_error:
                print(f"[WARNING] Could not create bucket, it may already exist: {create_error}")


    # =====================================================================
    # IAM Role + Policy loaded from JSON file
    # =====================================================================
    def create_iam_role(self):
        role = IamRole(
            self,
            "ec2Role",
            name=f"{self.project_name}-role",
            assume_role_policy="""{
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Principal": { "Service": "ec2.amazonaws.com" },
                  "Action": "sts:AssumeRole"
                }
              ]
            }"""
        )

        policy_path = os.path.join(
            os.path.dirname(__file__),
            "iam",
            "ec2_policy.json"
        )

        with open(policy_path, "r") as f:
            policy_json = json.dumps(json.load(f))

        IamRolePolicy(
            self,
            "ec2InlinePolicy",
            name=f"{self.project_name}-policy",
            role=role.id,
            policy=policy_json
        )

        return role


    # =====================================================================
    # Conditional ECR creation
    # =====================================================================
    def get_or_create_ecr(self):
        """
        Always create ECR repository as managed resource.
        Terraform will handle lifecycle - if it already exists in state, no changes.
        """
        repo_name = self.project_name
        print(f"[INFO] Creating ECR repository Terraform resource: {repo_name}")
        
        return EcrRepository(
            self,
            "ecrRepo",
            name=repo_name,
            force_delete=True
        )


    # =====================================================================
    # Conditional RDS creation
    # =====================================================================
    def get_or_create_rds(self):
        if not self.enable_rds:
            print("[INFO] RDS disabled (SKIP_DATABASE flag set).")
            return None

        # Always create RDS as a Terraform resource
        print(f"[INFO] Creating RDS '{self.rds_name}' via Terraform")
        return DbInstance(
            self,
            "rdsInstance",
            identifier=self.rds_name,
            engine="postgres",
            instance_class="db.t3.micro",
            allocated_storage=20,
            username="dbadmin",
            password="TempPassword123!",
            skip_final_snapshot=True
        )


    # =====================================================================
    # S3 Bucket creation as Terraform resource
    # =====================================================================
    def create_s3_bucket(self, bucket_name: str):
        """
        Create an S3 bucket as a Terraform resource.
        :param bucket_name: Name of the bucket to create
        """
        from imports.aws.s3_bucket import S3Bucket
        return S3Bucket(
            self,
            f"s3Bucket-{bucket_name}",
            bucket=bucket_name,
            force_destroy=True,
            tags={
                "projectName": self.project_name
            }
        )


    # =====================================================================
    # Security Group for EC2
    # =====================================================================
    def create_security_group(self):
        """
        Create a security group for the EC2 instance.
        - If PRIVATE_EC2 flag is set, only allows traffic from allowList IPs
        - Otherwise, allows public HTTP/HTTPS traffic (or from allowList if provided)
        """
        # Determine CIDR blocks for ingress
        if self.allow_list:
            # Use provided allowList - ensure they are in CIDR format
            cidr_blocks = [ip if "/" in ip else f"{ip}/32" for ip in self.allow_list]
        else:
            # Default to everywhere (0.0.0.0/0) if no allowList provided
            cidr_blocks = ["0.0.0.0/0"]

        # Build ingress rules
        ingress_rules = []

        # Only add HTTP/HTTPS ingress if not private EC2, or if allowList is provided
        if not self.is_private_ec2 or self.allow_list:
            # HTTP ingress
            ingress_rules.append(SecurityGroupIngress(
                from_port=80,
                to_port=80,
                protocol="tcp",
                cidr_blocks=cidr_blocks,
                description="HTTP access"
            ))
            # HTTPS ingress
            ingress_rules.append(SecurityGroupIngress(
                from_port=443,
                to_port=443,
                protocol="tcp",
                cidr_blocks=cidr_blocks,
                description="HTTPS access"
            ))

        # Egress rule - allow all outbound traffic
        egress_rules = [SecurityGroupEgress(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic"
        )]

        return SecurityGroup(
            self,
            "ec2SecurityGroup",
            name=f"{self.project_name}-sg",
            description=f"Security group for {self.project_name} EC2 instance",
            ingress=ingress_rules,
            egress=egress_rules,
            tags={
                "projectName": self.project_name
            }
        )


    # =====================================================================
    # Create SSH Keypair and Store in Secrets Manager
    # =====================================================================
    def create_keypair_and_secret(self):
        """
        Create an SSH keypair and store the private key in Secrets Manager.
        Checks if resources exist in AWS. If they do AND we're creating them for the first time
        (not in Terraform state), we'll fail to avoid overwriting existing resources.
        If they don't exist, creates them.
        Returns tuple of (keypair, secret)
        """
        import subprocess
        import tempfile
        from botocore.exceptions import ClientError
        
        keypair_name = f"{self.project_name}-keypair"
        secret_name = f"{self.platform_name}/{self.project_name}/{self.project_name}-keypair"
        
        # Generate SSH keypair material ONCE during initial synthesis
        # After first deployment, we use placeholder values since Terraform
        # already has the real values in state
        keypair_path = os.path.join(tempfile.gettempdir(), f"{keypair_name}_persistent.pub")
        
        # Check if we've already generated this keypair in a previous synthesis
        if os.path.exists(keypair_path):
            # Use cached values - prevents regeneration on every synthesis
            with open(keypair_path, "r") as f:
                public_key = f.read().strip()
            private_key_cached_path = keypair_path.replace(".pub", "")
            with open(private_key_cached_path, "r") as f:
                private_key = f.read()
            print(f"[INFO] Using cached keypair material from {keypair_path}")
        else:
            # Generate new SSH keypair
            print(f"[INFO] Generating new SSH keypair")
            with tempfile.TemporaryDirectory() as tmpdir:
                key_path = os.path.join(tmpdir, "id_rsa")
                subprocess.run(
                    ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", key_path, "-N", ""],
                    check=True,
                    capture_output=True
                )
                
                # Read the public and private keys
                with open(f"{key_path}.pub", "r") as f:
                    public_key = f.read().strip()
                
                with open(key_path, "r") as f:
                    private_key = f.read()
                
                # Cache the keys for future synthesis runs
                with open(keypair_path, "w") as f:
                    f.write(public_key)
                private_key_cached_path = keypair_path.replace(".pub", "")
                with open(private_key_cached_path, "w") as f:
                    f.write(private_key)
                print(f"[INFO] Cached keypair material to {keypair_path}")
        
        # Always create managed resources (not data sources)
        keypair = KeyPair(
            self,
            "sshKeypair",
            key_name=keypair_name,
            public_key=public_key,
            tags={
                "projectName": self.project_name
            }
        )
        
        # Create secret to store the private key
        keypair_secret = SecretsmanagerSecret(
            self,
            "keypairSecret",
            name=secret_name
        )
        
        # Store the private key in the secret
        secret_value = json.dumps({"keypair": private_key})
        SecretsmanagerSecretVersion(
            self,
            "keypairSecretVersion",
            secret_id=keypair_secret.id,
            secret_string=secret_value
        )
        
        return keypair, keypair_secret

    # =====================================================================
    # EC2 Instance
    # =====================================================================
    def create_ec2_instance(self):
        # Generate user data script
        user_data = self.generate_user_data()

        # Determine if we should assign a public IP
        # Public IP is assigned unless PRIVATE_EC2 flag is set
        associate_public_ip = not self.is_private_ec2
        
        return Instance(
            self,
            "ec2Instance",
            ami=self.config["ami_id"],
            instance_type=self.config["instance_type"],
            iam_instance_profile=self.iam_profile.name,
            key_name=self.keypair.key_name,
            user_data=user_data,
            vpc_security_group_ids=[self.security_group.id],
            associate_public_ip_address=associate_public_ip,
            root_block_device={
                "volume_size": self.config["disk_size"]
            },
            tags={
                "Name": self.project_name,
                "projectName": self.project_name
            }
        )

    # =====================================================================
    # Generate User Data Script
    # =====================================================================
    def generate_user_data(self) -> str:
        """
        Generate the EC2 user data script that downloads and executes setup.sh
        """
        user_data = ArchitectureHelpers.getFormattedTextFromFile(
            "user_data.sh",
            {
                "deployment_bucket": self.deployment_bucket,
                "project_name": self.project_name
            }
        )
        return user_data

    # =====================================================================
    # Upload Runtime Files to S3
    # =====================================================================
    def upload_runtime_files(self) -> list:
        """
        Upload all runtime scripts to the deployment bucket.
        Uses the uploader module to walk the scripts directory.
        """
        template_vars = {
            "ecr_repository_url": self.ecr_repository_url,
            "ecr_registry": self.ecr_registry,
            "deployment_bucket": self.deployment_bucket,
            "project_name": self.project_name
        }
        return upload_runtime_files(
            self, 
            self.deployment_bucket, 
            self.project_name, 
            template_vars
        )

    # =====================================================================
    # Get AWS Account ID
    # =====================================================================
    def get_account_id(self) -> str:
        """
        Get the AWS account ID using boto3.
        """
        sts = boto3.client("sts", region_name=self.region)
        return sts.get_caller_identity()["Account"]

    # =====================================================================
    # Build and Push Initial Docker Image
    # =====================================================================
    def build_and_push_initial_image(self):
        """
        Build and push the hello-world Docker image to ECR.
        This should be run manually after Terraform deploys the ECR repository.
        """
        hello_world_dir = os.path.join(os.path.dirname(__file__), "hello-world")
        if not os.path.exists(hello_world_dir):
            print(f"[WARNING] Hello-world directory not found: {hello_world_dir}")
            return
        print(f"[INFO] After Terraform deployment, manually build and push Docker image to {self.ecr_repository_url}")
