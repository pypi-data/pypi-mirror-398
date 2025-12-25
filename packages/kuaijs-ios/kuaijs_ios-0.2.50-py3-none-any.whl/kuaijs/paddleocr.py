from typing import List, TypedDict


class OCRResult(TypedDict):
    """OCR 识别结果"""

    text: str  # 识别文本
    confidence: float  # 置信度（0-1）
    x: int  # 左边界
    y: int  # 上边界
    ex: int  # 右边界
    ey: int  # 下边界
    width: int  # 宽度
    height: int  # 高度
    centerX: int  # 中心 X 坐标
    centerY: int  # 中心 Y 坐标
    angle: float  # 旋转角度（顺时针）
    orientation: int  # 方向（0=水平，1=垂直）


def loadV5(maxSideLen: int = 640) -> bool:
    """加载 PP-OCRv5 模型（maxSideLen 默认 640）"""
    return True


def recognize(
    input: str,
    x: int = 0,
    y: int = 0,
    ex: int = 0,
    ey: int = 0,
    confidenceThreshold: float = 0.6,
) -> List[OCRResult]:
    """执行 OCR 识别（返回 OCRResult 列表）

    参数默认值:
      x/y/ex/ey: 0（全屏）
      confidenceThreshold: 0.6
    """
    return []


def free():
    """释放模型资源"""
    pass
