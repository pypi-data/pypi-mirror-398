from typing import Dict, Optional, Tuple


def parse_headers(header_strings: Tuple[str, ...]) -> Optional[Dict[str, str]]:
    """
    解析命令行传入的 header 字符串
    
    支持格式:
    - "Key: Value"
    - "Key=Value"
    
    示例:
        --header "X-Custom: value1" --header "X-Test=value2"
    
    Args:
        header_strings: 命令行传入的 header 字符串元组
    
    Returns:
        Dict[str, str] or None: 解析后的 headers 字典，如果没有则返回 None
    
    Raises:
        ValueError: 如果 header 格式不正确
    """
    if not header_strings:
        return None
    
    headers = {}
    for header_str in header_strings:
        if ": " in header_str:
            key, value = header_str.split(": ", 1)
        elif "=" in header_str:
            key, value = header_str.split("=", 1)
        else:
            raise ValueError(
                f"Invalid header format: '{header_str}'. "
                f"Use 'Key: Value' or 'Key=Value'"
            )
        
        headers[key.strip()] = value.strip()
    
    return headers if headers else None
