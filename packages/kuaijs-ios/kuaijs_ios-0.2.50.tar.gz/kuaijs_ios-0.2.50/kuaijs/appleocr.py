from typing import List, Optional, TypedDict


class OCRResult(TypedDict):
    """OCR 识别结果"""

    text: str  # 识别文本
    confidence: float  # 置信度（0-1）
    x: int  # 边界框左上角 x 坐标
    y: int  # 边界框左上角 y 坐标
    ex: int  # 边界框右下角 x 坐标
    ey: int  # 边界框右下角 y 坐标
    width: int  # 边界框宽度
    height: int  # 边界框高度
    centerX: int  # 边界框中心 x 坐标
    centerY: int  # 边界框中心 y 坐标


def recognize(
    input: str,
    x: int = 0,
    y: int = 0,
    ex: int = 0,
    ey: int = 0,
    languages: Optional[List[str]] = None,
) -> List[OCRResult]:
    """OCR 识别（Apple Vision）

    参数默认值:
      x/y/ex/ey: 0
      languages: ["zh-Hans", "en-US"]
    返回:
      List[OCRResult]: 文本、置信度与位置信息列表
    """
    return []


def recognizeNumbers(
    input: str,
    x: int = 0,
    y: int = 0,
    ex: int = 0,
    ey: int = 0,
) -> List[OCRResult]:
    """仅识别数字（过滤非数字，保留 0-9 . , - +）

    参数默认值:
      x/y/ex/ey: 0
    返回:
      同 recognize
    """
    return []


def findText(
    input: str,
    texts: List[str],
    x: int = 0,
    y: int = 0,
    ex: int = 0,
    ey: int = 0,
    languages: Optional[List[str]] = None,
) -> List[OCRResult]:
    """查找指定文本位置

    参数默认值:
      x/y/ex/ey: 0
      languages: ["zh-Hans", "en-US"]
    返回:
      List[OCRResult]: 匹配文本的位置信息列表
    """
    return []
