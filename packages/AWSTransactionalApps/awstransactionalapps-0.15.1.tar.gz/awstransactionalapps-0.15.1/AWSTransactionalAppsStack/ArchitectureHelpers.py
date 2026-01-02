import os


class ArchitectureHelpers:
    @staticmethod
    def getFormattedTextFromFile(filename: str, jinjaDict: dict) -> str:
        """
        Load a text file and replace Jinja-style placeholders with values from the dictionary.

        :param filename: The path to the template file.
        :param jinjaDict: A dictionary where keys are Jinja placeholder names and values are replacements.
        :return: The formatted text with placeholders replaced.
        """
        # Get the directory where this module is located
        module_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(module_dir, "jinja", filename)
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace Jinja-style placeholders {{key}} with values from the dictionary
        for key, value in jinjaDict.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        
        return content

    @staticmethod
    def generate_resource_name(base_name: str, environment: str) -> str:
        """
        Generate a resource name by combining the base name with the environment.

        :param base_name: The base name of the resource.
        :param environment: The environment (e.g., 'dev', 'prod').
        :return: A combined resource name.
        """
        return f"{base_name}-{environment}"

    @staticmethod
    def validate_resource_name(name: str) -> bool:
        """
        Validate the resource name to ensure it meets naming conventions.

        :param name: The resource name to validate.
        :return: True if valid, False otherwise.
        """
        import re
        pattern = r'^[a-zA-Z0-9\-]{1,64}$'  # Example pattern: alphanumeric and hyphens, max length 64
        return bool(re.match(pattern, name))