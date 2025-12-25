from typing import Dict, Any


class DualHashMap:
    def __init__(self):
        # Single dictionary to maintain bidirectional mapping
        self.mapping: Dict[Any, Any] = {}

    def insert(self, key, value):
        """
        Inserts a key-value pair into the hash map.

        :param key: An integer key or a string key.
        :param value: A string value or an integer value.
        """
        assert isinstance(key, (str, int)), "Value must be a string or an integer"
        assert isinstance(value, (str, int)), "Value must be a string or an integer"
        self.mapping[key] = value
        self.mapping[value] = key

    def get(self, key):
        """
        Retrieves the value associated with the key.

        :param key: An integer or string key.
        :return: The associated value (string for int keys, int for string keys).
        :raises KeyError: If the key does not exist.
        """
        return self.mapping[key]

    def remove(self, key):
        """
        Removes the key-value pair associated with the given key.

        :param key: An integer or string key.
        :raises KeyError: If the key does not exist.
        """
        value = self.mapping.pop(key)
        self.mapping.pop(value)

    def __repr__(self):
        return f"DualHashMap({{k: v for k, v in self.mapping.items() if isinstance(k, int)}})"

    """
    # Example usage:
    dual_map = DualHashMap()
    dual_map.insert(1, "one")
    dual_map.insert(2, "two")

    print(dual_map.get(1))  # Output: "one"
    print(dual_map.get("one"))  # Output: 1

    # Remove a mapping
    dual_map.remove(1)

    print(dual_map)  # Output: DualHashMap({2: 'two'})
    """
