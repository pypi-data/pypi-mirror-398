import json
import os
import sys
import time
from datetime import datetime

import requests
from typing import Optional, Dict, Union, Any, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .Proxy_tools import BaseProxyTools
from .darren_utils import cookie_string_to_dict


class DarrenHttpSession(requests.Session):
    """
    扩展的requests.Session类，添加额外功能
    """

    def __init__(self, proxy_tool: Optional[BaseProxyTools] = None, enable_detailed_logging: bool = False):
        super().__init__()
        self.proxy_tool = proxy_tool
        self._cached_proxy = None  # 添加代理缓存
        self._proxy_failed = False  # 标记代理是否失效
        self.enable_detailed_logging = enable_detailed_logging

    def _log_request_details(self, task_id: Optional[str], method: str, url: str,
                             headers: Dict, cookies: Any, proxies: Dict,
                             request_start: float, response: Optional[requests.Response] = None,
                             error: Optional[Exception] = None):
        """记录详细请求信息到文件"""
        if not self.enable_detailed_logging:
            return

        log_data = {
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'request': {
                'method': method,
                'url': url,
                'headers': dict(headers) if headers else {},
                'cookies': cookies,
                'proxies': proxies,
                'used_proxy': self._cached_proxy
            },
            'performance': {
                'duration_seconds': time.time() - request_start
            }
        }

        if response:
            content_type = response.headers.get('content-type', '').lower()
            log_data['response'] = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content_length': len(response.content) if response.content else 0,
                'content_type': response.headers.get('content-type', '')
            }
            if 'text/' in content_type:
                log_data['response']['text'] = response.text
            elif 'application/json' in content_type:
                try:
                    log_data['response']['json'] = response.json()
                except (ValueError, requests.JSONDecodeError):
                    log_data['response']['text'] = response.text
        elif error:
            log_data['error'] = {
                'type': type(error).__name__,
                'message': str(error)
            }

        # 保存到文件
        filename = f"request_log_{task_id or 'default'}.txt"
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False, indent=2) + '\n')

    def request(self, method: str, url: str, headers: Optional[Dict] = None,
                cookies: Optional[Union[Dict, str]] = None, proxies: Optional[Dict] = None,
                use_proxy: bool = False, max_retries: int = 3, timeout: Union[int, Tuple[int, int]] = 10,
                task_id: Optional[str] = None,  # 添加task_id参数
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
            task_id:请求id
            **kwargs: 其他传递给requests的参数

        Returns:
            requests.Response: 响应对象，失败时返回None
        """
        request_start = time.time() if self.enable_detailed_logging else None
        headers = headers or {}
        current_proxies = proxies

        for attempt in range(max_retries + 1):
            # 如果启用了代理但没有有效的代理配置，则使用缓存或获取新代理
            if use_proxy and not current_proxies:
                if self._cached_proxy and not self._proxy_failed:
                    # 使用缓存的代理
                    current_proxies = self._cached_proxy
                elif self.proxy_tool:
                    # 获取新代理并缓存
                    proxy_result = self.proxy_tool.get_one_proxy()
                    if proxy_result:
                        current_proxies = proxy_result
                        self._cached_proxy = proxy_result
                        self._proxy_failed = False  # 重置失败标记

            try:
                if isinstance(cookies, str):
                    cookies = cookie_string_to_dict(cookies)

                response = super().request(
                    method=method,
                    url=url,
                    headers=headers,
                    cookies=cookies,
                    proxies=current_proxies,
                    timeout=timeout,
                    **kwargs
                )
                if self.enable_detailed_logging and request_start:
                    self._log_request_details(
                        task_id=task_id,
                        method=method,
                        url=url,
                        headers=headers,
                        cookies=cookies,
                        proxies=current_proxies,
                        request_start=request_start,
                        response=response
                    )
                return response
            except Exception as e:
                if self.enable_detailed_logging and request_start and attempt >= max_retries:
                    self._log_request_details(
                        task_id=task_id,
                        method=method,
                        url=url,
                        headers=headers,
                        cookies=cookies,
                        proxies=current_proxies,
                        request_start=request_start,
                        error=e
                    )
                if attempt < max_retries:
                    print(f"第 {attempt + 1} 次请求失败: {type(e).__name__}: {e}，正在重试...")
                    self._proxy_failed = True
                    current_proxies = None
                else:
                    print(f"请求最终失败: {type(e).__name__}: {e}")
                    return None

        return None

    def clear_proxy_cache(self):
        """清除代理缓存"""
        self._cached_proxy = None
        self._proxy_failed = False


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
    def Session(proxy_tool: Optional[BaseProxyTools] = None, enable_detailed_logging: bool = False):
        """
        返回扩展的Session对象，与requests.Session()兼容
        """
        return DarrenHttpSession(proxy_tool, enable_detailed_logging)

    # 其他方法保持不变...
    def request(self, method: str, url: str, headers: Optional[Dict] = None,
                cookies: Optional[Union[Dict, str]] = None, proxies: Optional[Dict] = None,
                use_proxy: bool = False, max_retries: int = 3, timeout: Union[int, Tuple[int, int]] = 10,
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
        return self.session.request(
            method=method,
            url=url,
            headers=headers,
            cookies=cookies,
            proxies=proxies,
            use_proxy=use_proxy,
            max_retries=max_retries,
            timeout=timeout,
            **kwargs
        )

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
    session = DarrenHttp.Session(enable_detailed_logging=True)
    request = session.request('GET', 'https://www.baidu.com', task_id='123')
    print(request.status_code)

