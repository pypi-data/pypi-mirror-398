from typing import Optional, Dict, Any
import psutil
import subprocess
import platform
import sys
from typing import Dict, Any

import platform
import subprocess
import os
from typing import Optional


def system_get_cpu_info() -> dict:
    """
    获取CPU详细信息

    Returns:
        dict: 包含CPU信息的字典
    """
    cpu_info = {
        'model': 'Unknown',
        'cores': 0,
        'threads': 0,
        'architecture': platform.machine(),
        'frequency': 'Unknown'
    }

    try:
        system = platform.system().lower()

        if system == "windows":
            # Windows系统获取CPU信息
            try:
                # 获取CPU型号
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'Name', '/value'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'Name=' in line:
                            cpu_info['model'] = line.split('=')[1].strip()
                            break

                # 获取CPU核心数
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'NumberOfCores', '/value'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'NumberOfCores=' in line:
                            cpu_info['cores'] = int(line.split('=')[1].strip())
                            break

                # 获取逻辑处理器数
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'NumberOfLogicalProcessors', '/value'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'NumberOfLogicalProcessors=' in line:
                            cpu_info['threads'] = int(line.split('=')[1].strip())
                            break

            except Exception:
                # 回退到platform.processor()
                cpu_info['model'] = platform.processor() or 'Unknown'

        elif system == "linux":
            # Linux系统获取CPU信息
            try:
                # 从/proc/cpuinfo获取CPU型号
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()

                # 查找CPU型号
                for line in cpuinfo.split('\n'):
                    if 'model name' in line:
                        cpu_info['model'] = line.split(':')[1].strip()
                        break

                # 获取核心数
                cores = set()
                for line in cpuinfo.split('\n'):
                    if 'core id' in line:
                        core_id = line.split(':')[1].strip()
                        cores.add(core_id)

                cpu_info['cores'] = len(cores) if cores else 1

                # 获取线程数
                thread_count = 0
                for line in cpuinfo.split('\n'):
                    if 'processor' in line and ':' in line:
                        thread_count += 1

                cpu_info['threads'] = thread_count if thread_count > 0 else 1

            except Exception:
                pass

        elif system == "darwin":
            # macOS系统获取CPU信息
            try:
                # 获取CPU型号
                result = subprocess.run(
                    ['sysctl', '-n', 'machdep.cpu.brand_string'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    cpu_info['model'] = result.stdout.strip()

                # 获取核心数
                result = subprocess.run(
                    ['sysctl', '-n', 'hw.physicalcpu'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    cpu_info['cores'] = int(result.stdout.strip())

                # 获取逻辑核心数
                result = subprocess.run(
                    ['sysctl', '-n', 'hw.logicalcpu'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    cpu_info['threads'] = int(result.stdout.strip())

            except Exception:
                pass

        # 如果还是Unknown，尝试使用platform.processor()
        if cpu_info['model'] == 'Unknown':
            cpu_info['model'] = platform.processor() or 'Unknown'

    except Exception:
        pass

    return cpu_info


def system_get_cpu_model() -> str:
    """
    获取CPU型号

    Returns:
        str: CPU型号字符串
    """
    try:
        cpu_info = system_get_cpu_info()
        return cpu_info.get('model', 'Unknown')
    except Exception:
        return 'Unknown'


def system_get_cpu_cores() -> int:
    """
    获取CPU物理核心数

    Returns:
        int: CPU物理核心数
    """
    try:
        cpu_info = system_get_cpu_info()
        return cpu_info.get('cores', 0)
    except Exception:
        return 0


def system_get_cpu_threads() -> int:
    """
    获取CPU逻辑线程数

    Returns:
        int: CPU逻辑线程数
    """
    try:
        cpu_info = system_get_cpu_info()
        return cpu_info.get('threads', 0)
    except Exception:
        return 0

def system_empty_recycle_bin(confirm: bool = True) -> bool:
    """
    清空回收站

    Args:
        confirm (bool): 是否弹出询问框，默认为True（弹出询问框）
                        True表示弹出系统确认对话框
                        False表示直接清空不询问

    Returns:
        bool: 成功清空回收站返回True，失败返回False
    """
    try:
        system = platform.system().lower()

        if system == "windows":
            # Windows系统清空回收站
            try:
                import ctypes
                from ctypes import wintypes

                # Windows API常量
                SHERB_NOCONFIRMATION = 0x00000001
                SHERB_NOPROGRESSUI = 0x00000002
                SHERB_NOSOUND = 0x00000004

                # 加载shell32.dll
                shell32 = ctypes.windll.shell32

                # 设置标志位
                flags = 0
                if not confirm:
                    flags |= SHERB_NOCONFIRMATION  # 不显示确认对话框

                # 调用Windows API清空回收站
                # 参数说明：
                # hwnd: 父窗口句柄，0表示无父窗口
                # pszRootPath: 回收站路径，None表示所有驱动器
                # dwFlags: 标志位
                result = shell32.SHEmptyRecycleBinW(0, None, flags)

                # 返回值为0表示成功
                return result == 0

            except Exception:
                # 如果ctypes方法失败，尝试使用PowerShell命令
                try:
                    if confirm:
                        # 弹出确认对话框
                        cmd = [
                            "powershell",
                            "-Command",
                            "Add-Type -AssemblyName Microsoft.VisualBasic; "
                            "[Microsoft.VisualBasic.Interaction]::MsgBox('确定要清空回收站吗？', 'OKCancel', '确认清空回收站') | Out-Null; "
                            "Clear-RecycleBin -Force"
                        ]
                    else:
                        # 直接清空不询问
                        cmd = [
                            "powershell",
                            "-Command",
                            "Clear-RecycleBin -Force"
                        ]

                    result = subprocess.run(cmd, capture_output=True, text=True)
                    return result.returncode == 0
                except Exception:
                    return False

        elif system == "darwin":  # macOS
            # macOS系统清空废纸篓
            try:
                # 使用AppleScript清空废纸篓
                if confirm:
                    # 弹出确认对话框
                    script = '''
                    display dialog "确定要清空废纸篓吗？" buttons {"取消", "确定"} default button "取消"
                    if button returned of result is "确定" then
                        tell application "Finder"
                            empty trash
                        end tell
                    end if
                    '''
                else:
                    # 直接清空不询问
                    script = '''
                    tell application "Finder"
                        empty trash
                    end tell
                    '''

                cmd = ["osascript", "-e", script]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0

            except Exception:
                return False

        elif system == "linux":
            # Linux系统清空回收站
            try:
                import shutil
                import glob

                # Linux回收站路径通常在 ~/.local/share/Trash/
                trash_path = os.path.expanduser("~/.local/share/Trash/")

                if os.path.exists(trash_path):
                    if confirm:
                        # 简单的命令行确认
                        response = input("确定要清空回收站吗？(y/N): ")
                        if response.lower() not in ['y', 'yes']:
                            return False

                    # 清空files目录（实际文件）
                    files_dir = os.path.join(trash_path, "files")
                    if os.path.exists(files_dir):
                        for item in os.listdir(files_dir):
                            item_path = os.path.join(files_dir, item)
                            try:
                                if os.path.isfile(item_path) or os.path.islink(item_path):
                                    os.unlink(item_path)
                                elif os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                            except Exception:
                                continue

                    # 清空info目录（元数据）
                    info_dir = os.path.join(trash_path, "info")
                    if os.path.exists(info_dir):
                        for item in os.listdir(info_dir):
                            item_path = os.path.join(info_dir, item)
                            try:
                                os.unlink(item_path)
                            except Exception:
                                continue

                    return True
                else:
                    return False

            except Exception:
                return False
        else:
            # 不支持的操作系统
            return False

    except Exception:
        return False


def system_get_version() -> Dict[str, Any]:
    """
    获取系统版本信息

    Returns:
        dict: 包含系统版本信息的字典
    """
    try:
        # 获取系统信息
        system_info = {
            'system': platform.system(),  # 操作系统名称
            'release': platform.release(),  # 操作系统发行版本
            'version': platform.version(),  # 操作系统版本
            'machine': platform.machine(),  # 机器类型
            'processor': platform.processor(),  # 处理器信息
            'architecture': platform.architecture()[0],  # 系统架构
            'node': platform.node(),  # 网络节点名称
            'platform': platform.platform(),  # 平台信息
            'python_version': sys.version,  # Python版本
            'python_compiler': platform.python_compiler()  # Python编译器
        }

        # 根据不同操作系统获取更详细的版本信息
        if system_info['system'].lower() == 'windows':
            # Windows系统额外信息
            try:
                import subprocess
                # 获取Windows版本详细信息
                result = subprocess.run(
                    ['wmic', 'os', 'get', 'Caption,Version,BuildNumber', '/value'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'Caption=' in line:
                            system_info['windows_caption'] = line.split('=')[1]
                        elif 'Version=' in line:
                            system_info['windows_version'] = line.split('=')[1]
                        elif 'BuildNumber=' in line:
                            system_info['windows_build'] = line.split('=')[1]
            except Exception:
                pass

        elif system_info['system'].lower() in ['linux', 'darwin']:
            # Unix/Linux/macOS系统额外信息
            try:
                import subprocess
                if system_info['system'].lower() == 'linux':
                    # Linux系统获取发行版信息
                    result = subprocess.run(['lsb_release', '-d'], capture_output=True, text=True)
                    if result.returncode == 0:
                        system_info['distribution'] = result.stdout.strip().split(':')[1].strip()
                else:
                    # macOS系统获取版本信息
                    result = subprocess.run(['sw_vers', '-productVersion'], capture_output=True, text=True)
                    if result.returncode == 0:
                        system_info['macos_version'] = result.stdout.strip()
            except Exception:
                pass

        return system_info

    except Exception as e:
        # 发生异常时返回基本系统信息
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'error': str(e)
        }


def system_get_simple_version() -> str:
    """
    获取简化版系统版本信息

    Returns:
        str: 简化版系统版本信息
    """
    try:
        return platform.platform()
    except Exception:
        return f"{platform.system()} {platform.release()}"


def system_is_windows() -> bool:
    """
    检查是否为Windows系统

    Returns:
        bool: 是Windows系统返回True，否则返回False
    """
    return platform.system().lower() == 'windows'


def system_is_linux() -> bool:
    """
    检查是否为Linux系统

    Returns:
        bool: 是Linux系统返回True，否则返回False
    """
    return platform.system().lower() == 'linux'


def system_is_macos() -> bool:
    """
    检查是否为macOS系统

    Returns:
        bool: 是macOS系统返回True，否则返回False
    """
    return platform.system().lower() == 'darwin'


def process_kill_by_pid(pid: int, force: bool = False) -> bool:
    """
    根据PID结束进程

    Args:
        pid (int): 进程ID
        force (bool): 是否强制结束进程，默认为False（正常结束）
                     True表示强制结束（SIGKILL），False表示正常结束（SIGTERM）

    Returns:
        bool: 成功结束进程返回True，失败返回False
    """
    try:
        # 检查PID是否有效
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError("PID必须是正整数")

        # 获取进程对象
        process = psutil.Process(pid)

        # 结束进程
        if force:
            # 强制结束进程
            process.kill()  # SIGKILL
        else:
            # 正常结束进程
            process.terminate()  # SIGTERM

        # 等待进程结束
        process.wait(timeout=3)
        return True

    except psutil.NoSuchProcess:
        # 进程不存在
        return False
    except psutil.AccessDenied:
        # 权限不足
        return False
    except psutil.TimeoutExpired:
        # 进程未在指定时间内结束，如果需要可以强制结束
        if not force:
            try:
                process.kill()
                process.wait(timeout=1)
                return True
            except Exception:
                return False
        return False
    except Exception:
        # 其他异常
        return False


def process_kill_by_name(name: str, force: bool = False) -> int:
    """
    根据进程名结束进程

    Args:
        name (str): 进程名
        force (bool): 是否强制结束进程，默认为False

    Returns:
        int: 成功结束的进程数量
    """
    killed_count = 0

    try:
        # 遍历所有进程
        for process in psutil.process_iter(['pid', 'name']):
            try:
                # 检查进程名是否匹配
                if process.info['name'].lower() == name.lower():
                    # 结束进程
                    if process_kill_by_pid(process.info['pid'], force):
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # 进程已不存在或权限不足，跳过
                continue

    except Exception:
        pass

    return killed_count


def port_check_process(port: int, protocol: str = 'tcp') -> Optional[Dict[str, Any]]:
    """
    检查端口被哪个程序占用

    Args:
        port (int): 端口号
        protocol (str): 协议类型，'tcp' 或 'udp'，默认为 'tcp'

    Returns:
        dict or None: 如果端口被占用，返回包含进程信息的字典；否则返回None
    """
    try:
        # 检查端口是否有效
        if not isinstance(port, int) or port < 0 or port > 65535:
            raise ValueError("端口号必须是0-65535之间的整数")

        # 检查协议类型
        protocol = protocol.lower()
        if protocol not in ['tcp', 'udp']:
            raise ValueError("协议类型必须是'tcp'或'udp'")

        # 遍历所有网络连接
        for conn in psutil.net_connections(kind=protocol):
            # 检查端口是否匹配
            if conn.laddr.port == port:
                # 获取进程信息
                try:
                    process = psutil.Process(conn.pid)
                    return {
                        'pid': conn.pid,
                        'name': process.name(),
                        'exe': process.exe(),
                        'cmdline': ' '.join(process.cmdline()),
                        'status': process.status(),
                        'port': port,
                        'protocol': protocol,
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 如果无法获取进程信息，返回基本连接信息
                    return {
                        'pid': conn.pid,
                        'name': "Unknown",
                        'exe': "Unknown",
                        'cmdline': "Unknown",
                        'status': "Unknown",
                        'port': port,
                        'protocol': protocol,
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                    }

        # 端口未被占用
        return None

    except Exception as e:
        # 发生异常时返回None
        return None


def port_get_processes(port: int) -> list:
    """
    获取占用指定端口的所有进程信息

    Args:
        port (int): 端口号

    Returns:
        list: 占用该端口的进程信息列表
    """
    processes = []

    try:
        # 检查TCP连接
        tcp_result = port_check_process(port, 'tcp')
        if tcp_result:
            processes.append(tcp_result)

        # 检查UDP连接
        udp_result = port_check_process(port, 'udp')
        if udp_result:
            processes.append(udp_result)

    except Exception:
        pass

    return processes




def system_shutdown(delay: int = 0, message: str = "") -> bool:
    """
    关闭计算机系统

    Args:
        delay (int): 延迟关机时间（秒），默认为0（立即关机）
        message (str): 关机前显示的消息，默认为空

    Returns:
        bool: 成功发起关机命令返回True，失败返回False
    """
    try:
        system = platform.system().lower()

        if system == "windows":
            # Windows系统关机命令
            if delay > 0:
                cmd = ["shutdown", "/s", "/t", str(delay)]
            else:
                cmd = ["shutdown", "/s", "/f", "/t", "0"]

            if message:
                cmd.extend(["/c", message])

        elif system in ["linux", "darwin"]:  # Linux or macOS
            # Unix/Linux/macOS系统关机命令
            if delay > 0:
                # 使用at命令实现延迟关机
                minutes = delay // 60
                if minutes > 0:
                    cmd = ["sudo", "shutdown", "-h", f"+{minutes}"]
                else:
                    cmd = ["sudo", "shutdown", "-h", "now"]
            else:
                cmd = ["sudo", "shutdown", "-h", "now"]

            if message:
                cmd.append(message)
        else:
            return False

        # 执行关机命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    except Exception:
        return False


def system_restart(delay: int = 0, message: str = "") -> bool:
    """
    重启计算机系统

    Args:
        delay (int): 延迟重启时间（秒），默认为0（立即重启）
        message (str): 重启前显示的消息，默认为空

    Returns:
        bool: 成功发起重启命令返回True，失败返回False
    """
    try:
        system = platform.system().lower()

        if system == "windows":
            # Windows系统重启命令
            if delay > 0:
                cmd = ["shutdown", "/r", "/t", str(delay)]
            else:
                cmd = ["shutdown", "/r", "/f", "/t", "0"]

            if message:
                cmd.extend(["/c", message])

        elif system in ["linux", "darwin"]:  # Linux or macOS
            # Unix/Linux/macOS系统重启命令
            if delay > 0:
                # 使用at命令实现延迟重启
                minutes = delay // 60
                if minutes > 0:
                    cmd = ["sudo", "shutdown", "-r", f"+{minutes}"]
                else:
                    cmd = ["sudo", "shutdown", "-r", "now"]
            else:
                cmd = ["sudo", "reboot"]

            if message:
                cmd.append(message)
        else:
            return False

        # 执行重启命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    except Exception:
        return False


def system_cancel_shutdown() -> bool:
    """
    取消已计划的关机或重启操作

    Returns:
        bool: 成功取消返回True，失败返回False
    """
    try:
        system = platform.system().lower()

        if system == "windows":
            # Windows系统取消关机命令
            cmd = ["shutdown", "/a"]
        elif system in ["linux", "darwin"]:
            # Unix/Linux/macOS系统取消关机命令
            cmd = ["sudo", "shutdown", "-c"]
        else:
            return False

        # 执行取消命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    except Exception:
        return False


if __name__ == '__main__':
    # 获取详细的系统版本信息
    system_info = system_get_version()
    for key, value in system_info.items():
        print(f"{key}: {value}")

    # 获取简化版系统版本信息
    simple_version = system_get_simple_version()
    print(f"系统版本: {simple_version}")

    # 检查系统类型
    if system_is_windows():
        print("当前系统: Windows")
    elif system_is_linux():
        print("当前系统: Linux")
    elif system_is_macos():
        print("当前系统: macOS")
    # system_empty_recycle_bin()
    cpu_info = system_get_cpu_info()
    print(f"CPU型号: {cpu_info['model']}")
    print(f"物理核心数: {cpu_info['cores']}")
    print(f"逻辑线程数: {cpu_info['threads']}")
    print(f"架构: {cpu_info['architecture']}")

    # 仅获取CPU型号
    cpu_model = system_get_cpu_model()
    print(f"CPU型号: {cpu_model}")

    # 获取CPU核心数
    cores = system_get_cpu_cores()
    print(f"CPU核心数: {cores}")

    # 获取CPU线程数
    threads = system_get_cpu_threads()
    print(f"CPU线程数: {threads}")
