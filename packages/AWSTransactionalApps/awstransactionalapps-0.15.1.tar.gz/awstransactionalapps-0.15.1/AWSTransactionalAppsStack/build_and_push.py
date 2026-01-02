#!/usr/bin/env python3
"""
Build and push Docker image to ECR.
This script is called after ECR repository creation.
"""
import subprocess
import sys
import os


def build_and_push(region: str, repository_url: str, hello_world_dir: str):
    """
    Build and push the hello-world Docker image to ECR.
    
    :param region: AWS region
    :param repository_url: Full ECR repository URL
    :param hello_world_dir: Path to hello-world directory
    """
    try:
        print(f"[INFO] Building and pushing Docker image to {repository_url}...")
        
        # Extract registry from repository URL
        registry = repository_url.split('/')[0]
        
        # Authenticate to ECR
        print(f"[INFO] Authenticating to ECR...")
        login_cmd = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {registry}"
        subprocess.run(login_cmd, shell=True, check=True)
        
        # Build the image
        print(f"[INFO] Building Docker image...")
        subprocess.run(
            ["docker", "build", "-t", f"{repository_url}:latest", "."],
            cwd=hello_world_dir,
            check=True
        )
        
        # Push the image
        print(f"[INFO] Pushing Docker image...")
        subprocess.run(
            ["docker", "push", f"{repository_url}:latest"],
            check=True
        )
        
        print(f"[INFO] Successfully pushed image to ECR: {repository_url}:latest")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to build/push Docker image: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: build_and_push.py <region> <repository_url> <hello_world_dir>")
        sys.exit(1)
    
    region = sys.argv[1]
    repository_url = sys.argv[2]
    hello_world_dir = sys.argv[3]
    
    success = build_and_push(region, repository_url, hello_world_dir)
    sys.exit(0 if success else 1)
