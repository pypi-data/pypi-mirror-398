import re

from typing import Optional


class VariableFinder:
    """Utilidades para extraer y buscar variables y códigos en texto y JSON"""
    
    @staticmethod
    def extract_issue_number(pr_body: str):
        """
        Extracts an issue number from a pull request body text.
        Looks for a pattern like '#123' preceded by whitespace.

        Args:
            pr_body (str): The pull request body text.
        Returns:
            Optional[int]: The extracted issue number as an integer, or None if not found.
        """
        match = re.search(r"\s+#(\d+)", pr_body or "", re.IGNORECASE)
        return int(match.group(1)) if match else None

    @staticmethod
    def get_code(text: str) -> Optional[str]:
        """
        Extracts a code matching the pattern 'AW1234567' or 'NU1234567' from a string.
        The code consists of two uppercase letters followed by seven digits.

        Args:
            text (str): The input string.
        Returns:
            Optional[str]: The extracted code or None if not found.
        """
        for tok in text.split('_'):
            if re.fullmatch(r'[A-Z]{2}\d{7}', tok):
                return tok
        return None

    @staticmethod
    def get_component_name(text: str) -> Optional[str]:
        """
        Extracts a component name from a string based on underscore-separated parts.
        If the last part is 'dxp', returns the two preceding parts joined by underscore.
        Otherwise, returns the last two parts.

        Args:
            text (str): The input string.
        Returns:
            Optional[str]: The component name or None if not enough parts.
        """
        parts = [p for p in text.strip('_').split('_') if p]
        if len(parts) >= 2:
            if parts[-1].lower() == "dxp":
                return f"{parts[-3]}_{parts[-2]}"
            return '_'.join(parts[-2:])
        return None

    @staticmethod
    def get_component_name_from_image(image: str, release_name: str) -> Optional[str]:
        """
        Extracts the component name from an image string.
        If extraction fails, falls back to using release_name.

        Args:
            image (str): The image string (e.g., 'repo/component:tag').
            release_name (str): The fallback release name.
        Returns:
            Optional[str]: The component name.
        """
        try:
            tag = image.split('/')[-1]
            repository_name = tag.split(':')[0]
            return repository_name
        except Exception:
            return VariableFinder.get_component_name(release_name)

    @staticmethod
    def collect_all_variables(json_data, txt_variable_groups):
        """
        Collects all variables from a nested JSON structure.
        Searches for keys named 'variables' and merges them into a single dictionary.

        Args:
            json_data (dict or list): The JSON data.
            txt_variable_groups (str): The key name for variable groups.
        Returns:
            dict: A dictionary of all variables found.
        """
        all_variables = {}

        def loop_through_json(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == 'variables':
                        all_variables.update(value)
                    elif key == txt_variable_groups:
                        if isinstance(value, list):
                            for group in value:
                                if isinstance(group, dict) and 'variables' in group:
                                    all_variables.update(group['variables'])
                    else:
                        loop_through_json(value)
            elif isinstance(data, list):
                for item in data:
                    loop_through_json(item)

        loop_through_json(json_data)
        return all_variables

    @staticmethod
    def resolve_value(value: str, all_variables: dict, visited=None) -> str:
        """
        Resolves variable references in a string recursively.
        Variables are referenced using the format $(VAR_NAME).

        Args:
            value (str): The string containing variable references.
            all_variables (dict): Dictionary of variables and their values.
            visited (set): Set of visited variables to detect cycles.
        Returns:
            str: The resolved string with all references replaced.
        """
        if visited is None:
            visited = set()

        pattern = re.compile(r'\$\(([^)]+)\)')
        while True:
            matches = pattern.findall(value)
            if not matches:
                break
            for match in matches:
                if match in visited:
                    return f'$(CYCLE:{match})'
                visited.add(match)
                replacement = all_variables.get(match, {}).get('value', '')
                resolved = VariableFinder.resolve_value(replacement, all_variables, visited.copy())
                value = value.replace(f'$({match})', resolved)
        return value

    @staticmethod
    def search_in_json(search_value: str, search_type: str, json_data, is_json_from_azure: bool = False) -> Optional[str]:
        """
        Searches for a variable in a nested JSON structure by key or value.
        Resolves references if found.

        Args:
            search_value (str): The value to search for.
            search_type (str): 'clave' to search by key, 'valor' to search by value.
            json_data (dict or list): The JSON data.
            is_json_from_azure (bool): Whether the JSON is from Azure (changes key names).
        Returns:
            Optional[str]: The resolved value if found, otherwise None.
        """
        txt_variable_groups = 'variableGroups' if is_json_from_azure else 'variable_groups'
        search_value = search_value.lower()
        all_variables = VariableFinder.collect_all_variables(json_data, txt_variable_groups)

        result_search = all_variables.get(search_value, {}).get('value', '')
        if result_search and '$(' not in result_search:
            return result_search

        def recursive_search(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key in ['variables', txt_variable_groups]:
                        if isinstance(value, dict):
                            for var_key, var_value in value.items():
                                if search_type == 'clave' and search_value == var_key.lower():
                                    return VariableFinder.resolve_value(var_value.get('value', ''), all_variables)
                                elif search_type == 'valor' and search_value == var_value.get('value', '').lower():
                                    return VariableFinder.resolve_value(var_value.get('value', ''), all_variables)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and 'variables' in item:
                                    for var_key, var_value in item['variables'].items():
                                        if search_type == 'clave' and search_value == var_key.lower():
                                            return VariableFinder.resolve_value(var_value.get('value', ''), all_variables)
                                        elif search_type == 'valor' and search_value == var_value.get('value', '').lower():
                                            return VariableFinder.resolve_value(var_value.get('value', ''), all_variables)
                    else:
                        result = recursive_search(value)
                        if result:
                            return result
            elif isinstance(data, list):
                for item in data:
                    result = recursive_search(item)
                    if result:
                        return result
            return None

        return recursive_search(json_data)
