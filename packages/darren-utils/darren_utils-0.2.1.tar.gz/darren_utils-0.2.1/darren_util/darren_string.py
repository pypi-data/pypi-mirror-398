import random
import string


def string_random_string(num, uppercase=True, lowercase=True, digits=True):
    """
    生成随机字符串

    Args:
        num (int): 生成字符串的长度
        uppercase (bool): 是否包含大写字母
        lowercase (bool): 是否包含小写字母
        digits (bool): 是否包含数字

    Returns:
        str: 生成的随机字符串
    """
    if not any([uppercase, lowercase, digits]):
        raise ValueError("至少需要启用一种字符类型")

    # 构建字符池
    char_pool = ""
    if uppercase:
        char_pool += string.ascii_uppercase
    if lowercase:
        char_pool += string.ascii_lowercase
    if digits:
        char_pool += string.digits

    # 生成随机字符串
    return ''.join(random.choices(char_pool, k=num))
def string_get_between(text, start_text, end_text):
    """
    获取两个文本之间的内容（不包含边界文本）

    Args:
        text (str): 原始文本
        start_text (str): 开始文本
        end_text (str): 结束文本

    Returns:
        str: 两个文本之间的内容，如果找不到则返回空字符串
    """
    # 查找开始文本的位置
    start_index = text.find(start_text)
    if start_index == -1:
        return ""

    # 计算开始位置（跳过开始文本）
    start_pos = start_index + len(start_text)

    # 从开始位置查找结束文本
    end_index = text.find(end_text, start_pos)
    if end_index == -1:
        return ""

    # 返回中间的文本
    return text[start_pos:end_index]
def string_get_left(text, delimiter):
    """
    获取文本中指定分隔符左边的内容

    Args:
        text (str): 原始文本
        delimiter (str): 分隔符

    Returns:
        str: 分隔符左边的内容，如果找不到分隔符则返回空字符串
    """
    index = text.find(delimiter)
    if index == -1:
        return ""
    return text[:index]
def string_get_right(text, delimiter):
    """
    获取文本中指定分隔符右边的内容

    Args:
        text (str): 原始文本
        delimiter (str): 分隔符

    Returns:
        str: 分隔符右边的内容，如果找不到分隔符则返回空字符串
    """
    index = text.find(delimiter)
    if index == -1:
        return ""
    return text[index + len(delimiter):]