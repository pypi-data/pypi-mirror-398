from typing import Literal, TypedDict


class ScreenSize(TypedDict):
    """屏幕尺寸

    width: 宽度（逻辑尺寸）
    height: 高度（逻辑尺寸）
    """

    width: float
    height: float


class BatteryInfo(TypedDict):
    """电池信息

    level: 电池电量0-100
    isCharging: 是否充电
    """

    level: int
    isCharging: bool


# 获取电池信息
# 返回：{"level": 百分比int, "isCharging": 是否充电bool}
def getBatteryInfo() -> BatteryInfo:
    """获取电池信息（level/isCharging）"""
    return {"level": 0, "isCharging": False}


# 获取设备ID（Vendor ID）
def getDeviceID() -> str:
    """获取设备 ID（Vendor ID）"""
    return ""


# 获取服务器设备ID（自定义）
def getServerDeviceId() -> str:
    """获取服务器设备 ID（自定义）"""
    return ""


# 获取设备名称
def getDeviceName() -> str:
    """获取设备名称"""
    return ""


# 获取设备型号（硬件型号）
def getDeviceModel() -> str:
    """获取设备型号（硬件型号）"""
    return ""


# 获取屏幕逻辑尺寸
# 返回：{"width": float, "height": float}
def getScreenSize() -> ScreenSize:
    """获取屏幕逻辑尺寸（width/height）"""
    return {"width": 0.0, "height": 0.0}


# 获取屏幕实际尺寸
# 返回：{"width": float, "height": float}
def getScreenRealSize() -> ScreenSize:
    """获取屏幕实际尺寸（width/height）"""
    return {"width": 0.0, "height": 0.0}


# 获取屏幕缩放比例
def getScreenScale() -> float:
    """获取屏幕缩放比例"""
    return 1.0


# 获取屏幕方向
def getOrientation() -> Literal["PORTRAIT", "LANDSCAPE"]:
    """获取屏幕方向"""
    return "PORTRAIT"


# 获取系统版本
def getOSVersion() -> str:
    """获取系统版本（例如 16.7.11）"""
    return ""


# 获取局域网IP
def getLanIp() -> str:
    """获取局域网 IP（例如 192.168.1.100）"""
    return ""


# 震动
# 参数：duration 毫秒；intensity 0.0-1.0
def vibrate(duration: int, intensity: float) -> None:
    """震动

    参数:
      duration: 持续时间（毫秒）
      intensity: 强度 0.0-1.0
    返回:
      None
    """
    return None
