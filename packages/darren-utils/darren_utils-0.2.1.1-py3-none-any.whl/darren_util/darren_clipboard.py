import pyperclip
from PIL import Image
import base64
import io


class Clipboard:
    """剪切板操作类"""

    @staticmethod
    def clipboard_set_text(text):
        """
        设置剪切板文本内容

        Args:
            text (str): 要设置的文本内容

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    @staticmethod
    def clipboard_get_text():
        """
        获取剪切板文本内容

        Returns:
            str: 剪切板中的文本内容，失败返回空字符串
        """
        try:
            return pyperclip.paste()
        except Exception:
            return ""



    @staticmethod
    def clipboard_clear():
        """
        清空剪切板内容

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            pyperclip.copy("")
            return True
        except Exception:
            return False
if __name__ == '__main__':
    pass
