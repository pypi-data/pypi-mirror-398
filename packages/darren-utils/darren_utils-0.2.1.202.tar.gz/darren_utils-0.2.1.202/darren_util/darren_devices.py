# encoding:utf-8
# Copyright (C) 2021-2024 Liu Qinghao
__author__ = 'Liu Qinghao'
import platform

if platform.system() == "Windows":
    import wmi  # 硬件信息
else:
    wmi = None
import platform  # 系统版本信息

# 处理相对导入和绝对导入的兼容性问题
try:
    from .encry.darren_hash import hash_md5_string
except ImportError:
    try:
        from encry.darren_hash import hash_md5_string
    except ImportError:
        hash_md5_string = None


class GetHardwareInformation:
    '''
    获取当前电脑硬件信息,包括:
    主板序列号   get_board_id
    bios序列号   get_bios_id
    CPU序列号    get_cpu_id
    硬盘序列号   get_physical_disk_id
    显卡信息     get_gpu_info
    系统版本     get_system_info
    系统UUID     get_system_uuid
    获得所有硬件信息 get_all
    所有返回信息中的英文均大写
    '''

    def __init__(self) -> None:
        try:
            self.硬件信息 = wmi.WMI()
        except Exception as e:
            raise RuntimeError(f"无法初始化WMI服务: {e}")

    def get_physical_disk_id(self):
        """硬盘序列号"""
        try:
            result = ''
            for physical_disk in self.硬件信息.Win32_DiskDrive():
                result += (physical_disk.SerialNumber or '') + ' '
            return result.strip().upper()
        except Exception:
            return 'UNKNOWN'

    def get_cpu_id(self):
        """CPU序列号 获取费时间"""
        try:
            result = ''
            for cpu in self.硬件信息.Win32_Processor():
                result += (cpu.ProcessorId or '').strip() + ' '
            return result.strip().upper()
        except Exception:
            return 'UNKNOWN'

    def get_board_id(self):
        """主板序列号 获取速度快"""
        try:
            result = ''
            for board_id in self.硬件信息.Win32_BaseBoard():
                result += (board_id.SerialNumber or '') + ' '
            return result.strip().upper()
        except Exception:
            return 'UNKNOWN'

    def get_bios_id(self):
        """bios序列号 获取速度快"""
        try:
            result = ''
            for bios_id in self.硬件信息.Win32_BIOS():
                result += (bios_id.SerialNumber or '') + ' '
            return result.strip().upper()
        except Exception:
            return 'UNKNOWN'

    def get_gpu_info(self):
        """
        获取显卡信息，包括显卡名称和设备ID
        返回大写信息，如：NVIDIA GEFORCE GTX 1660 TI|PCI\VEN_10DE&DEV_2182
        """
        result = ''
        for gpu in self.硬件信息.Win32_VideoController():
            gpu_name = gpu.Name if gpu.Name else ''
            gpu_pnp = gpu.PNPDeviceID if gpu.PNPDeviceID else ''
            if gpu_name:
                gpu_info = gpu_name
                if gpu_pnp:
                    # 只取PNP ID的关键部分
                    gpu_info += '|'
                result += gpu_info + ' '
        return result.strip().upper()

    def get_system_info(self):
        """
        获取系统版本信息
        返回大写信息，如：WINDOWS_11_10.0.26200
        """
        try:
            system = platform.system()  # 操作系统名称，如 Windows
            release = platform.release()  # 版本号，如 11
            version = platform.version()  # 详细版本，如 10.0.26200
            result = f"{system}_{release}_{version}"
            return result.upper()
        except Exception:
            return 'UNKNOWN'

    def get_system_uuid(self):
        """
        获取Windows系统UUID（主板/系统产品UUID）
        返回大写信息，如：12345678-ABCD-1234-ABCD-123456789ABC
        """
        try:
            result = ''
            for item in self.硬件信息.Win32_ComputerSystemProduct():
                if item.UUID:
                    result += item.UUID + ' '
            return result.strip().upper() if result.strip() else 'UNKNOWN'
        except Exception:
            return 'UNKNOWN'

    def get_all(self):
        """列出所有硬件信息"""
        try:
            result = (
                f'主板序列号:{self.get_board_id()}\n'
                f'bios序列号:{self.get_bios_id()}\n'
                f'CPU序列号:{self.get_cpu_id()}\n'
                f'硬盘序列号:{self.get_physical_disk_id()}\n'
                f'显卡信息:{self.get_gpu_info()}\n'
                f'系统版本:{self.get_system_info()}\n'
                f'系统UUID:{self.get_system_uuid()}'
            )
            print( result)
            return result
        except Exception as e:
            return f"获取硬件信息失败: {e}"

    def get_devices_id(self):
        """获取设备指纹ID"""
        if hash_md5_string is None:
            raise RuntimeError("hash_md5_string 函数不可用")
        return hash_md5_string(self.get_all())


def get_devices_id():
    """获取设备指纹ID的便捷函数"""
    try:
        return GetHardwareInformation().get_devices_id()
    except Exception as e:
        raise RuntimeError(f"获取设备ID失败: {e}")


if __name__ == '__main__':
    try:
        print(get_devices_id())
    except Exception as e:
        print(f"错误: {e}")