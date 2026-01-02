import os
import json
import boto3
from constructs import Construct
from cdktf import TerraformStack, TerraformOutput, S3Backend
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
from .ArchitectureFlags import ArchitectureFlags

class DockerEC2Standalone(TerraformStack):


    additional_outputs = [
        "The initial docker-compose.yml is available at {{docker-compose-s3-url}}",
        "The initial Dockerfile is available at {{dockerfile-s3-url}}",
        "The initial nginx configuration is available at {{nginx-config-s3-url}}",
        "---ECR Registry: {{ecr_registry}}",
        "---ECR Repository URL: {{ecr_repository_url}}",
        "---AWS Region: {{region}}",
        "---To push the your app image to ERC, use this command: 1) ECR Login: $(aws ecr get-login-password --region {{region}}) | docker login --username AWS --password-stdin {{ecr_registry}} 2) Tag your image: docker tag <your-image>:latest {{ecr_repository_url}}:latest 3) Push your image: docker-compose push {{ecr_repository_url}}:latest",
        "Deployment scripts are available at s3://{{deployment_bucket}}/{{project_name}}/deploy/ (appDeploy.sh, appBuild.sh, appPush.sh, appLoad.sh). Run these where your docker-compose.yaml is located.",
        "Use these steps in a CI/CD pipeline to ensure credential refresh limits are maintained:",
        "---1) Build your app: aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/deploy/appBuild.sh - | bash",
        "---2) Push your app image to ECR: aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/deploy/appPush.sh - | bash",
        "---3) Load and run your app on the EC2 instance: aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/deploy/appLoad.sh - | bash",
        "One-shot Direct Deploy on EC2 Instance. Local Use Onyl! DO NOT USE THIS IN A CICD PIPELINE:"
        "---1) Oneshot-deploy: aws s3 cp s3://{{deployment_bucket}}/{{project_name}}/deploy/appDeploy.sh - | bash",

    ]

    def get_or_create_backend_bucket(self, bucket_name: str, region: str):
        """
        Ensure the backend S3 bucket exists for Terraform state. If not, create it using boto3.
        """
        import re
        import boto3
        # Clean bucket name to meet S3 requirements
        bucket_name = bucket_name.lower()
        bucket_name = re.sub(r'[^a-z0-9.-]', '-', bucket_name)
        bucket_name = re.sub(r'(^[.-]+|[.-]+$)', '', bucket_name)
        if len(bucket_name) < 3:
            bucket_name += '-bucket'
        if len(bucket_name) > 63:
            bucket_name = bucket_name[:63]
        s3 = boto3.client("s3", region_name=region)
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"[INFO] Backend bucket '{bucket_name}' already exists.")
        except s3.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region}
                )
                print(f"[INFO] Created backend bucket '{bucket_name}' for Terraform state.")
            else:
                print(f"[ERROR] Could not access or create bucket '{bucket_name}': {e}")
        return bucket_name

    @staticmethod
    def get_architecture_flags():
        """ Return architecture flags for this stack. """
        return ArchitectureFlags

    @staticmethod
    def get_archetype(product, app, tier, organization, region):
        """ Get the BuzzerboyArchetype instance for advanced configuration. """
        from BuzzerboyArchetypeStack.BuzzerboyArchetype import BuzzerboyArchetype
        return BuzzerboyArchetype(product=product, app=app, tier=tier, organization=organization, region=region)

    def set_defaults(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


    def __init__(self, scope: Construct, id: str, *, project_name: str, **kwargs):
        temp_config = dict(DEFAULTS)
        temp_config.update(kwargs)
        platform_name = temp_config.get("platform_name") or project_name
        state_name = temp_config.get("state_name") or platform_name
        self.config = dict(DEFAULTS)
        self.config.update(kwargs)
        self.project_name = project_name
        self.secret_name = self.config.get("secret_name") or f"{self.project_name}-config"
        self.architecture_flags = self.config.get("architecture_flags", [])
        self.enable_rds = getattr(self.config, 'SKIP_DATABASE', False) not in self.architecture_flags
        self.is_private_ec2 = getattr(self.config, 'PRIVATE_EC2', False) in self.architecture_flags
        self.allow_list = self.config.get("allowList", [])
        self.platform_name = self.config["platform_name"] or self.project_name
        self.state_name = self.config["state_name"] or self.platform_name
        self.rds_name = self.config["rds_name"] or project_name
        self.domains = self.config.get("domains", [])
        self.primary_domain = self.domains[0] if self.domains else "www.somethingamazing.io"
        self.author_email = self.config.get("author_email", "info@buzzerboy.com") 
        self.container_name = self.config.get("container_name", "web")

        if "region" not in self.config or not self.config["region"]:
            self.config["region"] = self.config.get('region', 'us-east-1')
        self.deployment_bucket = (
            self.config["deployment_bucket"]
            or f"{self.platform_name}-deployments"
        )
        self.storage_bucket = (
            self.config["storage_bucket"]
            or self.project_name
        )
        # Backend bucket logic
        backend_bucket_name = kwargs.get('state_bucket_name', f"{self.project_name}-tfstate")
        self.backend_bucket_name = self.get_or_create_backend_bucket(backend_bucket_name, self.config["region"])



        super().__init__(scope, id)
        # Register AWS provider for this stack

        self.configure_s3_backend()
        AwsProvider(self, "aws", region=self.config["region"])
        self.iam_role = self.create_iam_role()
        self.iam_profile = IamInstanceProfile(
            self,
            "ec2InstanceProfile",
            name=f"{self.project_name}-instance-profile",
            role=self.iam_role.name
        )
        self.ecr_repo = self.get_or_create_ecr()
        self.ecr_repository_url = f"{self.get_account_id()}.dkr.ecr.{self.config['region']}.amazonaws.com/{self.project_name}"
        self.ecr_registry = f"{self.get_account_id()}.dkr.ecr.{self.config['region']}.amazonaws.com"
        self.rds = self.get_or_create_rds()
        self.deployment_bucket_resource = self.create_s3_bucket(self.deployment_bucket)
        self.uploaded_scripts = self.upload_runtime_files()
        self.storage_bucket_resource = self.create_s3_bucket(self.storage_bucket)
        self.secret = SecretsmanagerSecret(
            self,
            "projectConfigSecret",
            name=self.secret_name
        )
        self.keypair, self.keypair_secret = self.create_keypair_and_secret()
        self.security_group = self.create_security_group()
        self.ec2_instance = self.create_ec2_instance()
        self.create_resource_list_output()
        self.create_additional_outputs()

    def configure_s3_backend(self):
        """
        Configure the S3 backend for Terraform state using the backend bucket, project name, and region.
        """
        # Replace the default local backend with S3 to avoid duplicate backend blocks.
        S3Backend(
            self,
            bucket=self.backend_bucket_name,
            key=f"{self.project_name}/terraform.tfstate",
            region=self.config["region"]
        )



    def create_resource_list_output(self):
        TerraformOutput(
            self,
            "resourceList",
            value=[
                self.iam_role.name,
                self.iam_profile.name,
                self.ecr_repo.name,
                self.deployment_bucket_resource.bucket,
                self.storage_bucket_resource.bucket,
                self.secret.name,
                self.keypair.key_name,
                getattr(self.keypair.secret, 'name', None),
                self.security_group.name,
                self.ec2_instance.id
            ]
        )


    def get_template_vars(self) -> dict:
        return {
            "ecr_repository_url": self.ecr_repository_url,
            "ecr_registry": self.ecr_registry,
            "deployment_bucket": self.deployment_bucket,
            "project_name": self.project_name,
            "primary_domain": self.primary_domain,
            "aws_account_id": self.get_account_id(),
            "author_email": self.author_email,
            "container_name": self.container_name,
            "secret_name": self.secret_name,
            "region": self.config["region"],
            "ec2_instance_id": "${aws_instance.ec2Instance.id}",
            "docker-compose-s3-url": f"s3://{self.deployment_bucket}/{self.project_name}/runtime/docker-compose.yml",
            "dockerfile-s3-url": f"s3://{self.deployment_bucket}/{self.project_name}/runtime/Dockerfile",
            "nginx-config-s3-url": f"s3://{self.deployment_bucket}/{self.project_name}/runtime/nginx/conf.d/1.conf",\
        }
    
    def create_additional_outputs(self):
        template_vars = self.get_template_vars()
        rendered = [
            self._render_template(message, template_vars)
            for message in self.additional_outputs
        ]
        TerraformOutput(
            self,
            "additional_outputs",
            value=rendered,
            description="Helpful post-deploy messages with resolved values"
        )

    def _render_template(self, content: str, template_vars: dict) -> str:
        for key, value in template_vars.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        return content

    def create_iam_role(self):
        role = IamRole(
            self,
            "ec2Role",
            name=f"{self.project_name}-role",
            assume_role_policy="""{
              \"Version\": \"2012-10-17\",
              \"Statement\": [
                {
                  \"Effect\": \"Allow\",
                  \"Principal\": { \"Service\": \"ec2.amazonaws.com\" },
                  \"Action\": \"sts:AssumeRole\"
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

    def get_or_create_ecr(self):
        repo_name = self.project_name
        return EcrRepository(
            self,
            "ecrRepo",
            name=repo_name,
            force_delete=True
        )

    def get_or_create_rds(self):
        if not self.enable_rds:
            return None
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

    def create_s3_bucket(self, bucket_name: str):
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

    def create_security_group(self):
        if self.allow_list:
            cidr_blocks = [ip if "/" in ip else f"{ip}/32" for ip in self.allow_list]
        else:
            cidr_blocks = ["0.0.0.0/0"]
        ingress_rules = []
        if not self.is_private_ec2 or self.allow_list:
            ingress_rules.append(SecurityGroupIngress(
                from_port=80,
                to_port=80,
                protocol="tcp",
                cidr_blocks=cidr_blocks,
                description="HTTP access"
            ))
            ingress_rules.append(SecurityGroupIngress(
                from_port=443,
                to_port=443,
                protocol="tcp",
                cidr_blocks=cidr_blocks,
                description="HTTPS access"
            ))
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

    def create_keypair_and_secret(self):
        from imports.aws.key_pair import KeyPair
        from imports.aws.secretsmanager_secret import SecretsmanagerSecret
        from imports.aws.secretsmanager_secret_version import SecretsmanagerSecretVersion
        import tempfile
        import subprocess
        key_name = f"{self.project_name}-keypair"
        keypair_secret_name = f"{self.project_name}-private-keypair"
        existing_private_key = self._get_existing_secret_value(keypair_secret_name)
        if existing_private_key:
            private_key = existing_private_key
            public_key = self._public_key_from_private(private_key)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                private_key_path = os.path.join(tmpdir, f"{key_name}.pem")
                public_key_path = os.path.join(tmpdir, f"{key_name}.pub")
                subprocess.run([
                    "ssh-keygen", "-t", "rsa", "-b", "2048", "-f", private_key_path, "-N", ""
                ], check=True)
                # Explicitly generate the public key file from the private key
                with open(public_key_path, "w") as pubf:
                    subprocess.run([
                        "ssh-keygen", "-y", "-f", private_key_path
                    ], check=True, stdout=pubf)
                with open(public_key_path, "r") as pubf:
                    public_key = pubf.read().strip()
                with open(private_key_path, "r") as privf:
                    private_key = privf.read().strip()
        keypair = KeyPair(
            self,
            "ec2KeyPair",
            key_name=key_name,
            public_key=public_key
        )
        secret = SecretsmanagerSecret(
            self,
            "ec2KeyPairSecret",
            name=keypair_secret_name
        )
        secret_version = SecretsmanagerSecretVersion(
            self,
            "ec2KeyPairSecretVersion",
            secret_id=secret.id,
            secret_string=private_key
        )
        keypair.secret = secret
        keypair.secret_version = secret_version
        return keypair, secret

    def _get_existing_secret_value(self, secret_name: str):
        client = boto3.client("secretsmanager", region_name=self.config["region"])
        try:
            response = client.get_secret_value(SecretId=secret_name)
        except client.exceptions.ResourceNotFoundException:
            return None
        secret_string = response.get("SecretString")
        return secret_string.strip() if secret_string else None

    def _public_key_from_private(self, private_key: str) -> str:
        import tempfile
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            private_key_path = os.path.join(tmpdir, "existing-key.pem")
            with open(private_key_path, "w") as privf:
                privf.write(private_key.strip() + "\n")
            os.chmod(private_key_path, 0o600)
            result = subprocess.run(
                ["ssh-keygen", "-y", "-f", private_key_path],
                check=True,
                stdout=subprocess.PIPE,
                text=True
            )
            return result.stdout.strip()

    def create_ec2_instance(self):
        user_data = self.generate_user_data()
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

    def generate_user_data(self) -> str:
        user_data = ArchitectureHelpers.getFormattedTextFromFile(
            "user_data.sh",
            {
                "deployment_bucket": self.deployment_bucket,
                "project_name": self.project_name
            }
        )
        return user_data

    def upload_runtime_files(self) -> list:
        template_vars = self.get_template_vars()

        return upload_runtime_files(
            self, 
            self.deployment_bucket, 
            self.project_name, 
            template_vars
        )

    def get_account_id(self) -> str:
        sts = boto3.client("sts", region_name=self.config["region"])
        self.aws_account_id = sts.get_caller_identity()["Account"]
        return sts.get_caller_identity()["Account"]

    def build_and_push_initial_image(self):
        return ""
        hello_world_dir = os.path.join(os.path.dirname(__file__), "hello-world")
        if not os.path.exists(hello_world_dir):
            print(f"[WARNING] Hello-world directory not found: {hello_world_dir}")
            return
        print(f"[INFO] After Terraform deployment, manually build and push Docker image to {self.ecr_repository_url}")
