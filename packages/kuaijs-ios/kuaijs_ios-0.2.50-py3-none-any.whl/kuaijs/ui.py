from typing import Any, Callable


def show():
    return None


def showToast(message: str):
    """显示 Toast 提示

    参数:
      message: 提示消息字符串
    返回:
      None
    """
    pass


def confirm(title: str, message: str) -> bool:
    """显示确认对话框

    参数:
      title: 对话框标题
      message: 对话框内容
    返回:
      bool: 用户是否点击“确定”
    """
    return False


def confirmInput(title: str, message: str) -> str:
    """显示输入对话框

    参数:
      title: 对话框标题
      message: 对话框内容
    返回:
      str: 用户输入文本；取消返回空字符串
    """
    return ""


def alert(title: str, message: str):
    """显示警告对话框

    参数:
      title: 对话框标题
      message: 对话框内容
    返回:
      None
    """
    pass


UIEventCallback = Callable[[str, dict[str, Any]], None]


def onEvent(callback: UIEventCallback):
    """设置事件回调函数

    参数:
      callback: 回调函数签名为 (event: str, data: dict[str, Any]) -> None。
                data 为字典对象（WebView 端传入的对象会被转换为 Python 对象）。
    返回:
      None
    """
    pass


def call(key: str, data: dict[str, Any]):
    """调用网页中通过 ms.registerUIFunc 注册的函数

    参数:
      key: 注册的函数名
      data: 传入数据（字典），Python 侧都会转换为原生对象
    返回:
      None
    """
    pass


def eval(code: str):
    """执行JavaScript代码

    参数:
      code: JavaScript 代码字符串
    返回:
      None
    """
    pass
