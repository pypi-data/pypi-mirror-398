# uploader.py
# Module to upload runtime scripts to S3 using Terraform S3Object resources

import os
from cdktf import TerraformResourceLifecycle
from imports.aws.s3_object import S3Object


class ScriptUploader:
    """
    Uploads all runtime scripts from the scripts/ folder to S3,
    preserving the folder hierarchy.
    """

    def __init__(self, scope, deployment_bucket: str, project_name: str, template_vars: dict = None, deployment_bucket_resource=None):
        """
        Initialize the ScriptUploader.

        :param scope: The Terraform scope (typically `self` from the stack)
        :param deployment_bucket: Name of the S3 deployment bucket
        :param project_name: Project name used as prefix in S3 keys
        :param template_vars: Dictionary of variables for template rendering
        :param deployment_bucket_resource: The actual S3 bucket resource object (for depends_on)
        """
        self.scope = scope
        self.deployment_bucket = deployment_bucket
        self.project_name = project_name
        self.template_vars = template_vars or {}
        self.scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
        self.uploaded_objects = []
        self.deployment_bucket_resource = deployment_bucket_resource

    def upload_all(self) -> list:
        """
        Walk the scripts directory and upload all files to S3.
        
        Returns a list of S3Object resources created.
        """
        if not os.path.exists(self.scripts_dir):
            print(f"[WARNING] Scripts directory not found: {self.scripts_dir}")
            return []

        for root, dirs, files in os.walk(self.scripts_dir):
            for filename in files:
                local_path = os.path.join(root, filename)

                # Get relative path from scripts directory
                relative_path = os.path.relpath(local_path, self.scripts_dir)
                print(f"[DEBUG] Found script file: {local_path} (relative: {relative_path})")

                # Build S3 key: <deployment_bucket>/<relative_path> (force use of deployment_bucket variable)
                s3_key = f"{self.project_name}/{relative_path}"
                print(f"[DEBUG] Initial S3 key: {s3_key}")

                # Remove duplicate bucket prefix if present
                if s3_key.startswith(f"{self.deployment_bucket}/{self.deployment_bucket}/"):
                    s3_key = s3_key.replace(f"{self.deployment_bucket}/{self.deployment_bucket}/", f"{self.project_name}/")

                s3_key = s3_key.replace(f"{self.deployment_bucket}/{self.deployment_bucket}/", f"{self.project_name}/")
                print(f"[DEBUG] Preparing to upload {local_path} to s3://{s3_key}")

                # Create a unique Terraform resource ID
                resource_id = self._make_resource_id(relative_path)
                # Read file content
                with open(local_path, "r") as f:
                    content = f.read()
                # Apply template rendering if this is a template file
                content = self._render_template(content, relative_path)
                # Create S3Object resource
                s3_obj = S3Object(
                    self.scope,
                    resource_id,
                    bucket=self.deployment_bucket,
                    key=s3_key,
                    content=content,
                    content_type=self._get_content_type(filename),
                    lifecycle=TerraformResourceLifecycle(ignore_changes=["content", "content_type"]),
                    depends_on=[self.deployment_bucket_resource] if self.deployment_bucket_resource is not None else None
                )
                self.uploaded_objects.append(s3_obj)
                print(f"[INFO] Registered S3 upload: s3://{self.deployment_bucket}/{s3_key}")
        return self.uploaded_objects

    def _make_resource_id(self, relative_path: str) -> str:
        """
        Create a valid Terraform resource ID from a file path.
        """
        # Replace path separators and dots with underscores
        resource_id = relative_path.replace("/", "_").replace("\\", "_")
        resource_id = resource_id.replace(".", "_").replace("-", "_")
        return f"script_{resource_id}"

    def _get_content_type(self, filename: str) -> str:
        """
        Determine content type based on file extension.
        """
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            ".sh": "text/x-shellscript",
            ".yml": "text/yaml",
            ".yaml": "text/yaml",
            ".json": "application/json",
            ".service": "text/plain",
            ".timer": "text/plain",
        }
        return content_types.get(ext, "text/plain")
    
    def _render_template(self, content: str, relative_path: str) -> str:
        """
        Render template variables in file content.
        
        :param content: File content
        :param relative_path: Relative path to determine if template rendering is needed
        :return: Rendered content
        """
        # Apply template rendering to all files if template_vars are provided
        if self.template_vars:
            for key, value in self.template_vars.items():
                content = content.replace(f"{{{{{key}}}}}", str(value))
        return content


def upload_runtime_files(scope, deployment_bucket: str, project_name: str, template_vars: dict = None) -> list:
    """
    Convenience function to upload all runtime scripts to S3.
    
    :param scope: The Terraform scope (typically `self` from the stack)
    :param deployment_bucket: Name of the S3 deployment bucket
    :param project_name: Project name used as prefix in S3 keys
    :param template_vars: Dictionary of variables for template rendering
    :returns: List of S3Object resources created
    """
    # Try to get deployment_bucket_resource from scope if present
    deployment_bucket_resource = getattr(scope, 'deployment_bucket_resource', None)
    uploader = ScriptUploader(scope, deployment_bucket, project_name, template_vars, deployment_bucket_resource)
    return uploader.upload_all()

        # CLI entrypoint for local-exec usage
    if __name__ == "__main__":
        import argparse
        parser = argparse.ArgumentParser(description="Upload runtime files to S3 using ScriptUploader.")
        parser.add_argument("--bucket", required=True, help="Deployment S3 bucket name")
        parser.add_argument("--project", required=True, help="Project name (used as prefix, but will be ignored if you patched for bucket-only)")
        parser.add_argument("--template-vars", default=None, help="JSON string of template vars (optional)")
        args = parser.parse_args()

        import json
        template_vars = json.loads(args.template_vars) if args.template_vars else None
        uploader = ScriptUploader(None, args.bucket, args.project, template_vars)
        uploader.upload_all()
        print("[INFO] Upload complete via CLI.")
