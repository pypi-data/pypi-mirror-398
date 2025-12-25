from typing import Optional, TypedDict


class LogViewParams(TypedDict, total=False):
    """悬浮窗日志窗口显示参数"""

    width: Optional[int]  # 宽度（默认 300）
    height: Optional[int]  # 高度（默认 400）
    textSize: Optional[int]  # 文本字体大小（默认 14）
    textColor: Optional[str]  # 文本颜色（默认 #FFFFFF）
    backgroundColor: Optional[str]  # 背景颜色（默认 #000000）


def setLogViewParams(params: Optional[LogViewParams] = None):
    """设置悬浮窗日志窗口的显示参数（需在显示前调用）"""
    pass


def isPipActive() -> bool:
    """是否开启了悬浮窗"""
    return False


def showLogWindow() -> bool:
    """显示日志窗口（App 必须在前台）"""
    return True


def closeLogWindow() -> bool:
    """关闭日志窗口（App 必须在前台）"""
    return True


def setPipCtrlScript(ctrl: bool) -> bool:
    """设置是否允许悬浮窗控制脚本启停"""
    return True
