import datetime
import random
import time


def time_get_timestamp(is_10_digits=False):
    """
    获取当前时间戳

    Args:
        is_10_digits (bool): 是否返回10位时间戳，默认为False（返回13位毫秒时间戳）

    Returns:
        int: 时间戳
    """
    if is_10_digits:
        # 返回10位时间戳（秒级）
        return int(time.time())
    else:
        # 返回13位时间戳（毫秒级）
        return int(time.time() * 1000)
def time_random_timestamp():
    """
    生成一个随机的时间戳（类似0.842703761170252格式的小数）

    Returns:
        float: 随机时间戳
    """
    return random.random()
def time_format(time_value, date_format=None, time_format=None, is_24_hour=True):
    """
    格式化指定日期与时间，失败返回空文本

    Args:
        time_value (datetime.datetime or int or float): 欲格式化的时间
        date_format (str, optional): 日期格式，如: yyyy/M/d dddd(年/月/日 星期几)
        time_format (str, optional): 时间格式，如: hh:mm:ss(小时:分钟:秒)
        is_24_hour (bool, optional): 是否为24小时制，默认为True

    Returns:
        str: 格式化后的日期时间字符串，失败返回空字符串
    """
    try:
        # 处理不同类型的输入时间
        if isinstance(time_value, (int, float)):
            # 如果是时间戳，转换为datetime对象
            if time_value > 10000000000:  # 13位时间戳
                time_value = datetime.datetime.fromtimestamp(time_value / 1000)
            else:  # 10位时间戳
                time_value = datetime.datetime.fromtimestamp(time_value)
        elif not isinstance(time_value, datetime.datetime):
            return ""

        # 默认格式
        if date_format is None and time_format is None:
            return time_value.strftime("%Y-%m-%d %H:%M:%S")

        # 构建格式化字符串
        format_str = ""

        # 处理日期格式
        if date_format:
            # 替换易语言格式为Python格式
            date_format = date_format.replace("yyyy", "%Y")
            date_format = date_format.replace("MM", "%m")
            date_format = date_format.replace("M", "%m")
            date_format = date_format.replace("dd", "%d")
            date_format = date_format.replace("d", "%d")
            date_format = date_format.replace("dddd", "%A")
            format_str += date_format

        # 添加空格分隔符
        if date_format and time_format:
            format_str += " "

        # 处理时间格式
        if time_format:
            # 处理上午/下午
            if "tt" in time_format:
                if is_24_hour:
                    time_format = time_format.replace("tt", "")
                    time_format = time_format.replace("hh", "%H")
                    time_format = time_format.replace("h", "%H")
                else:
                    time_format = time_format.replace("tt", "%p")
                    time_format = time_format.replace("hh", "%I")
                    time_format = time_format.replace("h", "%I")
            else:
                time_format = time_format.replace("hh", "%H")
                time_format = time_format.replace("h", "%H")

            time_format = time_format.replace("mm", "%M")
            time_format = time_format.replace("m", "%M")
            time_format = time_format.replace("ss", "%S")
            time_format = time_format.replace("s", "%S")

            format_str += time_format

        # 格式化时间
        result = time_value.strftime(format_str.strip())

        # 处理星期中文显示
        if "%A" in format_str:
            weekdays = {
                'Monday': '星期一',
                'Tuesday': '星期二',
                'Wednesday': '星期三',
                'Thursday': '星期四',
                'Friday': '星期五',
                'Saturday': '星期六',
                'Sunday': '星期日'
            }
            for eng, chn in weekdays.items():
                result = result.replace(eng, chn)

        # 处理上午/下午中文显示
        if "%p" in format_str:
            result = result.replace("AM", "上午").replace("PM", "下午")

        return result

    except Exception as e:
        raise  e