#!/usr/bin/env python3
"""
Deploy script for building and pushing Docker images to AWS ECR.

This script parses docker-compose.yml files, builds Docker images, and pushes them to ECR.
It can be run as a module:
    python3 -m AWSTransactionalApps.AWSTransactionalAppsStack.Operations.Deploy [options]

The script automatically:
1. Parses docker-compose.yml to find services with build contexts
2. Authenticates with AWS ECR
3. Builds Docker images for each service
4. Tags images appropriately for ECR
5. Pushes images to the specified ECR repository
"""

import argparse
import subprocess
import sys
import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ECRDeployer:
    """Handles building and pushing Docker images to AWS ECR."""

    def __init__(
        self,
        product: str,
        app: str,
        tier: str,
        organization: str,
        region: str = "us-east-1",
        compose_file: str = "docker-compose.yml",
        aws_profile: Optional[str] = None,
    ):
        """
        Initialize the ECR deployer.

        Args:
            product: Product name
            app: Application name
            tier: Environment tier (dev, staging, prod, etc.)
            organization: Organization name
            region: AWS region
            compose_file: Path to docker-compose.yml file
            aws_profile: AWS profile to use (optional)
        """
        self.product = product
        self.app = app
        self.tier = tier
        self.organization = organization
        self.region = region
        self.compose_file = Path(compose_file)
        self.aws_profile = aws_profile

        # Construct ECR repository name
        # Format: organization-product-app-tier
        self.ecr_repo_name = f"{organization}-{product}-{app}-{tier}"

        # Will be set after getting account ID
        self.account_id: Optional[str] = None
        self.ecr_registry: Optional[str] = None
        self.ecr_repository_url: Optional[str] = None

    def get_aws_account_id(self) -> str:
        """Get AWS account ID using AWS CLI."""
        try:
            cmd = ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"]
            if self.aws_profile:
                cmd.extend(["--profile", self.aws_profile])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            account_id = result.stdout.strip()
            print(f"[INFO] AWS Account ID: {account_id}")
            return account_id
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to get AWS account ID: {e.stderr}")
            raise

    def authenticate_ecr(self) -> bool:
        """Authenticate Docker to AWS ECR."""
        try:
            print(f"[INFO] Authenticating to ECR in region {self.region}...")

            # Get ECR login password
            cmd = ["aws", "ecr", "get-login-password", "--region", self.region]
            if self.aws_profile:
                cmd.extend(["--profile", self.aws_profile])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            password = result.stdout.strip()

            # Login to Docker
            login_cmd = [
                "docker",
                "login",
                "--username",
                "AWS",
                "--password-stdin",
                self.ecr_registry,
            ]

            subprocess.run(
                login_cmd,
                input=password,
                text=True,
                check=True,
                capture_output=True,
            )

            print(f"[INFO] Successfully authenticated to ECR registry: {self.ecr_registry}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to authenticate to ECR: {e.stderr}")
            return False

    def parse_docker_compose(self) -> Dict[str, dict]:
        """
        Parse docker-compose.yml and extract services with build contexts.

        Returns:
            Dictionary mapping service names to their build configurations
        """
        if not self.compose_file.exists():
            raise FileNotFoundError(f"Docker compose file not found: {self.compose_file}")

        print(f"[INFO] Parsing docker-compose file: {self.compose_file}")

        with open(self.compose_file, "r") as f:
            compose_data = yaml.safe_load(f)

        services = compose_data.get("services", {})
        buildable_services = {}

        for service_name, service_config in services.items():
            if "build" in service_config:
                build_config = service_config["build"]

                # Handle both simple string and complex build configurations
                if isinstance(build_config, str):
                    build_context = build_config
                    dockerfile = "Dockerfile"
                elif isinstance(build_config, dict):
                    build_context = build_config.get("context", ".")
                    dockerfile = build_config.get("dockerfile", "Dockerfile")
                else:
                    continue

                buildable_services[service_name] = {
                    "context": build_context,
                    "dockerfile": dockerfile,
                }

        print(f"[INFO] Found {len(buildable_services)} buildable service(s): {', '.join(buildable_services.keys())}")
        return buildable_services

    def build_image(self, service_name: str, build_config: dict) -> bool:
        """
        Build a Docker image for a service.

        Args:
            service_name: Name of the service
            build_config: Build configuration containing context and dockerfile

        Returns:
            True if successful, False otherwise
        """
        context = build_config["context"]
        dockerfile = build_config["dockerfile"]

        # Resolve context path relative to compose file location
        context_path = (self.compose_file.parent / context).resolve()

        if not context_path.exists():
            print(f"[ERROR] Build context not found: {context_path}")
            return False

        # Construct image tag
        image_tag = f"{self.ecr_repository_url}:{service_name}-latest"

        print(f"[INFO] Building image for service '{service_name}'...")
        print(f"       Context: {context_path}")
        print(f"       Dockerfile: {dockerfile}")
        print(f"       Tag: {image_tag}")

        try:
            cmd = [
                "docker",
                "build",
                "-f",
                dockerfile,
                "-t",
                image_tag,
                ".",
            ]

            subprocess.run(
                cmd,
                cwd=context_path,
                check=True,
            )

            print(f"[INFO] Successfully built image: {image_tag}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to build image for service '{service_name}': {e}")
            return False

    def push_image(self, service_name: str) -> bool:
        """
        Push a Docker image to ECR.

        Args:
            service_name: Name of the service

        Returns:
            True if successful, False otherwise
        """
        image_tag = f"{self.ecr_repository_url}:{service_name}-latest"

        print(f"[INFO] Pushing image: {image_tag}")

        try:
            subprocess.run(
                ["docker", "push", image_tag],
                check=True,
            )

            print(f"[INFO] Successfully pushed image: {image_tag}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to push image '{image_tag}': {e}")
            return False

    def ensure_ecr_repository(self) -> bool:
        """
        Ensure ECR repository exists, create if it doesn't.

        Returns:
            True if repository exists or was created, False otherwise
        """
        try:
            print(f"[INFO] Checking if ECR repository '{self.ecr_repo_name}' exists...")

            cmd = [
                "aws",
                "ecr",
                "describe-repositories",
                "--repository-names",
                self.ecr_repo_name,
                "--region",
                self.region,
            ]
            if self.aws_profile:
                cmd.extend(["--profile", self.aws_profile])

            subprocess.run(
                cmd,
                capture_output=True,
                check=True,
            )

            print(f"[INFO] ECR repository '{self.ecr_repo_name}' exists")
            return True

        except subprocess.CalledProcessError:
            # Repository doesn't exist, create it
            print(f"[INFO] ECR repository '{self.ecr_repo_name}' not found, creating...")

            try:
                cmd = [
                    "aws",
                    "ecr",
                    "create-repository",
                    "--repository-name",
                    self.ecr_repo_name,
                    "--region",
                    self.region,
                ]
                if self.aws_profile:
                    cmd.extend(["--profile", self.aws_profile])

                subprocess.run(
                    cmd,
                    capture_output=True,
                    check=True,
                )

                print(f"[INFO] Successfully created ECR repository: {self.ecr_repo_name}")
                return True

            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to create ECR repository: {e.stderr}")
                return False

    def deploy(self) -> bool:
        """
        Execute the full deployment pipeline.

        Returns:
            True if all steps successful, False otherwise
        """
        try:
            # Step 1: Get AWS account ID
            self.account_id = self.get_aws_account_id()
            self.ecr_registry = f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"
            self.ecr_repository_url = f"{self.ecr_registry}/{self.ecr_repo_name}"

            print(f"\n{'=' * 70}")
            print(f"ECR Deployment Configuration")
            print(f"{'=' * 70}")
            print(f"Organization:     {self.organization}")
            print(f"Product:          {self.product}")
            print(f"App:              {self.app}")
            print(f"Tier:             {self.tier}")
            print(f"Region:           {self.region}")
            print(f"ECR Repository:   {self.ecr_repo_name}")
            print(f"Repository URL:   {self.ecr_repository_url}")
            print(f"Compose File:     {self.compose_file}")
            print(f"{'=' * 70}\n")

            # Step 2: Ensure ECR repository exists
            if not self.ensure_ecr_repository():
                return False

            # Step 3: Parse docker-compose.yml
            services = self.parse_docker_compose()

            if not services:
                print("[WARNING] No services with build configurations found in docker-compose.yml")
                return False

            # Step 4: Authenticate to ECR
            if not self.authenticate_ecr():
                return False

            # Step 5: Build and push each service
            failed_services = []

            for service_name, build_config in services.items():
                print(f"\n{'=' * 70}")
                print(f"Processing service: {service_name}")
                print(f"{'=' * 70}")

                if not self.build_image(service_name, build_config):
                    failed_services.append(service_name)
                    continue

                if not self.push_image(service_name):
                    failed_services.append(service_name)
                    continue

            # Summary
            print(f"\n{'=' * 70}")
            print(f"Deployment Summary")
            print(f"{'=' * 70}")
            print(f"Total services:   {len(services)}")
            print(f"Successful:       {len(services) - len(failed_services)}")
            print(f"Failed:           {len(failed_services)}")

            if failed_services:
                print(f"Failed services:  {', '.join(failed_services)}")
                print(f"{'=' * 70}\n")
                return False
            else:
                print(f"All services deployed successfully!")
                print(f"{'=' * 70}\n")
                return True

        except Exception as e:
            print(f"[ERROR] Deployment failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point for the deployment script."""
    parser = argparse.ArgumentParser(
        description="Build and push Docker images to AWS ECR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy using docker-compose.yml in current directory
  python3 -m AWSTransactionalApps.AWSTransactionalAppsStack.Operations.Deploy \\
      --product devops \\
      --app myapp \\
      --tier dev \\
      --organization myorg

  # Deploy with custom docker-compose.yml location
  python3 -m AWSTransactionalApps.AWSTransactionalAppsStack.Operations.Deploy \\
      --product devops \\
      --app myapp \\
      --tier prod \\
      --organization myorg \\
      --compose-file /path/to/docker-compose.yml \\
      --region us-west-2

  # Deploy with AWS profile
  python3 -m AWSTransactionalApps.AWSTransactionalAppsStack.Operations.Deploy \\
      --product devops \\
      --app myapp \\
      --tier staging \\
      --organization myorg \\
      --aws-profile production
        """,
    )

    parser.add_argument(
        "--product",
        required=True,
        help="Product name (e.g., devops, platform)",
    )

    parser.add_argument(
        "--app",
        required=True,
        help="Application name (e.g., myapp, transactionalapp)",
    )

    parser.add_argument(
        "--tier",
        required=True,
        help="Environment tier (e.g., dev, staging, prod, tst1)",
    )

    parser.add_argument(
        "--organization",
        required=True,
        help="Organization name (e.g., myorg, buzzerboy)",
    )

    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )

    parser.add_argument(
        "--compose-file",
        default="docker-compose.yml",
        help="Path to docker-compose.yml file (default: docker-compose.yml in current directory)",
    )

    parser.add_argument(
        "--aws-profile",
        help="AWS CLI profile to use (optional)",
    )

    args = parser.parse_args()

    # Create deployer and run
    deployer = ECRDeployer(
        product=args.product,
        app=args.app,
        tier=args.tier,
        organization=args.organization,
        region=args.region,
        compose_file=args.compose_file,
        aws_profile=args.aws_profile,
    )

    success = deployer.deploy()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
