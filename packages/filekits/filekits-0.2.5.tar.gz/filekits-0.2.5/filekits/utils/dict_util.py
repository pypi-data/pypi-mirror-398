# 从字典中移除指定的键
def remove_keys(data: dict, keys_to_remove: list) -> dict:
    """从字典中移除指定的键列表
    
    Args:
        data: 要处理的字典
        keys_to_remove: 需要移除的键列表
        
    Returns:
        处理后的字典
    """
    for key in keys_to_remove:
        if key in data:
            del data[key]
    return data