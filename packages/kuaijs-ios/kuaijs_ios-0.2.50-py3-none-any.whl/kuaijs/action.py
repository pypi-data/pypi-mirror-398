from typing import List, Literal, TypedDict


class TapPoint(TypedDict):
    """点击点

    x: 坐标 X
    y: 坐标 Y
    """

    x: int
    y: int


def setJitterValue(value: int):
    """设置动作抖动值（像素，随屏幕 scale 适配）

    参数:
      value: 抖动像素值
    返回:
      bool: 是否设置成功
    """
    pass


def click(x: int, y: int, duration: int = 20, jitter: bool = False) -> bool:
    """点击指定坐标

    参数:
      x: 坐标 X
      y: 坐标 Y
      duration: 按下持续时间（毫秒，默认 20ms）
      jitter: 是否启用抖动（默认 False）
    返回:
      bool: 是否点击成功
    """
    return True


def clickRandom(x1: int, y1: int, x2: int, y2: int, duration: int = 20) -> bool:
    """随机点击矩形区域

    参数:
      x1: 左上角 X
      y1: 左上角 Y
      x2: 右下角 X
      y2: 右下角 Y
      duration: 按下持续时间（毫秒，默认 20ms）
    返回:
      bool: 是否点击成功
    """
    return True


def doubleClick(
    x: int, y: int, duration: int = 20, interval: int = 20, jitter: bool = False
) -> bool:
    """双击

    参数:
      x: 坐标 X
      y: 坐标 Y
      duration: 每次按下持续时间（毫秒，默认 20ms）
      interval: 两次点击间隔（毫秒，默认 20ms）
      jitter: 是否启用抖动（默认 False）
    返回:
      bool: 是否双击成功
    """
    return True


def doubleClickRandom(
    x1: int, y1: int, x2: int, y2: int, duration: int = 20, interval: int = 20
) -> bool:
    """随机双击矩形区域

    参数:
      x1: 左上角 X
      y1: 左上角 Y
      x2: 右下角 X
      y2: 右下角 Y
      duration: 每次按下持续时间（毫秒，默认 20ms）
      interval: 两次点击间隔（毫秒，默认 20ms）
    返回:
      bool: 是否双击成功
    """
    return True


def swipe(
    startX: int,
    startY: int,
    endX: int,
    endY: int,
    duration: int = 100,
    jitter: bool = False,
    steps: int = 6,
) -> bool:
    """直线滑动

    参数:
      startX: 起始 X
      startY: 起始 Y
      endX: 结束 X
      endY: 结束 Y
      duration: 总时长（毫秒，默认 100ms）
      jitter: 是否启用抖动（默认 False）
      steps: 轨迹点数量（默认 6）
    返回:
      bool: 是否滑动成功
    """
    return True


def pressAndSwipe(
    startX: int,
    startY: int,
    endX: int,
    endY: int,
    touch_down_duration: int = 500,
    touch_move_duration: int = 1000,
    touch_up_duration: int = 500,
    jitter: bool = False,
    steps: int = 6,
) -> bool:
    """长按并滑动

    参数:
      touch_down_duration: 按下时长（毫秒，默认 500ms）
      touch_move_duration: 移动时长（毫秒，默认 1000ms）
      touch_up_duration: 抬起时长（毫秒，默认 500ms）
      jitter: 是否启用抖动（默认 False）
      steps: 轨迹点数量（默认 6）
      其他坐标与滑动参数同 swipe
    返回:
      bool: 是否执行成功
    """
    return True


def swipeCurve(
    startX: int,
    startY: int,
    midX: int,
    midY: int,
    endX: int,
    endY: int,
    duration: int = 1000,
) -> bool:
    """3点曲线滑动（先快后慢）

    参数:
      startX/startY: 起点坐标
      midX/midY: 中间控制点坐标
      endX/endY: 终点坐标
      duration: 总时长（毫秒，默认 1000ms）
    返回:
      bool: 是否执行成功
    """
    return True


def input(text: str) -> bool:
    """输入英文文本（不支持中文）

    参数:
      text: 文本内容
    返回:
      bool: 是否输入成功
    """
    return True


def backspace(count: int = 1) -> bool:
    """删除文本

    参数:
      count: 删除数量（默认 1）
    返回:
      bool: 是否删除成功
    """
    return True


def enter() -> bool:
    """回车

    返回:
      bool: 是否成功
    """
    return True


def homeScreen() -> bool:
    """回到主屏幕

    返回:
      bool: 是否成功
    """
    return True


def pressButton(button: Literal["home", "volumeup", "volumedown"]) -> bool:
    """按按钮（home/volumeup/volumedown 等）

    参数:
      button: 按钮名称
    返回:
      bool: 是否成功
    """
    return True


def pressHidButton(
    button: Literal["home", "volumeup", "volumedown", "power", "snapshot"],
    duration: int = 20,
) -> bool:
    """按 HID 按钮（power/snapshot 等），可指定时长

    参数:
      button: HID 按钮名称
      duration: 持续时间（毫秒，默认 20ms）
    返回:
      bool: 是否成功
    """
    return True


class ActionBuilder:
    def addPointer(self, id: int) -> Pointer:
        return Pointer(self, id)

    def singleTap(self, x: int, y: int, duration: int = 20) -> "ActionBuilder":
        return self

    def multiTap(self, points: List[TapPoint], duration: int = 20) -> "ActionBuilder":
        return self

    def execute(self) -> bool:
        return True


class Pointer:
    def __init__(self, builder: "ActionBuilder", id: int):
        self.builder = builder
        self.id = id

    def moveTo(self, x: int, y: int, duration: int = 20) -> "Pointer":
        return self

    def down(self) -> "Pointer":
        return self

    def up(self) -> "Pointer":
        return self

    def stay(self, duration: int = 20) -> "Pointer":
        return self

    def tap(self, x: int, y: int, duration: int = 20) -> "Pointer":
        return self

    def done(self) -> "ActionBuilder":
        return self.builder


def createBuilder() -> ActionBuilder:
    """创建 ActionBuilder 构建器

    返回:
      ActionBuilder: 链式构建器实例
    """
    return ActionBuilder()
