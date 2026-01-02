#!/usr/bin/env python3
"""
SSH Connection Script for AWS EC2 Instances

This script automates the process of connecting to EC2 instances by:
1. Determining EC2 instance name and secret name from product, app tier, and organization
2. Downloading the SSH keypair from AWS Secrets Manager
3. Updating the security group to allow SSH from current IP
4. Establishing SSH connection to the EC2 instance

Prerequisites:
- AWS CLI installed and configured with appropriate credentials
- boto3 Python library
- User must have permissions for EC2, Secrets Manager, and security group operations
"""

import argparse
import boto3
import json
import os
import sys
import subprocess
import tempfile
import requests
from pathlib import Path


class EC2SSHConnector:
    """Handles EC2 SSH connections with automatic security group and keypair management."""
    
    def __init__(self, product, app, tier, organization, platform_name=None, region='ca-central-1'):
        """
        Initialize the SSH connector.
        
        Args:
            product: Product name
            app: Application name
            tier: Environment tier (e.g., dev, staging, prod)
            organization: Organization name
            platform_name: Platform name (defaults to organization-product-app-tier)
            region: AWS region (default: ca-central-1)
        """
        self.product = product
        self.app = app
        self.tier = tier
        self.organization = organization
        self.region = region
        
        # AWS clients
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.secrets_client = boto3.client('secretsmanager', region_name=region)
        
        # Derived names based on naming convention
        self.project_name = f"{product}-{app}-{tier}"
        self.platform_name = platform_name or f"{organization}-{product}-{app}-{tier}"
        self.ec2_instance_name = self.project_name
        self.secret_name = f"{self.platform_name}/{self.project_name}/{self.project_name}-keypair"
        
        # Runtime variables
        self.instance_id = None
        self.public_ip = None
        self.security_group_id = None
        self.keypair_path = None
        self.current_ip = None
        
    def get_current_public_ip(self):
        """Get the current public IP address of this machine."""
        try:
            # Try ipify first
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            self.current_ip = response.json()['ip']
            print(f"✓ Current public IP: {self.current_ip}")
            return self.current_ip
        except Exception as e:
            print(f"⚠ Warning: Could not determine public IP: {e}")
            print("  Security group will not be updated automatically.")
            return None
    
    def find_ec2_instance(self):
        """Find the EC2 instance by name tag."""
        print(f"\n🔍 Looking for EC2 instance: {self.ec2_instance_name}")
        
        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [self.ec2_instance_name]},
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                instances.extend(reservation['Instances'])
            
            if not instances:
                print(f"✗ No EC2 instance found with name: {self.ec2_instance_name}")
                return False
            
            if len(instances) > 1:
                print(f"⚠ Warning: Multiple instances found with name {self.ec2_instance_name}")
                print("  Using the first one.")
            
            instance = instances[0]
            self.instance_id = instance['InstanceId']
            self.public_ip = instance.get('PublicIpAddress')
            
            # Get security group
            if instance.get('SecurityGroups'):
                self.security_group_id = instance['SecurityGroups'][0]['GroupId']
            
            state = instance['State']['Name']
            print(f"✓ Found instance: {self.instance_id}")
            print(f"  State: {state}")
            print(f"  Public IP: {self.public_ip or 'N/A'}")
            print(f"  Security Group: {self.security_group_id or 'N/A'}")
            
            if state != 'running':
                print(f"\n⚠ Warning: Instance is in '{state}' state, not 'running'")
                response = input("  Do you want to start it? (y/n): ")
                if response.lower() == 'y':
                    self.start_instance()
                else:
                    print("✗ Cannot SSH to a non-running instance")
                    return False
            
            if not self.public_ip:
                print("✗ Instance does not have a public IP address")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Error finding EC2 instance: {e}")
            return False
    
    def start_instance(self):
        """Start a stopped EC2 instance and wait for it to be running."""
        print(f"\n🚀 Starting instance {self.instance_id}...")
        
        try:
            self.ec2_client.start_instances(InstanceIds=[self.instance_id])
            
            # Wait for instance to be running
            print("  Waiting for instance to start...")
            waiter = self.ec2_client.get_waiter('instance_running')
            waiter.wait(InstanceIds=[self.instance_id])
            
            # Refresh instance info to get public IP
            response = self.ec2_client.describe_instances(InstanceIds=[self.instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            self.public_ip = instance.get('PublicIpAddress')
            
            print(f"✓ Instance started successfully")
            print(f"  Public IP: {self.public_ip}")
            
        except Exception as e:
            print(f"✗ Error starting instance: {e}")
            raise
    
    def download_keypair(self):
        """Download the SSH keypair from AWS Secrets Manager."""
        print(f"\n🔑 Downloading keypair from Secrets Manager: {self.secret_name}")
        
        try:
            response = self.secrets_client.get_secret_value(SecretId=self.secret_name)
            secret_string = response['SecretString']
            
            # Parse the secret (it should contain the private key)
            try:
                secret_data = json.loads(secret_string)
                private_key = secret_data.get('private_key') or secret_data.get('privateKey')
            except json.JSONDecodeError:
                # Secret might be the raw private key
                private_key = secret_string
            
            if not private_key:
                print("✗ Private key not found in secret")
                return False
            
            # Create temporary file for the keypair
            temp_dir = tempfile.gettempdir()
            self.keypair_path = os.path.join(temp_dir, f"{self.project_name}-keypair.pem")
            
            with open(self.keypair_path, 'w') as f:
                f.write(private_key)
            
            # Set proper permissions (read-only for owner)
            os.chmod(self.keypair_path, 0o400)
            
            print(f"✓ Keypair downloaded to: {self.keypair_path}")
            return True
            
        except self.secrets_client.exceptions.ResourceNotFoundException:
            print(f"✗ Secret not found: {self.secret_name}")
            print("  Please check the secret name or create the secret in Secrets Manager")
            return False
        except Exception as e:
            print(f"✗ Error downloading keypair: {e}")
            return False
    
    def update_security_group(self):
        """Update the security group to allow SSH from current IP."""
        if not self.current_ip or not self.security_group_id:
            print("\n⚠ Skipping security group update (missing IP or security group)")
            return True
        
        print(f"\n🔒 Updating security group {self.security_group_id}")
        
        try:
            # Check if rule already exists
            response = self.ec2_client.describe_security_groups(
                GroupIds=[self.security_group_id]
            )
            
            security_group = response['SecurityGroups'][0]
            ssh_rule_exists = False
            
            for rule in security_group.get('IpPermissions', []):
                if rule.get('FromPort') == 22 and rule.get('ToPort') == 22:
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == f"{self.current_ip}/32":
                            ssh_rule_exists = True
                            break
            
            if ssh_rule_exists:
                print(f"✓ SSH rule already exists for {self.current_ip}/32")
                return True
            
            # Add SSH rule
            print(f"  Adding SSH rule for {self.current_ip}/32...")
            self.ec2_client.authorize_security_group_ingress(
                GroupId=self.security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [
                            {
                                'CidrIp': f"{self.current_ip}/32",
                                'Description': f'SSH access from current IP (auto-added)'
                            }
                        ]
                    }
                ]
            )
            
            print(f"✓ SSH rule added successfully")
            return True
            
        except self.ec2_client.exceptions.ClientError as e:
            if 'InvalidPermission.Duplicate' in str(e):
                print(f"✓ SSH rule already exists for {self.current_ip}/32")
                return True
            else:
                print(f"⚠ Warning: Could not update security group: {e}")
                print("  You may need to manually add SSH access for your IP")
                return True  # Don't fail, just warn
        except Exception as e:
            print(f"⚠ Warning: Error updating security group: {e}")
            return True  # Don't fail, just warn
    
    def connect_ssh(self, username='ec2-user'):
        """Establish SSH connection to the EC2 instance."""
        if not self.keypair_path or not self.public_ip:
            print("✗ Cannot establish SSH connection (missing keypair or IP)")
            return False
        
        print(f"\n🔗 Connecting to {username}@{self.public_ip}...")
        print(f"   Using keypair: {self.keypair_path}")
        print(f"\n{'='*60}")
        
        ssh_command = [
            'ssh',
            '-i', self.keypair_path,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'{username}@{self.public_ip}'
        ]
        
        try:
            # Execute SSH command
            subprocess.run(ssh_command)
            return True
        except Exception as e:
            print(f"\n✗ Error during SSH connection: {e}")
            return False
        finally:
            # Clean up keypair file
            self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.keypair_path and os.path.exists(self.keypair_path):
            try:
                os.remove(self.keypair_path)
                print(f"\n🧹 Cleaned up temporary keypair file")
            except Exception as e:
                print(f"\n⚠ Warning: Could not delete temporary keypair: {e}")
    
    def run(self, username='ec2-user'):
        """
        Main execution flow.
        
        Args:
            username: SSH username (default: ec2-user)
        
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"AWS EC2 SSH Connector")
        print(f"{'='*60}")
        print(f"Product:      {self.product}")
        print(f"App:          {self.app}")
        print(f"Tier:         {self.tier}")
        print(f"Organization: {self.organization}")
        print(f"Region:       {self.region}")
        print(f"{'='*60}")
        print(f"Project Name: {self.project_name}")
        print(f"Platform:     {self.platform_name}")
        print(f"EC2 Name:     {self.ec2_instance_name}")
        print(f"Secret Name:  {self.secret_name}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Get current IP
            self.get_current_public_ip()
            
            # Step 2: Find EC2 instance
            if not self.find_ec2_instance():
                return False
            
            # Step 3: Download keypair
            if not self.download_keypair():
                return False
            
            # Step 4: Update security group
            if not self.update_security_group():
                return False
            
            # Step 5: Connect via SSH
            if not self.connect_ssh(username):
                return False
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠ Operation cancelled by user")
            self.cleanup()
            return False
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            self.cleanup()
            return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='SSH into AWS EC2 instances with automatic configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s myproduct myapp dev myorg
  %(prog)s myproduct myapp prod myorg --region us-east-1
  %(prog)s myproduct myapp staging myorg --platform-name custom-platform
  %(prog)s myproduct myapp dev myorg --username ubuntu
        """
    )
    
    parser.add_argument('product', help='Product name')
    parser.add_argument('app', help='Application name')
    parser.add_argument('tier', help='Environment tier (e.g., dev, staging, prod)')
    parser.add_argument('organization', help='Organization name')
    parser.add_argument('--platform-name', help='Platform name (defaults to organization-product-app-tier)')
    parser.add_argument('--region', default='ca-central-1', help='AWS region (default: ca-central-1)')
    parser.add_argument('--username', default='ec2-user', help='SSH username (default: ec2-user)')
    
    args = parser.parse_args()
    
    connector = EC2SSHConnector(
        product=args.product,
        app=args.app,
        tier=args.tier,
        organization=args.organization,
        platform_name=args.platform_name,
        region=args.region
    )
    
    success = connector.run(username=args.username)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
