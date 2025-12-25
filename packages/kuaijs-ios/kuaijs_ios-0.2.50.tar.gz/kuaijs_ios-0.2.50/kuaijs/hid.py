from typing import List, Optional, Literal, Union, TypedDict


class AppInfo(TypedDict):
    """应用信息"""

    name: str  # 应用名称
    bundleId: str  # 应用 Bundle ID


class HIDKey:
    """HID 按键常量映射"""

    COMMAND = 0
    LEFT_CTRL = 0
    LEFT_SHIFT = 0
    LEFT_ALT = 0
    RIGHT_CTRL = 0
    RIGHT_SHIFT = 0
    RIGHT_ALT = 0
    UP_ARROW = 0
    DOWN_ARROW = 0
    LEFT_ARROW = 0
    RIGHT_ARROW = 0
    SPACE = 0
    BACKSPACE = 0
    TAB = 0
    RETURN = 0
    ESC = 0
    INSERT = 0
    DELETE = 0
    PAGE_UP = 0
    PAGE_DOWN = 0
    HOME = 0
    END = 0
    CAPS_LOCK = 0
    F1 = 0
    F2 = 0
    F3 = 0
    F4 = 0
    F5 = 0
    F6 = 0
    F7 = 0
    F8 = 0
    F9 = 0
    F10 = 0
    F11 = 0
    F12 = 0

    def __getitem__(self, key: str) -> int:
        return getattr(self, key, 0)


hidKey = HIDKey()
"""HID 按键常量映射。

用于组合键发送：可通过 hidKey.COMMAND、hidKey.LEFT_CTRL 等取得修饰键代码，
也支持字典访问 hidKey["COMMAND"] 与直接传入字符串名称（如 "COMMAND"）。
示例：
    from kuaijs import hid
    hid.sendKey([hid.hidKey.COMMAND, "c"])    # 复制（点属性）
    hid.sendKey([hid.hidKey["COMMAND"], "c"])  # 复制（字典）
    hid.sendKey(["COMMAND", "v"])             # 粘贴（字符串键名）
"""


def openRecordScreen() -> bool:
    """打开录屏界面

    返回:
      bool: 是否成功开始录屏界面

    示例:
        from kuaijs import hid
        hid.openRecordScreen()
    """
    return True


def isRecording() -> bool:
    """录屏是否开启

    返回:
      bool: 是否正在录屏

    示例:
        from kuaijs import hid
        if hid.isRecording():
            ...
    """
    return True


# 设置动作抖动值（像素，随屏幕 scale 适配）
def setJitterValue(value: int):
    """设置动作抖动值（像素，随屏幕 scale 适配）"""
    pass


# 重置坐标系方向（如 "portrait" | "landscape"）
def resetPosition(orientation: Literal["PORTRAIT", "LANDSCAPE"] = "PORTRAIT"):
    """重置坐标系方向

    参数:
      orientation: 屏幕方向（PORTRAIT/LANDSCAPE）
    """
    pass


def move(x: int, y: int) -> bool:
    """移动坐标

    参数:
      x/y: 坐标
    返回:
      bool: 是否成功
    """
    return True


def click(x: int, y: int, duration: int = 10, jitter: bool = False) -> bool:
    """点击指定坐标

    参数:
      x/y: 坐标
      duration: 按下时长（毫秒，默认 10ms）
      jitter: 是否启用抖动（默认 False）
    返回:
      bool: 是否成功
    """
    return True


def clickRandom(x1: int, y1: int, x2: int, y2: int, duration: int = 20) -> bool:
    """随机点击指定矩形区域

    参数:
      x1/y1/x2/y2: 矩形区域坐标
      duration: 按下时长（毫秒，默认 20ms）
    返回:
      bool: 是否成功
    """
    return True


def doubleClick(
    x: int, y: int, duration: int = 20, interval: int = 20, jitter: bool = False
) -> bool:
    """双击指定坐标

    参数:
      x/y: 坐标
      duration: 每次按下时长（毫秒，默认 20ms）
      interval: 两次点击间隔（毫秒，默认 20ms）
      jitter: 是否启用抖动（默认 False）
    返回:
      bool: 是否成功
    """
    return True


def doubleClickRandom(
    x1: int, y1: int, x2: int, y2: int, duration: int = 20, interval: int = 20
) -> bool:
    """随机双击矩形区域

    参数:
      x1/y1/x2/y2: 矩形区域坐标
      duration: 每次按下时长（毫秒，默认 20ms）
      interval: 两次点击间隔（毫秒，默认 20ms）
    返回:
      bool: 是否成功
    """
    return True


def swipe(
    x: int, y: int, ex: int, ey: int, jitter: bool = False, steps: int = 6
) -> bool:
    """直线滑动

    参数:
      x/y: 起点坐标
      ex/ey: 终点坐标
      jitter: 是否启用抖动（默认 False）
      steps: 轨迹点数量（默认 6）
    """
    return True


def swipeCurve(
    startX: int, startY: int, midX: int, midY: int, endX: int, endY: int
) -> bool:
    """3 点曲线滑动
    参数:
      startX/startY: 起点坐标
      midX/midY: 中间点坐标
      endX/endY: 终点坐标
    返回:
      bool: 是否成功
    """
    return True


def pressAndSwipe(
    startX: int,
    startY: int,
    endX: int,
    endY: int,
    duration: int = 500,
    jitter: bool = False,
    steps: int = 6,
) -> bool:
    """长按并滑动

    参数:
      startX/startY: 起点坐标
      endX/endY: 终点坐标
      duration: 长按时间（毫秒，默认 500ms）
      jitter: 是否启用抖动（默认 False）
      steps: 轨迹点数量（默认 6）
    返回:
      bool: 是否成功
    """
    return True


def homeScreen() -> bool:
    """回主页
    返回:
      bool: 是否成功
    """
    return True


def inputSimple(text: str) -> bool:
    """输入简单文本（只支持英文）

    参数:
      text: 要输入的文本
    返回:
      bool: 是否成功
    """
    return True


def space() -> bool:
    """空格键
    返回:
      bool: 是否成功
    """
    return True


def backspace() -> bool:
    """删除键
    返回:
      bool: 是否成功
    """
    return True


def enter() -> bool:
    """回车键
    返回:
      bool: 是否成功
    """
    return True


def sendKey(keys: List[Union[int, str]]) -> bool:
    """发送组合按键（支持数字或字符）
    参数:
      keys: 按键列表（数字或字符）
    返回:
      bool: 是否成功
    """
    return True


def copyText() -> bool:
    """复制文本（Command+C）
    返回:
      bool: 是否成功
    """
    return True


def pasteText() -> bool:
    """粘贴文本（Command+V）
    返回:
      bool: 是否成功
    """
    return True


def back() -> bool:
    """返回（Tab+B）
    返回:
      bool: 是否成功
    """
    return True


def recent() -> bool:
    """APP 切换器
    返回:
      bool: 是否成功
    """
    return True


def lock() -> bool:
    """锁屏
    返回:
      bool: 是否成功
    """
    return True


def unlock() -> bool:
    """解锁
    返回:
      bool: 是否成功
    """
    return True


def openURL(url: str) -> bool:
    """打开 URL
    参数:
      url: URL 地址
    返回:
      bool: 是否成功
    """
    return True


def openApp(name: str) -> bool:
    """打开 App
    参数:
      name: App 名称
    返回:
      bool: 是否成功
    """
    return True


def takeMeToFront() -> bool:
    """切到前台
    返回:
      bool: 是否成功
    """
    return True


def currentAppInfo() -> Optional[AppInfo]:
    """当前应用信息（仅 iOS18+）
    返回:
      AppInfo: 当前应用信息
    """
    return None


def setClipboard(text: str) -> bool:
    """设置剪贴板
    参数:
      text: 要设置的文本
    返回:
      bool: 是否成功
    """
    return True


def getClipboard() -> str:
    """获取剪贴板
    返回:
      str: 剪贴板文本
    """
    return ""


def customButton(button: int) -> bool:
    """执行自定义按钮（1-11）
    参数:
      button: 按钮编号（1-11）
    返回:
      bool: 是否成功
    """
    return True
