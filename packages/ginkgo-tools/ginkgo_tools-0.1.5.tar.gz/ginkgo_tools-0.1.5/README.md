# Ginkgo Tools

一套实用的 Python 工具库，包含日志、时间处理和多线程相关的工具函数。

## 功能模块

### 日志工具 (tools_log)
- [console_log_debug](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_log.py#L12-L51): 标准的打印函数，输出时间、内容、调用的文件和函数，便于调试和问题追踪

### 时间工具 (tools_time)
- [trans_timestr_to_datetime](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L18-L70): 将多种格式的时间字符串转换为 datetime 对象
- [trans_timestr_to_stddatestr](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L72-L93): 将时间字符串转换为标准日期格式字符串
- [trans_datetime_to_describe](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L95-L128): 将 datetime 对象转换为描述性信息字典
- [get_week_dates](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L130-L148): 获取指定日期所在周的日期列表
- [get_week_range](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L150-L182): 获取指定日期所在周的开始和结束时间范围
- [get_month_range](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L184-L217): 获取指定日期所在月的开始和结束时间范围
- [get_quarter_range](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L219-L252): 获取指定日期所在季度的开始和结束时间范围
- [get_year_range](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L254-L291): 获取指定日期所在年的开始和结束时间范围
- [get_offset_date](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L325-L338): 获取相对于今天的偏移日期
- [create_timestamp_mark](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L340-L358): 创建时间戳标记（用于文件名等场景）
- [create_time_mark](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L360-L371): 创建时间标记（精确到毫秒，用于临时文件名等场景）
- [analyse_filename_time](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L373-L401): 从文件名中提取时间信息
- [analyse_fileattr_time](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_time.py#L403-L419): 从文件属性中获取修改时间

### 多线程工具 (tools_threading_target)
- [Base_Operation_Threading_Target](file://D:\Python_Project\#工具脚本\GINKGO-TOOLS\ginkgo_tools\tools_threading_target.py#L15-L32): 异步任务对象基类，用于创建多线程任务

## 安装

```bash
pip install ginkgo-tools
```

## 使用示例

### 日志工具使用示例
```python
from ginkgo_tools import console_log_debug

# 打印调试信息
console_log_debug("这是一条调试信息", "变量值:", variable)

# 异常处理中的日志打印
try:
    # 一些可能出错的代码
    pass
except Exception:
    console_log_debug("发生异常", onException=True)
```

### 时间工具使用示例
```python
from ginkgo_tools import (
    trans_timestr_to_datetime, 
    get_week_range, 
    create_time_mark
)

# 时间字符串转换
dt = trans_timestr_to_datetime("2024-03-08T16:34")

# 获取本周时间范围
week_start, week_end = get_week_range()

# 创建时间标记
time_mark = create_time_mark()
```

### 多线程工具使用示例
```python
from ginkgo_tools import Base_Operation_Threading_Target

class MyThreadTask(Base_Operation_Threading_Target):
    def run(self):
        # 实现具体的任务逻辑
        pass

# 创建并启动线程任务
task = MyThreadTask(target_object, operation_dict)
task.start()
```

## 支持的 Python 版本

- Python 3.6
- Python 3.7
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11