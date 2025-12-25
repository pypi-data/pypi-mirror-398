def setLoggerLevel(level: str):
    """设置日志级别

    参数:
      level: 日志级别（error|warn|info|debug|off）
    返回:
      None
    """
    pass


def setLogToFile(enabled: bool):
    """设置是否输出到日志文件

    参数:
      enabled: True 启用文件输出；False 关闭文件输出
    返回:
      None
    """
    pass


def setMaxLogFileCount(count: int):
    """设置最大日志文件数量（默认 10 个）"""
    pass


def setMaxLogFileSize(size: int):
    """设置最大日志文件大小（单位 MB，默认 10MB）"""
    pass


def resetLogFile():
    """重置日志文件（创建新文件并开始写入）"""
    pass


def debug(*args: object):
    """输出调试日志（将参数按空格拼接为字符串）"""
    pass


def info(*args: object):
    """输出信息日志（将参数按空格拼接为字符串）"""
    pass


def warn(*args: object):
    """输出警告日志（将参数按空格拼接为字符串）"""
    pass


def error(*args: object):
    """输出错误日志（将参数按空格拼接为字符串）"""
    pass
