from typing import Optional, Dict

import requests

from .Proxy_tools import BaseProxyTools
from .darren_utils import cookie_string_to_dict

def darren_http(method: str, url: str, headers: Optional[Dict] = None,
                      cookies: Optional[Dict] = None, proxies: Optional[Dict] = None,
                      use_proxy: bool = True, max_retries: int = 3, timeout: int = 10,
                      proxy_tool: Optional[BaseProxyTools] = None,
                      **kwargs) -> Optional[requests.Response]:
    """
    简化版HTTP请求函数，只返回Response对象

    Args:
        method: HTTP方法 ('GET', 'POST', 'PUT', 'DELETE' 等)
        url: 请求URL
        headers: 请求头
        cookies: Cookie字典
        proxies: 传入的代理配置
        use_proxy: 是否使用代理
        max_retries: 最大重试次数
        timeout: 超时时间（秒）
        proxy_tool: 自定义代理工具实例
        **kwargs: 其他传递给requests的参数

    Returns:
        Optional[requests.Response]: Response对象，失败时返回None
    """
    response, _ = darren_http_proxy(method, url, headers, cookies, proxies,
                             use_proxy, max_retries, timeout, proxy_tool, **kwargs)
    return response
def darren_http_proxy(method: str, url: str, headers: Optional[Dict] = None,
                cookies: Optional[Dict] = None, proxies: Optional[Dict] = None,
                use_proxy: bool = True, max_retries: int = 3, timeout: int = 10,
                proxy_tool: Optional[BaseProxyTools] = None,
                **kwargs) -> tuple[Optional[requests.Response], Optional[Dict]]:
    """
    封装的HTTP请求函数，支持自动重试和代理切换

    Args:
        method: HTTP方法 ('GET', 'POST', 'PUT', 'DELETE' 等)
        url: 请求URL
        headers: 请求头
        cookies: Cookie字典
        proxies: 传入的代理配置
        use_proxy: 是否使用代理
        max_retries: 最大重试次数
        timeout: 超时时间（秒）
        proxy_tool: 自定义代理工具实例
        **kwargs: 其他传递给requests的参数

    Returns:
        tuple[Optional[requests.Response], Optional[Dict]]:
        返回(response对象, 使用的代理)的元组，失败时返回(None, None)

    Example:
        >>> response, proxies = darren_http('GET', 'https://httpbin.org/get')
        >>> if response:
        ...     print(response.status_code)
    """
    headers = headers or {}
    # 使用用户提供的代理工具或默认工具
    # 注意：这里需要用户自己提供 ProxyTool 实例或实现 BaseProxyTools
    tool = proxy_tool
    # 如果传入了代理参数，优先使用传入的
    current_proxies = proxies
    for attempt in range(max_retries + 1):
        # 如果启用了代理但没有有效的代理配置，则动态获取
        if use_proxy and not current_proxies and tool:
            proxy_result = tool.get_one_proxy()
            if proxy_result:
                current_proxies = proxy_result
        try:
            if isinstance(cookies, str):
                cookies = cookie_string_to_dict(cookies)
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                cookies=cookies,
                proxies=current_proxies,
                timeout=timeout,
                **kwargs
            )
            return response, current_proxies
        except Exception as e:
            if attempt < max_retries:
                print(f"第 {attempt + 1} 次请求失败: {type(e).__name__}, {e}正在重试...")
                current_proxies = None
            else:
                return None, None

    return None, None


