from abc import ABC, abstractmethod

class BaseProxyTools(ABC):
    @abstractmethod
    def get_one_proxy(self):
        """获取一个代理，子类必须实现此方法"""
        pass