from typing import Optional


def isOk() -> bool:
    """输入法是否可用（键盘是否已弹出）"""
    return False


def getText() -> str:
    """获取当前输入框文本"""
    return ""


def clearText() -> bool:
    """清空输入框文本"""
    return True


def input(text: str) -> str:
    """输入文本（content 为空时使用剪贴板）"""
    return text


def paste(text: Optional[str] = None) -> str:
    """粘贴文本（content 为空时使用剪贴板）"""
    return text or ""


def pressDel() -> str:
    """删除一个字符（返回剩余文本；空表示无数据）"""
    return ""


def pressEnter() -> bool:
    """回车键"""
    return True


def dismiss() -> bool:
    """隐藏键盘"""
    return True


def getClipboard() -> str:
    """获取剪贴板"""
    return ""


def setClipboard(text: str) -> bool:
    """设置剪贴板（键盘显示时）"""
    return True


def switchKeyboard() -> bool:
    """切换输入法"""
    return True
