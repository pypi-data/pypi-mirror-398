from typing import Optional, TypedDict


class TomatoInitResult(TypedDict):
    """TomatoOCR 初始化结果"""

    deviceId: str  # 设备 ID
    expiryTime: str  # 有效期时间
    message: str  # 初始化消息
    status: str  # 状态
    versionName: str  # 版本名称


def initializeWithConfig(
    mode: str, licenseData: str, remark: str = ""
) -> Optional[TomatoInitResult]:
    """初始化 TomatoOCR 并设置基本配置

    参数默认值:
      remark: 空字符串
    """
    return None


def setHttpIntervalTime(second: float):
    """设置 HTTP 请求间隔时间（秒）"""
    pass


def setRecType(recType: str):
    """设置识别类型（如 ch-3.0/cht/japan 等）"""
    pass


def setDetBoxType(detBoxType: str):
    """设置检测框类型（rect/quad）"""
    pass


def setDetUnclipRatio(detUnclipRatio: float):
    """设置检测框展开比例（建议 1.6-2.5）"""
    pass


def setDetScaleRatio(detScaleRatio: float):
    """设置检测框缩放比例"""
    pass


def setRecScoreThreshold(recScoreThreshold: float):
    """设置识别分数阈值（默认 0.1）"""
    pass


def setReturnType(returnType: str):
    """设置返回类型（json/text/num/自定义字符集）"""
    pass


def setBinaryThresh(binaryThresh: float):
    """设置二值化阈值（0-255）"""
    return None


def setRunMode(runMode: str):
    """设置运行模式（如 fast）"""
    pass


def setFilterColor(filterColor: str, backgroundColor: str):
    """设置图像滤色参数（多色用 | 连接）"""
    pass


def ocrImage(
    input: str, type: int = 3, x: int = 0, y: int = 0, ex: int = 0, ey: int = 0
) -> str:
    """对图像执行 OCR 识别，返回 JSON 字符串

    参数默认值:
      type: 3（检测+识别）
      x/y/ex/ey: 0
    """
    return ""


def findTapPoint(data: str) -> str:
    """查找点击点（返回中心点 JSON 字符串）"""
    return ""


def findTapPoints(data: str) -> str:
    """查找多个点击点（返回中心点数组 JSON 字符串）"""
    return ""
