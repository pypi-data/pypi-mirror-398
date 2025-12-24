import requests
from typing import Optional, Dict, Union, Any
from .Proxy_tools import BaseProxyTools
from .darren_utils import cookie_string_to_dict


class DarrenHttpSession(requests.Session):
    """
    扩展的requests.Session类，添加额外功能
    """

    def __init__(self, proxy_tool: Optional[BaseProxyTools] = None):
        super().__init__()
        self.proxy_tool = proxy_tool

    def request(self, method: str, url: str, headers: Optional[Dict] = None,
                cookies: Optional[Union[Dict, str]] = None, proxies: Optional[Dict] = None,
                use_proxy: bool = False, max_retries: int = 3, timeout: int = 10,
                **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求，支持重试和代理

        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            cookies: Cookie字典或字符串
            proxies: 代理配置
            use_proxy: 是否使用代理
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            **kwargs: 其他传递给requests的参数

        Returns:
            requests.Response: 响应对象，失败时返回None
        """
        headers = headers or {}
        current_proxies = proxies

        for attempt in range(max_retries + 1):
            # 如果启用了代理但没有有效的代理配置，则动态获取
            if use_proxy and not current_proxies and self.proxy_tool:
                proxy_result = self.proxy_tool.get_one_proxy()
                if proxy_result:
                    current_proxies = proxy_result

            try:
                if isinstance(cookies, str):
                    cookies = cookie_string_to_dict(cookies)

                response = super().request(
                    method=method,
                    url=url,
                    headers=headers,
                    cookies=cookies,
                    proxies=current_proxies,
                    timeout=(timeout, timeout),
                    **kwargs
                )
                return response
            except Exception as e:
                if attempt < max_retries:
                    print(f"第 {attempt + 1} 次请求失败: {type(e).__name__}: {e}，正在重试...")
                    current_proxies = None
                else:
                    print(f"请求最终失败: {type(e).__name__}: {e}")
                    return None

        return None


class DarrenHttp:
    """
    基于requests的HTTP客户端封装类
    """

    def __init__(self, proxy_tool: Optional[BaseProxyTools] = None):
        """
        初始化DarrenHttp客户端

        Args:
            proxy_tool: 代理工具实例
        """
        self.session = DarrenHttpSession(proxy_tool)
        self.proxy_tool = proxy_tool

    @staticmethod
    def Session(proxy_tool: Optional[BaseProxyTools] = None):
        """
        返回扩展的Session对象，与requests.Session()兼容
        """
        return DarrenHttpSession(proxy_tool)

    # 其他方法保持不变...
    def request(self, method: str, url: str, headers: Optional[Dict] = None,
                cookies: Optional[Union[Dict, str]] = None, proxies: Optional[Dict] = None,
                use_proxy: bool = False, max_retries: int = 3, timeout: int = 10,
                **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            cookies: Cookie字典或字符串
            proxies: 代理配置
            use_proxy: 是否使用代理
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            **kwargs: 其他传递给requests的参数

        Returns:
            requests.Response: 响应对象，失败时返回None
        """
        return self.session.request(method, url, headers, cookies, proxies,
                                    use_proxy, max_retries, timeout, **kwargs)

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送GET请求"""
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送POST请求"""
        return self.request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送PUT请求"""
        return self.request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送DELETE请求"""
        return self.request('DELETE', url, **kwargs)

    def head(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送HEAD请求"""
        return self.request('HEAD', url, **kwargs)

    def options(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送OPTIONS请求"""
        return self.request('OPTIONS', url, **kwargs)

    def patch(self, url: str, **kwargs) -> Optional[requests.Response]:
        """发送PATCH请求"""
        return self.request('PATCH', url, **kwargs)

    def close(self):
        """关闭session"""
        self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
if __name__ == '__main__':
    session = DarrenHttp.Session()
    session.request('GET', 'https://www.baidu.com')

