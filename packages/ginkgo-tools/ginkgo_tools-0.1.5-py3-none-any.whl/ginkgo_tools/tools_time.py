"""
时间处理工具模块
提供各种时间格式转换和时间计算功能
"""
import datetime
import re
import os
import time
from typing import Optional, List, Tuple, Union
from .tools_log import console_log_debug

# 定义中国时区
CHINA_TZ = datetime.timezone(datetime.timedelta(hours=8))


def trans_timestr_to_datetime(time_str: str, remove_tzinfo: bool = False, target_tz: Optional[datetime.timezone] = None) -> Optional[datetime.datetime]:
    """
    将时间字符串转换为datetime对象
    
    支持多种时间格式:
    - 各种ISO 8601格式变体
        - "2024-03-08T16:34" (ISO格式)
        - '2011-06-24T06:39:24.000Z' (ISO格式)
    - "2024-03-08" (日期格式)
    - "20240308163400" (紧凑型日期时间格式)
    - "202403081634" (紧凑型日期时间格式，分钟级)
    - "2024030816" (紧凑型日期时间格式，小时级)
    - "20240308" (紧凑型日期格式)

    
    Args:
        time_str (str): 时间字符串
        remove_tzinfo (bool): 是否移除时区信息，默认为False，返回带时区的datetime对象；
                             如果为True，则移除时区信息，返回naive datetime对象
        target_tz (Optional[datetime.timezone]): 目标时区，默认为中国时区（UTC+8）
        
    Returns:
        Optional[datetime.datetime]: 转换后的时间对象，失败时返回None
        
    Example:
        >>> trans_timestr_to_datetime("2024-03-08T16:34")
        datetime.datetime(2024, 3, 9, 0, 34, tzinfo=datetime.timezone(datetime.timedelta(seconds=28800)))
        >>> trans_timestr_to_datetime("2024-03-08T16:34Z", remove_tzinfo=True)
        datetime.datetime(2024, 3, 9, 0, 34)
        >>> import datetime
        >>> utc_tz = datetime.timezone.utc
        >>> trans_timestr_to_datetime("2024-03-08T16:34Z", target_tz=utc_tz)
        datetime.datetime(2024, 3, 8, 16, 34, tzinfo=datetime.timezone.utc)
    """
    if not time_str:
        return None
        
    # 如果没有指定目标时区，默认使用中国时区
    if target_tz is None:
        target_tz = CHINA_TZ
        
    datetime_target = None
    try:
        if "T" in time_str:
            # 处理各种ISO 8601格式
            datetime_target = _parse_iso_format(time_str)
            # 统一转换为目标时区
            if datetime_target:
                # 如果有明确的时区信息，先转换到目标时区
                # 如果没有时区信息，假定它是UTC时间，先加上UTC时区，再转换到目标时区
                if datetime_target.tzinfo is not None:
                    datetime_target = datetime_target.astimezone(target_tz)
                else:
                    # 假设为UTC时间
                    datetime_target = datetime_target.replace(tzinfo=datetime.timezone.utc).astimezone(target_tz)
        elif "-" in time_str:
            # 处理日期格式（可能包含时间）
            # 通过空格判断是否包含时间部分
            if " " in time_str:
                # 包含时间部分，尝试不同的时间格式
                date_part, time_part = time_str.split(" ", 1)
                
                # 尝试不同时间格式
                time_formats = [
                    "%H:%M:%S",  # 时:分:秒 (如 16:34:00)
                    "%H:%M",     # 时:分 (如 16:34)
                    "%H"         # 时 (如 16)
                ]
                
                for time_format in time_formats:
                    try:
                        time_obj = datetime.datetime.strptime(time_part, time_format)
                        date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")
                        datetime_target = datetime.datetime.combine(date_obj.date(), time_obj.time()).replace(tzinfo=target_tz)
                        break  # 成功解析则跳出循环
                    except ValueError:
                        continue  # 继续尝试下一种格式
                        
                # 如果所有格式都失败，则走默认的None
            else:
                # 纯日期格式: "2024-03-08"
                datetime_target = datetime.datetime.strptime(time_str, "%Y-%m-%d").replace(
                    hour=0, minute=0, second=0, microsecond=0, tzinfo=target_tz)
        else:
            # 紧凑型格式
            if len(time_str) == 14:
                # 20240308163400
                datetime_target = datetime.datetime.strptime(time_str, "%Y%m%d%H%M%S").replace(tzinfo=target_tz)
            elif len(time_str) == 12:
                # 202403081634
                datetime_target = datetime.datetime.strptime(time_str, '%Y%m%d%H%M').replace(tzinfo=target_tz)
            elif len(time_str) == 10:
                # 2024030816
                datetime_target = datetime.datetime.strptime(time_str, '%Y%m%d%H').replace(tzinfo=target_tz)
            elif len(time_str) == 8:
                # 20240308
                datetime_target = datetime.datetime.strptime(time_str, '%Y%m%d').replace(tzinfo=target_tz)
            
        # 统一处理是否移除时区信息
        if datetime_target and remove_tzinfo:
            datetime_target = datetime_target.replace(tzinfo=None)
            
    except Exception as e:
        console_log_debug("时间转换异常！！！", time_str, onException=True)

    return datetime_target


def _parse_iso_format(time_str: str) -> Optional[datetime.datetime]:
    """
    解析各种ISO 8601格式的时间字符串
    
    支持的格式包括:
    - 2011-06-24T06:39:24.000Z
    - 2011-06-24T06:39:24Z
    - 2011-06-24T06:39:24+08:00
    - 2011-06-24T06:39:24+0800
    - 2011-06-24T06:39:24.123+08:00
    - 2011-06-24T06:39:24
    - 2024-03-08T16:34
    
    Args:
        time_str (str): ISO格式的时间字符串
        
    Returns:
        Optional[datetime.datetime]: 解析后的时间对象
    """
    # 尝试使用datetime.fromisoformat (Python 3.7+)
    try:
        # Python 3.7+的fromisoformat不支持"Z"结尾表示UTC，需要替换为"+00:00"
        if time_str.endswith('Z'):
            # 替换末尾的Z为+00:00
            formatted_str = time_str[:-1] + '+00:00'
            return datetime.datetime.fromisoformat(formatted_str)
        else:
            return datetime.datetime.fromisoformat(time_str)
    except ValueError:
        pass
    
    # 如果fromisoformat失败，尝试手动解析常见格式
    try:
        if "Z" in time_str:
            # ISO格式: 2011-06-24T06:39:24.000Z 或 2011-06-24T06:39:24Z
            if "." in time_str:
                return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)
            else:
                return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        elif "+" in time_str or time_str.count('-') > 2:
            # 带时区偏移: 2011-06-24T06:39:24+08:00 或 2011-06-24T06:39:24-05:00
            # 注意：strptime不直接支持时区偏移，我们需要手动处理
            if "." in time_str:
                # 带毫秒
                if ":" in time_str[-6:]:  # +08:00 格式
                    dt_part, tz_part = time_str.rsplit('+', 1) if '+' in time_str else time_str.rsplit('-', 1)
                    sign = '-' if '-' in time_str[-6:] else '+'
                    base_dt = datetime.datetime.strptime(dt_part, "%Y-%m-%dT%H:%M:%S.%f")
                else:  # +0800 格式
                    dt_part = time_str[:-5]
                    tz_sign = time_str[-5]
                    tz_hours = int(time_str[-4:-2])
                    tz_minutes = int(time_str[-2:])
                    base_dt = datetime.datetime.strptime(dt_part, "%Y-%m-%dT%H:%M:%S.%f")
                    # 这里简单处理为无时区信息的本地时间
                    return base_dt
            else:
                # 不带毫秒
                if ":" in time_str[-6:]:  # +08:00 格式
                    dt_part, tz_part = time_str.rsplit('+', 1) if '+' in time_str else time_str.rsplit('-', 1)
                    base_dt = datetime.datetime.strptime(dt_part, "%Y-%m-%dT%H:%M:%S")
                else:  # +0800 格式
                    dt_part = time_str[:-5]
                    base_dt = datetime.datetime.strptime(dt_part, "%Y-%m-%dT%H:%M:%S")
                    # 这里简单处理为无时区信息的本地时间
                    return base_dt
            # 对于时区信息，简单处理为本地时间
            return base_dt
        else:
            # 无时区信息: 2011-06-24T06:39:24 或 2024-03-08T16:34
            if len(time_str) == 16:
                # ISO格式: 2024-03-08T16:34
                return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M").replace(second=0, microsecond=0)
            elif "." in time_str:
                # 带毫秒: 2011-06-24T06:39:24.123
                return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f")
            else:
                # 标准格式: 2011-06-24T06:39:24
                return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        pass
    
    return None


def trans_timestr_to_stddatestr(time_str: str) -> Optional[str]:
    """
    将时间字符串转换为标准日期格式字符串
    
    Args:
        time_str (str): 时间字符串，格式应为 "%Y-%m-%d"
        
    Returns:
        Optional[str]: 标准日期格式字符串 "YYYY-MM-DD"，失败时返回None
        
    Example:
        >>> trans_timestr_to_stddatestr("2024-03-08")
        "2024-03-08"
    """
    try:
        return datetime.datetime.strptime(time_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return None


def trans_datetime_to_describe(datetime_i: datetime.datetime) -> dict:
    """
    将datetime对象转换为描述性信息字典
    
    Args:
        datetime_i (datetime.datetime): datetime对象
        
    Returns:
        dict: 包含多种时间格式和描述的字典
            - datestr_Ymd: "YYYY-MM-DD"格式
            - datestr_BdY: "Month DD, YYYY"格式
            - datetimestr_Ymd_HMS: "YYYY-MM-DD HH:MM:SS"格式
            - weekday: 中文星期描述
            - workday: 工作日/周末标识
    """
    describe_dict = {}
    describe_dict["datestr_Ymd"] = datetime_i.strftime("%Y-%m-%d")
    describe_dict["datestr_BdY"] = datetime_i.strftime("%B %d, %Y")  # May 21, 2017
    describe_dict["datetimestr_Ymd_HMS"] = datetime_i.strftime("%Y-%m-%d %H:%M:%S")
    
    weekday_map = {
        0: ("星期一", "工作日"),
        1: ("星期二", "工作日"),
        2: ("星期三", "工作日"),
        3: ("星期四", "工作日"),
        4: ("星期五", "工作日"),
        5: ("星期六", "周末"),
        6: ("星期日", "周末")
    }
    
    weekday, workday = weekday_map[datetime_i.weekday()]
    describe_dict["weekday"] = weekday
    describe_dict["workday"] = workday
    
    return describe_dict


def get_week_dates(std_datetime: Union[datetime.datetime, datetime.date, None] = None) -> List[datetime.date]:
    """
    获取指定日期所在周的日期列表
    
    Args:
        std_datetime (Union[datetime.datetime, datetime.date, None], optional): 
            指定日期，支持datetime和date类型，默认为当前日期
        
    Returns:
        List[datetime.date]: 一周七天的日期列表（周一到周日）
    """
    if std_datetime is None:
        std_datetime = datetime.datetime.now()
        
    # 统一转换为date类型处理
    if isinstance(std_datetime, datetime.datetime):
        std_date = std_datetime.date()
    else:
        std_date = std_datetime
        
    # 计算本周一日期
    monday = std_date - datetime.timedelta(days=std_date.weekday())
    return [monday + datetime.timedelta(days=i) for i in range(7)]


def get_week_range(std_datetime: Union[datetime.datetime, datetime.date, None] = None, 
                   last: bool = False) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    获取指定日期所在周的开始和结束时间范围
    
    Args:
        std_datetime (Union[datetime.datetime, datetime.date, None], optional): 
            指定日期，支持datetime和date类型，默认为当前日期
        last (bool): 是否获取上周范围
        
    Returns:
        Tuple[datetime.datetime, datetime.datetime]: (开始时间, 结束时间)元组
            开始时间为周一 00:00:00.000000
            结束时间为周日 23:59:59.999999
    """
    if std_datetime is None:
        std_datetime = datetime.datetime.now()
        
    # 统一转换为date类型处理
    if isinstance(std_datetime, datetime.datetime):
        std_date = std_datetime.date()
    else:
        std_date = std_datetime
        
    if last:
        # 计算上周一
        monday = std_date - datetime.timedelta(days=std_date.weekday() + 7)
    else:
        # 计算本周一
        monday = std_date - datetime.timedelta(days=std_date.weekday())
        
    # 设置时间为 00:00:00.000000
    start_time = datetime.datetime.combine(monday, datetime.time.min)
    # 设置结束时间为周日 23:59:59.999999
    end_time = datetime.datetime.combine(monday + datetime.timedelta(days=6), datetime.time.max)
    
    return (start_time, end_time)


def get_month_range(std_datetime: Union[datetime.datetime, datetime.date, None] = None, 
                    last: bool = False) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    获取指定日期所在月的开始和结束时间范围
    
    Args:
        std_datetime (Union[datetime.datetime, datetime.date, None], optional): 
            指定日期，支持datetime和date类型，默认为当前日期
        last (bool): 是否获取上月范围
        
    Returns:
        Tuple[datetime.datetime, datetime.datetime]: (开始时间, 结束时间)元组
            开始时间为月初 00:00:00.000000
            结束时间为月末 23:59:59.999999
    """
    if std_datetime is None:
        std_datetime = datetime.datetime.now()
        
    # 统一转换为date类型处理
    if isinstance(std_datetime, datetime.datetime):
        std_date = std_datetime.date()
    else:
        std_date = std_datetime
        
    if last:
        # 计算上月第一天
        first_day = (std_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    else:
        # 本月第一天
        first_day = std_date.replace(day=1)
        
    # 计算月末日期
    if first_day.month == 12:
        end_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - datetime.timedelta(days=1)
    else:
        end_day = first_day.replace(month=first_day.month + 1, day=1) - datetime.timedelta(days=1)
        
    # 设置时间为 00:00:00.000000 和 23:59:59.999999
    start_time = datetime.datetime.combine(first_day, datetime.time.min)
    end_time = datetime.datetime.combine(end_day, datetime.time.max)
        
    return (start_time, end_time)


def get_quarter_range(std_datetime: Union[datetime.datetime, datetime.date, None] = None, 
                      last: bool = False) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    获取指定日期所在季度的开始和结束时间范围
    
    Args:
        std_datetime (Union[datetime.datetime, datetime.date, None], optional): 
            指定日期，支持datetime和date类型，默认为当前日期
        last (bool): 是否获取上季度范围
        
    Returns:
        Tuple[datetime.datetime, datetime.datetime]: (开始时间, 结束时间)元组
            开始时间为季度初 00:00:00.000000
            结束时间为季度末 23:59:59.999999
    """
    if std_datetime is None:
        std_datetime = datetime.datetime.now()
        
    # 统一转换为date类型处理
    if isinstance(std_datetime, datetime.datetime):
        std_date = std_datetime.date()
    else:
        std_date = std_datetime
        
    if last:
        # 上个季度的标记日期
        mark_date = std_date.replace(day=1, month=(std_date.month - 1) // 3 * 3 + 1) - datetime.timedelta(days=1)
    else:
        mark_date = std_date
        
    # 季度第一天
    first_day = mark_date.replace(day=1, month=(mark_date.month - 1) // 3 * 3 + 1)
    # 季度最后一天
    end_month_first = first_day.replace(month=first_day.month + 2, day=1)
    if end_month_first.month > 12:
        end_month_first = end_month_first.replace(year=end_month_first.year + 1, month=end_month_first.month - 12)
        
    if end_month_first.month == 12:
        end_day = end_month_first.replace(year=end_month_first.year + 1, month=1, day=1) - datetime.timedelta(days=1)
    else:
        end_day = end_month_first.replace(month=end_month_first.month + 1, day=1) - datetime.timedelta(days=1)
        
    # 设置时间为 00:00:00.000000 和 23:59:59.999999
    start_time = datetime.datetime.combine(first_day, datetime.time.min)
    end_time = datetime.datetime.combine(end_day, datetime.time.max)
        
    return (start_time, end_time)


def get_year_range(std_datetime: Union[datetime.datetime, datetime.date, None] = None, 
                   last: bool = False) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    获取指定日期所在年的开始和结束时间范围
    
    Args:
        std_datetime (Union[datetime.datetime, datetime.date, None], optional): 
            指定日期，支持datetime和date类型，默认为当前日期
        last (bool): 是否获取去年范围
        
    Returns:
        Tuple[datetime.datetime, datetime.datetime]: (开始时间, 结束时间)元组
            开始时间为年初 00:00:00.000000
            结束时间为年末 23:59:59.999999
    """
    if std_datetime is None:
        std_datetime = datetime.datetime.now()
        
    # 统一转换为date类型处理
    if isinstance(std_datetime, datetime.datetime):
        std_date = std_datetime.date()
    else:
        std_date = std_datetime
        
    if last:
        # 去年第一天
        first_day = std_date.replace(year=std_date.year - 1, month=1, day=1)
    else:
        # 今年第一天
        first_day = std_date.replace(year=std_date.year, month=1, day=1)
        
    # 今年最后一天
    end_day = std_date.replace(year=std_date.year, month=12, day=31)
    
    # 设置时间为 00:00:00.000000 和 23:59:59.999999
    start_time = datetime.datetime.combine(first_day, datetime.time.min)
    end_time = datetime.datetime.combine(end_day, datetime.time.max)
    
    return (start_time, end_time)


def get_offset_date(offset: int = 1) -> datetime.date:
    """
    获取相对于今天的偏移日期
    
    Args:
        offset (int): 偏移天数，正数表示未来，负数表示过去，默认为1
        
    Returns:
        datetime.date: 偏移后的日期
    """
    return datetime.date.today() + datetime.timedelta(days=offset)


def create_timestamp_mark(digit: int = 5) -> str:
    """
    创建时间戳标记（用于文件名等场景）
    
    Args:
        digit (int): 返回的位数，默认为5位
        
    Returns:
        str: 时间戳标记字符串
    """
    timemark = int(time.time() * 1000000)  # 去掉小数位
    timemark_str = str(timemark)[-digit:]
    return timemark_str


def create_time_mark() -> str:
    """
    创建时间标记（精确到毫秒，用于临时文件名等场景）
    
    Returns:
        str: 17位时间戳字符串，格式为"YYYYMMDDHHMMSS.SSS"
    """
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S.%f")[:-3]


def analyse_filename_time(filename: str) -> Optional[datetime.datetime]:
    """
    从文件名中提取时间信息
    
    Args:
        filename (str): 文件名
        
    Returns:
        Optional[datetime.datetime]: 提取到的时间对象，未找到或解析失败时返回None
    """
    # 清理文件名中的分隔符
    cleaned_filename = filename.replace("-", "").replace("_", "").replace(".", "").replace(" ", "").replace(":", "")
    
    # 匹配8-14位数字
    match_result = re.search(r"\d{8,14}", cleaned_filename)

    the_time = None
    if match_result:
        time_str = match_result.group()
        try:
            if len(time_str) == 14:
                # YYYYMMDDHHMMSS
                the_time = datetime.datetime.strptime(time_str, "%Y%m%d%H%M%S")
            elif len(time_str) == 12:
                # YYYYMMDDHHMM
                the_time = datetime.datetime.strptime(time_str, '%Y%m%d%H%M')
            elif len(time_str) == 10:
                # YYYYMMDDHH
                the_time = datetime.datetime.strptime(time_str, '%Y%m%d%H')
            elif len(time_str) == 8:
                # YYYYMMDD
                the_time = datetime.datetime.strptime(time_str, '%Y%m%d')
        except Exception as e:
            # 解析失败，保持the_time为None
            pass
            
    return the_time


def analyse_fileattr_time(file_path: str) -> Optional[datetime.datetime]:
    """
    从文件属性中获取修改时间
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        Optional[datetime.datetime]: 文件修改时间，失败时返回None
    """
    the_time = None
    try:
        time_stamp = os.path.getmtime(file_path)
        the_time = datetime.datetime.fromtimestamp(time_stamp)
    except Exception as e:
        # 获取失败，保持the_time为None
        pass
        
    return the_time