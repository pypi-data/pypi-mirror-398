from typing import List, Dict, Any


class DictionaryUtility:
    """
    A class to provide utility methods for working with dictionaries.
    """

    @staticmethod
    def find_dict_by_name(
        dict_list: List[dict], key_field: str, name: str
    ) -> List[dict] | dict | str:
        """
        Searches for dictionaries in a list where the key 'name' matches the specified value.

        Args:
        dict_list (list): A list of dictionaries to search through.
        key_field (str): The key to search for in each dictionary.
        name (str): The value to search for in the 'key_field' key.

        Returns:
        list: A list of dictionaries where the 'key_field' key matches the specified value.
        """
        # List comprehension to filter dictionaries that have the 'name' key equal to the specified name

        return [d for d in dict_list if d.get(key_field) == name]

    @staticmethod
    def rename_keys(
        dictionary: Dict[str, Any] | List[Dict[str, Any]], old_key: str, new_key: str
    ) -> Dict[str, Any] | List[Dict[str, Any]]:
        """
        Renames a key in a dictionary.

        Args:
        dictionary (dict): The dictionary to modify.
        old_key (str): The key to be renamed.
        new_key (str): The new key name.

        Returns:
        dict: The modified dictionary with the key renamed.
        """
        if isinstance(dictionary, list):
            results: List[Dict[str, Any]] = []

            for item in dictionary:
                if isinstance(item, dict):
                    x = DictionaryUtility.rename_keys(item, old_key, new_key)
                    if isinstance(x, dict):
                        results.append(x)

                else:
                    if isinstance(item, dict):
                        results.append(item)

            return results
        if isinstance(dictionary, dict):
            if old_key in dictionary:
                dictionary[new_key] = dictionary.pop(old_key)
            return dictionary

        raise ValueError("Input must be a dictionary or a list of dictionaries")

    @staticmethod
    def load_json(path: str) -> dict:
        """
        Loads a JSON file from the specified path.

        Args:
        path (str): The path to the JSON file.

        Returns:
        dict: The loaded JSON data.
        """
        import json

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
