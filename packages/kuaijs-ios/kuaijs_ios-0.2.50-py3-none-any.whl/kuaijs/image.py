from typing import List, Optional, TypedDict


class Size(TypedDict):
    """图片尺寸信息

    width: 宽度
    height: 高度
    """

    width: int  # 宽度
    height: int  # 高度


class Point(TypedDict):
    """点坐标信息

    x: X 坐标
    y: Y 坐标
    """

    x: int  # X 坐标
    y: int  # Y 坐标


class Rect(TypedDict):
    """矩形区域信息

    index: 模版索引
    x: 矩形左上角 X 坐标
    y: 矩形左上角 Y 坐标
    width: 矩形宽度
    height: 矩形高度
    confidence: 匹配度（0-1）
    centerX: 矩形中心 X 坐标
    centerY: 矩形中心 Y 坐标
    ex: 矩形右下角 X 坐标
    ey: 矩形右下角 Y 坐标
    """

    index: int  # 模版索引
    x: int  # 矩形左上角 X 坐标
    y: int  # 矩形左上角 Y 坐标
    width: int  # 矩形宽度
    height: int  # 矩形高度
    confidence: float  # 匹配度（0-1）
    centerX: int  # 矩形中心 X 坐标
    centerY: int  # 矩形中心 Y 坐标
    ex: int  # 矩形右下角 X 坐标
    ey: int  # 矩形右下角 Y 坐标


def captureFullScreen() -> Optional[str]:
    """截取全屏并返回图片ID（失败返回 None）"""
    return None


def captureRect(x: int, y: int, ex: int, ey: int) -> Optional[str]:
    """截取屏幕区域并返回图片ID（x/y 左上角；ex/ey 右下角）"""
    return None


def captureFullScreenPIL() -> Optional[object]:
    """截取全屏并返回 PIL 图片对象（失败返回 None）"""
    return None


def readImage(path: str) -> Optional[str]:
    """读取图片文件为图片ID"""
    return None


def clip(id: str, x: int, y: int, ex: int, ey: int) -> Optional[str]:
    """裁剪图片并返回新的图片ID"""
    return None


def getSize(id: str) -> Optional[Size]:
    """获取图片尺寸信息 {width,height}"""
    return None


def toBase64Format(id: str, format: str, q: int) -> Optional[str]:
    """图片转 base64（format: jpg|png；q: 质量1-100，仅jpg）"""
    return None


def base64ToImage(base64data: str) -> Optional[str]:
    """base64 转图片ID"""
    return None


def isRelease(id: str) -> bool:
    """图片是否已被释放"""
    return False


def release(id: str):
    """释放图片"""
    pass


def releaseAll():
    """释放全部图片"""
    pass


def saveTo(id: str, path: str) -> bool:
    """保存图片到路径"""
    return True


def rotateImage(id: str, degree: int) -> Optional[str]:
    """旋转图片（degree: 90 | -90 | 180），返回新ID"""
    return None


def cmpColor(id: str, points: str, threshold: float) -> bool:
    """多点比色

    参数:
      points: "x|y|主色-偏色,..."
      threshold: 0.0-1.0
    返回:
      bool: 是否相同
    """
    return False


def findColor(
    id: str,
    color: str,
    threshold: float,
    x: int,
    y: int,
    ex: int,
    ey: int,
    limit: int,
    orz: int,
) -> List[Point]:
    """单点找色（返回点坐标列表）"""
    return []


def findMultiColor(
    id: str,
    firstColor: str,
    threshold: float,
    points: str,
    x: int,
    y: int,
    ex: int,
    ey: int,
    limit: int,
    orz: int,
) -> List[Point]:
    """多点找色（返回点坐标列表）"""
    return []


def countColor(
    id: str,
    colors: str,
    threshold: float,
    x: int,
    y: int,
    ex: int,
    ey: int,
) -> int:
    """统计颜色数量

    参数:
      colors: 多色列表，格式 "主色-偏色|主色-偏色|..."
      threshold: 0.0-1.0
      x/y/ex/ey: 统计区域
    返回:
      int: 命中像素数量
    """
    return 0


def findImage(
    id: str,
    templateImageId: str,
    x: int,
    y: int,
    ex: int,
    ey: int,
    threshold: float,
    limit: int,
    method: int,
    rgb: bool = False,
) -> List[Rect]:
    """找图（返回矩形列表）

    参数默认值:
      rgb: False
    """
    return []


def pixel(id: str, x: int, y: int) -> int:
    """获取像素颜色（整数 RGB）"""
    return 0


def argb(color: int) -> str:
    """颜色值转 16 进制字符串（#RRGGBB）"""
    return "#000000"


def binaryzation(id: str, threshold: float) -> Optional[str]:
    """二值化图片（返回新ID）"""
    return None


def gray(id: str) -> Optional[str]:
    """灰度化图片（返回新ID）"""
    return None


def scanCode(id: str) -> Optional[str]:
    """扫描条码/二维码（返回识别文本）"""
    return None


def drawRect(id: str, x: int, y: int, ex: int, ey: int, color: str, thickness: int):
    """在图片上绘制矩形（直接修改原图）"""
    pass
