from typing import List, Optional, TypedDict


class YoloResult(TypedDict):
    """YOLO 目标检测结果"""

    x: int  # 左边界
    y: int  # 上边界
    ex: int  # 右边界
    ey: int  # 下边界
    centerX: int  # 中心 X 坐标
    centerY: int  # 中心 Y 坐标
    width: int  # 宽度
    height: int  # 高度
    confidence: float  # 置信度（0-1）
    classId: int  # 类别 ID


def loadV11(paramPath: str, binPath: str, nc: int) -> Optional[str]:
    """加载 YOLOv11 模型，返回模型ID（失败返回 None）"""
    return None


def detect(
    modelId: str,
    img: str,
    targetSize: int = 640,
    threshold: float = 0.4,
    nmsThreshold: float = 0.5,
) -> List[YoloResult]:
    """目标检测（返回边框/置信度/类别等）

    参数默认值:
      targetSize: 640
      threshold: 0.4
      nmsThreshold: 0.5
    """
    return []


def free(modelId: str):
    """释放指定模型资源"""
    pass


def freeAll():
    """释放所有模型资源"""
    pass
