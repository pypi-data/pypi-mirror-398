
class ArchitectureMaker:


    @staticmethod
    def auto_main(definitions):
        from cdktf import App
        from .DockerEC2 import DockerEC2
        from .DockerEC2Standalone import DockerEC2Standalone

        if not isinstance(definitions, dict):
            raise TypeError("definitions must be a dictionary")

        architecture_class = DockerEC2Standalone

        required_keys = ["product", "app", "tier", "organization", "region"]
        missing_keys = [key for key in required_keys if not definitions.get(key)]
        if missing_keys:
            raise ValueError(f"Missing required definitions: {', '.join(missing_keys)}")

        app = App()

        region = definitions.get("region")
        archetype = architecture_class.get_archetype(
            product=definitions.get("product"),
            app=definitions.get("app"),
            tier=definitions.get("tier"),
            organization=definitions.get("organization"),
            region=region,
        )

        project_name = definitions.get("project_name") or archetype.get_project_name()
        platform_name = definitions.get("platform_name") or project_name
        secret_name = definitions.get("secret_name") or archetype.get_secret_name()

        architecture_flags = definitions.get("architecture_flags")
        if architecture_flags is None:
            architecture_flags = definitions.get("architectureFlags")

        reserved_keys = {
            "architecture_class",
            "stack_class",
            "product",
            "app",
            "tier",
            "organization",
            "project_name",
            "platform_name",
            "secret_name",
            "architecture_flags",
            "architectureFlags",
        }

        stack_kwargs = {key: value for key, value in definitions.items() if key not in reserved_keys}

        stack_kwargs["platform_name"] = platform_name
        stack_kwargs["secret_name"] = secret_name
        if architecture_flags is not None:
            stack_kwargs["architecture_flags"] = architecture_flags

        if "domains" not in stack_kwargs:
            stack_kwargs["domains"] = []

        stack = architecture_class(
            app,
            f"{project_name}-stack",
            project_name=project_name,
            **stack_kwargs,
        )

        app.synth()

        template_vars = stack.get_template_vars()
        rendered_messages = [
            stack._render_template(message, template_vars)
            for message in stack.additional_outputs
        ]

        green_bold = "\033[1;32m"
        reset = "\033[0m"
        for message in rendered_messages:
            print(f"{green_bold}{message}{reset}")

        print(f"[INFO] Successfully synthesized Terraform configuration for '{project_name}'")
        print("[INFO] Run 'cdktf diff' to preview changes")
        print("[INFO] Run 'cdktf deploy' to apply changes")
