"""
文件操作工具模块
"""

import os
import errno
import subprocess
import platform
import shutil
import fnmatch
import math
import time
from send2trash import send2trash
# 尝试导入send2trash库，用于删除到回收站



def file_exists(file_path):
    """
    检查文件是否存在
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        bool: 文件存在返回True，否则返回False
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    return os.path.exists(file_path) and os.path.isfile(file_path)


def dir_exists(dir_path):
    """
    检查目录是否存在
    
    Args:
        dir_path (str): 目录路径
        
    Returns:
        bool: 目录存在返回True，否则返回False
    """
    if not isinstance(dir_path, str):
        raise ValueError("目录路径必须是字符串类型")
    
    return os.path.exists(dir_path) and os.path.isdir(dir_path)


def file_is_use(file_path):
    """
    检查文件是否被占用
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        bool: 文件被占用返回True，否则返回False
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    # 首先检查文件是否存在
    if not file_exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 尝试以独占模式打开文件
    try:
        with open(file_path, "r+b") as f:
            pass
        return False  # 文件未被占用
    except IOError as e:
        if e.errno == errno.EACCES:
            return True  # 文件被占用
        else:
            raise  # 其他错误重新抛出


def file_open(file_path, mode='r'):
    """
    打开文件并返回文件句柄，如果失败则返回-1
    
    Args:
        file_path (str): 文件路径
        mode (str): 文件打开模式，默认为'r'(只读)
        
    Returns:
        file object or int: 成功时返回文件句柄，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    if not isinstance(mode, str):
        raise ValueError("文件打开模式必须是字符串类型")
    
    try:
        file_handle = open(file_path, mode)
        return file_handle
    except Exception:
        return -1


def file_execute(file_path):
    """
    执行文件，如运行exe程序或用默认程序打开文件
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        subprocess.Popen or bool or int: 成功时返回进程对象或True，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    # 检查文件是否存在
    if not file_exists(file_path):
        return -1
    
    try:
        system = platform.system()
        if system == "Windows":
            # Windows系统使用os.startfile
            os.startfile(file_path)
            return True
        elif system == "Darwin":
            # macOS系统使用open命令
            process = subprocess.Popen(["open", file_path])
            return process
        elif system == "Linux":
            # Linux系统使用xdg-open命令
            process = subprocess.Popen(["xdg-open", file_path])
            return process
        else:
            # 其他系统尝试使用subprocess
            process = subprocess.Popen([file_path])
            return process
    except Exception:
        return -1


def file_locate(file_path):
    """
    在文件管理器中定位文件，打开文件所在目录并选中该文件
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        bool or int: 成功时返回True，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    # 检查文件是否存在
    if not file_exists(file_path):
        return -1
    
    try:
        system = platform.system()
        if system == "Windows":
            # Windows系统使用explorer命令，并加上/select参数来选中文件
            subprocess.Popen(['explorer', '/select,', os.path.abspath(file_path)])
            return True
        elif system == "Darwin":
            # macOS系统使用open命令定位文件
            subprocess.Popen(['open', '-R', file_path])
            return True
        elif system == "Linux":
            # Linux系统打开文件所在目录（大多数文件管理器不支持直接选中文件）
            directory = os.path.dirname(os.path.abspath(file_path))
            subprocess.Popen(['xdg-open', directory])
            return True
        else:
            # 其他系统打开文件所在目录
            directory = os.path.dirname(os.path.abspath(file_path))
            subprocess.Popen(['open', directory])  # 尝试使用macOS的open命令
            return True
    except Exception:
        return -1


def file_copy(src_path, dest_path, overwrite=False):
    """
    复制文件
    
    Args:
        src_path (str): 源文件路径
        dest_path (str): 目标文件路径
        overwrite (bool): 是否覆盖已存在的文件，默认为False
        
    Returns:
        bool or int: 成功时返回True，失败时返回-1
    """
    if not isinstance(src_path, str):
        raise ValueError("源文件路径必须是字符串类型")
    
    if not isinstance(dest_path, str):
        raise ValueError("目标文件路径必须是字符串类型")
    
    if not isinstance(overwrite, bool):
        raise ValueError("overwrite参数必须是布尔类型")
    
    # 检查源文件是否存在
    if not file_exists(src_path):
        return -1
    
    # 检查目标文件是否存在且不允许覆盖
    if file_exists(dest_path) and not overwrite:
        return -1
    
    try:
        # 执行文件复制
        shutil.copy2(src_path, dest_path)
        return True
    except Exception:
        return -1


def file_rename(old_name, new_name):
    """
    重命名文件
    
    Args:
        old_name (str): 原文件名
        new_name (str): 新文件名
        
    Returns:
        bool or int: 成功时返回True，失败时返回-1
    """
    if not isinstance(old_name, str):
        raise ValueError("原文件名必须是字符串类型")
    
    if not isinstance(new_name, str):
        raise ValueError("新文件名必须是字符串类型")
    
    # 检查原文件是否存在
    if not file_exists(old_name):
        return -1
    
    # 检查新文件名是否已存在
    if file_exists(new_name):
        return -1
    
    try:
        # 执行文件重命名
        os.rename(old_name, new_name)
        return True
    except Exception:
        return -1


def file_enumerate(directory, pattern="*.*", with_path=False, sort_alpha=False, recursive=False):
    """
    枚举某个目录下的指定类型文件
    
    Args:
        directory (str): 欲寻找的目录
        pattern (str): 欲寻找的文件名(如果寻找全部文件可以填入*.*，或*.txt只找txt文件, 多个后缀中间用"|"隔开)
        with_path (bool): 是否带路径(默认为假； 真=带目录路径，如C:\012.txt； 假=不带，如 012.txt)
        sort_alpha (bool): 是否按字母排序(默认为假；真=按字母a-z排序 假=不排序)
        recursive (bool): 是否遍历子目录(默认为假)
        
    Returns:
        list or int: 成功时返回文件列表，失败时返回-1
    """
    if not isinstance(directory, str):
        raise ValueError("目录必须是字符串类型")
    
    if not isinstance(pattern, str):
        raise ValueError("文件名模式必须是字符串类型")
    
    if not isinstance(with_path, bool):
        raise ValueError("with_path参数必须是布尔类型")
    
    if not isinstance(sort_alpha, bool):
        raise ValueError("sort_alpha参数必须是布尔类型")
    
    if not isinstance(recursive, bool):
        raise ValueError("recursive参数必须是布尔类型")
    
    # 检查目录是否存在
    if not dir_exists(directory):
        return -1
    
    try:
        files = []
        
        # 处理多个文件模式（用 | 分隔）
        patterns = pattern.split("|")
        patterns = [p.strip() for p in patterns]
        
        # 根据是否递归选择不同的遍历方法
        if recursive:
            # 递归遍历所有子目录
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    # 检查文件是否匹配任一模式
                    for pat in patterns:
                        if fnmatch.fnmatch(filename, pat):
                            if with_path:
                                files.append(os.path.join(root, filename))
                            else:
                                files.append(filename)
                            break  # 匹配到一个就够了，避免重复添加
        else:
            # 只遍历当前目录
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                # 检查是否为文件（而不是目录）
                if os.path.isfile(file_path):
                    # 检查文件是否匹配任一模式
                    for pat in patterns:
                        if fnmatch.fnmatch(filename, pat):
                            if with_path:
                                files.append(file_path)
                            else:
                                files.append(filename)
                            break  # 匹配到一个就够了，避免重复添加
        
        # 如果需要按字母排序
        if sort_alpha:
            files.sort()
        
        return files
    except Exception:
        return -1


def file_size(file_path, unit="M"):
    """
    获取文件大小
    
    Args:
        file_path (str): 文件路径
        unit (str): 返回大小的单位(B、KB、MB、GB)，默认为M
        
    Returns:
        str or int: 成功时返回格式化的文件大小字符串，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    if not isinstance(unit, str):
        raise ValueError("单位必须是字符串类型")
    
    # 检查文件是否存在
    if not file_exists(file_path):
        return -1
    
    try:
        # 获取文件大小（字节）
        size_bytes = os.path.getsize(file_path)
        
        # 定义单位映射
        units = {
            'B': 0,
            'KB': 1,
            'MB': 2,
            'GB': 3
        }
        
        # 转换为大写并检查单位是否有效
        unit = unit.upper()
        if unit not in units:
            unit = "MB"  # 默认使用MB
        
        # 计算对应的单位大小
        if size_bytes == 0:
            return f"0 {unit}"
        
        # 计算大小
        size = size_bytes / (1024 ** units[unit])
        
        # 格式化输出
        if size >= 1000:
            return f"{size:.2f} {unit}"
        elif size >= 100:
            return f"{size:.3f} {unit}"
        elif size >= 10:
            return f"{size:.4f} {unit}"
        else:
            return f"{size:.5f} {unit}"
            
    except Exception:
        return -1


def file_get_extension(file_path):
    """
    获取文件扩展名
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str or int: 成功时返回文件扩展名（如：.jpg），没有扩展名时返回空字符串，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    try:
        # 使用os.path.splitext获取文件扩展名
        _, extension = os.path.splitext(file_path)
        return extension
    except Exception:
        return -1


def file_get_directory(file_path):
    """
    获取文件所在目录路径
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str or int: 成功时返回文件所在目录路径，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    try:
        # 使用os.path.dirname获取文件所在目录
        directory = os.path.dirname(file_path)
        
        # 如果目录为空，说明是相对路径的文件，返回当前目录
        if directory == "":
            return "."
        
        # 确保目录路径末尾有路径分隔符
        if not directory.endswith(os.sep):
            directory += os.sep
            
        return directory
    except Exception:
        return -1


def file_get_info(file_path):
    """
    获取文件信息
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        dict or int: 成功时返回包含文件信息的字典，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    # 检查文件是否存在
    if not file_exists(file_path):
        return -1
    
    try:
        # 获取文件统计信息
        stat_info = os.stat(file_path)
        
        # 获取文件基本信息
        file_info = {
            "name": os.path.basename(file_path),  # 文件名
            "path": file_path,  # 完整路径
            "directory": file_get_directory(file_path),  # 所在目录
            "extension": file_get_extension(file_path),  # 扩展名
            "size_bytes": stat_info.st_size,  # 文件大小（字节）
            "size_formatted": file_size(file_path, "MB"),  # 格式化文件大小
            "created_time": time.ctime(stat_info.st_ctime),  # 创建时间
            "modified_time": time.ctime(stat_info.st_mtime),  # 修改时间
            "accessed_time": time.ctime(stat_info.st_atime),  # 访问时间
            "is_readable": os.access(file_path, os.R_OK),  # 是否可读
            "is_writable": os.access(file_path, os.W_OK),  # 是否可写
            "is_executable": os.access(file_path, os.X_OK)  # 是否可执行
        }
        
        return file_info
    except Exception:
        return -1


def file_get_name(file_path, with_extension=False):
    """
    获取文件名
    
    Args:
        file_path (str): 文件路径
        with_extension (bool): 是否带后缀，默认为False，不带后缀；True为带后缀
        
    Returns:
        str or int: 成功时返回文件名，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    if not isinstance(with_extension, bool):
        raise ValueError("with_extension参数必须是布尔类型")
    
    try:
        # 获取文件名（带后缀）
        file_name_with_ext = os.path.basename(file_path)
        
        # 如果需要带后缀，直接返回
        if with_extension:
            return file_name_with_ext
        
        # 如果不需要带后缀，去掉后缀后再返回
        file_name_without_ext = os.path.splitext(file_name_with_ext)[0]
        return file_name_without_ext
    except Exception:
        return -1


def file_delete(file_path, to_trash=True):
    """
    删除文件
    
    Args:
        file_path (str): 文件路径
        to_trash (bool): 是否删除到回收站，默认为True（删除到回收站）；False为彻底删除
        
    Returns:
        bool or int: 成功时返回True，失败时返回-1
    """
    if not isinstance(file_path, str):
        raise ValueError("文件路径必须是字符串类型")
    
    if not isinstance(to_trash, bool):
        raise ValueError("to_trash参数必须是布尔类型")
    
    # 检查文件是否存在
    if not file_exists(file_path):
        return -1
    
    try:
        if to_trash:
            send2trash(file_path)
        else:
            # 彻底删除
            os.remove(file_path)
        
        return True
    except Exception:
        return -1


if __name__ == "__main__":
    # 测试文件存在检查
    print(f"当前文件是否存在: {file_exists(__file__)}")
    print(f"不存在的文件: {file_exists('nonexistent.txt')}")
    print(f"当前目录是否存在: {dir_exists('.')}")
    
    # 测试文件占用检查
    # 使用原始字符串避免转义字符问题
    test_file_path = r'G:\python\yoloProUP\dist\YOLO免环境自动标注训练工具专业版\shortcuts.ini'
    try:
        print(f"当前文件是否被占用: {file_is_use(test_file_path)}")
    except FileNotFoundError:
        print(f"文件不存在: {test_file_path}")
    except Exception as e:
        print(f"检查文件占用状态时发生错误: {e}")
    
    # # 测试文件打开功能
    # print(f"打开当前文件: {file_open(__file__)}")
    # print(f"打开不存在的文件: {file_open('nonexistent.txt')}")
    #
    # # 测试文件执行功能
    # # 注意：这里只是示例，实际使用时请提供存在的文件路径
    # print(f"执行文件: {file_execute(test_file_path)}")
    # print(f"执行不存在的文件: {file_execute('nonexistent.txt')}")
    
    # # 测试文件定位功能
    # print(f"定位当前文件: {file_locate(__file__)}")
    # print(f"定位不存在的文件: {file_locate('nonexistent.txt')}")
    #
    # # 测试文件复制功能
    # print(f"复制当前文件到临时位置: {file_copy(__file__, 'temp_test_copy.py')}")
    # # print(f"复制当前文件到临时位置(覆盖): {file_copy(__file__, 'temp_test_copy.py', True)}")
    # print(f"复制不存在的文件: {file_copy('nonexistent.txt', 'temp_nonexistent_copy.py')}")
    # 
    # # 测试文件重命名功能
    # # 先创建一个测试文件
    # with open('temp_rename_test.txt', 'w') as f:
    #     f.write('test content')
    # print(f"重命名文件: {file_rename('temp_rename_test.txt', 'temp_renamed_test.txt')}")
    # # 清理测试文件
    # if file_exists('temp_renamed_test.txt'):
    #     os.remove('temp_renamed_test.txt')
    # print(f"重命名不存在的文件: {file_rename('nonexistent.txt', 'temp_renamed_test.txt')}")
    # 
    # # 测试文件枚举功能
    # print(f"枚举当前目录所有文件: {file_enumerate('.', '*.py',recursive=False)}")
    # print(f"枚举当前目录txt文件: {file_enumerate('.', '*.py')}")
    # print(f"枚举当前目录py和txt文件: {file_enumerate('.', '*.py|*.txt')}")
    # print(f"枚举当前目录所有文件(带路径): {file_enumerate('.', '*.*', with_path=True)}")
    # print(f"枚举当前目录所有文件(排序): {file_enumerate('.', '*.*', sort_alpha=True)}")
    # print(f"枚举当前目录所有文件(带路径+排序): {file_enumerate('.', '*.*', with_path=True, sort_alpha=True)}")
    # 
    # 测试文件大小功能
    # print(f"当前文件大小(MB): {file_size(__file__)}")
    # print(f"当前文件大小(B): {file_size(__file__, 'B')}")
    # print(f"当前文件大小(KB): {file_size(__file__, 'KB')}")
    # print(f"当前文件大小(GB): {file_size(__file__, 'GB')}")
    # print(f"不存在文件的大小: {file_size('nonexistent.txt')}")
    # 
    # 测试文件扩展名功能
    # print(f"当前文件的扩展名: {file_get_extension(__file__)}")
    # print(f"没有扩展名的文件: {file_get_extension('README')}")
    # print(f"带扩展名的文件: {file_get_extension('test.txt')}")
    # print(f"多级扩展名: {file_get_extension('archive.tar.gz')}")
    # 
    # 测试文件目录功能
    # print(f"当前文件所在目录: {file_get_directory(__file__)}")
    # print(f"绝对路径文件所在目录: {file_get_directory(r'C:\\012\\3600.exe')}")
    # print(f"相对路径文件所在目录: {file_get_directory('folder/test.txt')}")
    # 
    # 测试文件信息功能
    # info = file_get_info(__file__)
    # if info != -1:
    #     print("当前文件信息:")
    #     for key, value in info.items():
    #         print(f"  {key}: {value}")
    # else:
    #     print("获取文件信息失败")
    # 
    # print(f"不存在文件的信息: {file_get_info('nonexistent.txt')}")
    # 
    # 测试文件名功能
    # print(f"当前文件名(不带后缀): {file_get_name(__file__)}")
    # print(f"当前文件名(带后缀): {file_get_name(__file__, True)}")
    # print(f"C:\\123.exe(不带后缀): {file_get_name(r'C:\\123.exe')}")
    # print(f"C:\\123.exe(带后缀): {file_get_name(r'C:\\123.exe', True)}")
    # print(f"不存在文件的文件名: {file_get_name('nonexistent.txt')}")
    # 
    # 测试文件删除功能
    # # 先创建一个测试文件
    # with open('temp_delete_test.txt', 'w') as f:
    #     f.write('test content for deletion')
    # print(f"删除文件到回收站: {file_delete('temp_delete_test.txt')}")
    # 
    # # 再创建一个测试文件
    # with open('temp_delete_test2.txt', 'w') as f:
    #     f.write('test content for permanent deletion')
    # print(f"彻底删除文件: {file_delete('temp_delete_test2.txt', False)}")
    # 
    # print(f"删除不存在的文件: {file_delete('nonexistent.txt')}")