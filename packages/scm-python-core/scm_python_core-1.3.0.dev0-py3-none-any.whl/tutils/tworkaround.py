def list_add(*args: list) -> list:
    """
    数组相加
    如果有个参数为空,跳过而不是抛出异常
    """
    if len(args) == 0:
        return []
    result = []
    for list_item in args:
        if list_item:
            result += list_item
    return result


def list_add_with_trim(*args: list) -> list:
    return [item for item in list_add(*args) if item]


def split(segmented_str: str, separator: str):
    if separator in segmented_str:
        return segmented_str.split(separator)
    return segmented_str, ""
