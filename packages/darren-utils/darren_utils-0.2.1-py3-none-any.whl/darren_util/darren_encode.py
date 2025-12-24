import urllib.parse
from urllib.parse import urlparse, parse_qs
def url_encode(text, is_utf8=True):
    """
    将字符串转换为URL编码

    Args:
        text (str): 要编码的字符串
        is_utf8 (bool): 是否使用UTF-8编码，默认为True

    Returns:
        str: URL编码后的字符串
    """
    if not isinstance(text, str):
        raise ValueError("输入必须是字符串类型")

    if is_utf8:
        # 使用UTF-8编码
        return urllib.parse.quote(text, encoding='utf-8')
    else:
        # 使用系统默认编码
        return urllib.parse.quote(text, encoding='GBK')


def url_get_param(url, param_name):
    """
    从URL中获取指定参数的值

    Args:
        url (str): 完整的URL地址
        param_name (str): 要获取的参数名称

    Returns:
        str: 参数值，如果参数不存在或URL无效则返回空字符串
    """
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # parse_qs返回的是列表，取第一个值
        param_values = query_params.get(param_name)
        if param_values:
            return param_values[0]
        return ""
    except Exception:
        return ""

def url_decode(encoded_text, is_utf8=True):
    """
    将URL编码的字符串解码为原始字符串

    Args:
        encoded_text (str): URL编码的字符串
        is_utf8 (bool): 是否使用UTF-8解码，默认为True

    Returns:
        str: 解码后的原始字符串
    """
    if not isinstance(encoded_text, str):
        raise ValueError("输入必须是字符串类型")

    if is_utf8:
        # 使用UTF-8解码
        return urllib.parse.unquote(encoded_text, encoding='utf-8')
    else:
        # 使用系统默认解码
        return urllib.parse.unquote(encoded_text, encoding='GBK')
if __name__ == '__main__':
    encoded = url_encode("你好 world")
    print("编码后:", encoded)
    decoded = url_decode(encoded)
    print("解码后:", decoded)