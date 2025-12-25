"""Utility functions for json2csv-pro."""

from typing import Dict, Any


def flatten_json(data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Flatten nested JSON structure.
    
    Args:
        data (Dict[str, Any]): Nested JSON data
        **kwargs: Flattening parameters
            - parent_key (str): Parent key for recursion (default: '')
            - separator (str): Key separator (default: '.')
            - max_depth (int): Maximum depth to flatten (default: 10)
    
    Returns:
        Dict[str, Any]: Flattened dictionary
        
    Example:
        >>> from json2csv_pro import flatten_json
        >>> data = {"user": {"name": "John", "address": {"city": "NYC"}}}
        >>> flat = flatten_json(data, separator='_')
        >>> print(flat)
        {'user_name': 'John', 'user_address_city': 'NYC'}
    """
    parent_key = kwargs.get('parent_key', '')
    separator = kwargs.get('separator', '.')
    max_depth = kwargs.get('max_depth', 10)
    current_depth = kwargs.get('current_depth', 0)
    
    items = []
    
    if current_depth >= max_depth:
        return {parent_key: data}
    
    for k, v in data.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(
                flatten_json(
                    v,
                    parent_key=new_key,
                    separator=separator,
                    max_depth=max_depth,
                    current_depth=current_depth + 1
                ).items()
            )
        elif isinstance(v, list):
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    
    return dict(items)


def detect_delimiter(**kwargs) -> str:
    """
    Detect delimiter from a CSV sample.
    
    Args:
        **kwargs: Detection parameters
            - sample (str): Sample CSV string
            - candidates (List[str]): Delimiter candidates (default: [',', ';', '\t', '|'])
    
    Returns:
        str: Detected delimiter
        
    Example:
        >>> from json2csv_pro import detect_delimiter
        >>> sample = "name;age;city\\nJohn;30;NYC"
        >>> delimiter = detect_delimiter(sample=sample)
        >>> print(delimiter)
        ';'
    """
    sample = kwargs.get('sample', '')
    candidates = kwargs.get('candidates', [',', ';', '\t', '|'])
    
    max_count = 0
    detected = ','
    
    for delimiter in candidates:
        count = sample.count(delimiter)
        if count > max_count:
            max_count = count
            detected = delimiter
    
    return detected