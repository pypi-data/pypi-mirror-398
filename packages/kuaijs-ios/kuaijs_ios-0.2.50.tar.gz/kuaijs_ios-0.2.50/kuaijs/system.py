from typing import Any, Dict, List, Optional, TypedDict


# 获取内存使用信息（单位：MB）
# 返回键：
# - used: 已使用内存
# - available: 可用内存
# - total: 系统总内存
# - usagePercentage: 使用率（0-100）
class MemoryInfo(Protocol):
    # 已使用内存（MB）
    used: int
    # 可用内存（MB）
    available: int
    # 系统总内存（MB）
    total: int
    # 使用率（0-100）
    usagePercentage: int


# 获取当前运行的应用信息（可能为 None）
class ProcessArguments(Protocol):
    # 环境变量映射（键为字符串，值为任意类型）
    env: Dict[str, Any]
    # 启动参数列表
    args: List[str]


class ActivateAppInfo(Protocol):
    # 应用名称
    name: str
    # 进程 ID
    pid: int
    # 应用 Bundle ID
    bundleId: str
    # 启动参数信息
    processArguments: ProcessArguments


# 设置 Agent 参数
# 参数：
# - params: 支持的键：
#   - mjpegServerScreenshotQuality: int 截图质量（MJPEG）
#   - mjpegServerFramerate: int MJPEG 帧率
#   - screenshotQuality: int 普通截图质量
class AgentSettings(TypedDict):
    # MJPEG 截图质量
    mjpegServerScreenshotQuality: Optional[int]
    # MJPEG 帧率
    mjpegServerFramerate: Optional[int]
    # 普通截图质量
    screenshotQuality: Optional[int]


def startApp(bundle_id: str, args: List[str] = [], env: Dict[str, Any] = {}) -> bool:
    """启动应用

    参数:
      bundle_id: 应用 Bundle ID
      args: 启动参数列表
      env: 环境变量映射
    返回:
      bool: 是否启动成功
    """
    return True


def stopApp(bundle_id: str) -> bool:
    """停止应用"""
    return True


def activateApp(bundle_id: str) -> bool:
    """激活应用到前台（未启动则启动）"""
    return True


def activateAppInfo() -> Optional[ActivateAppInfo]:
    """获取当前运行的应用信息（可能为 None）"""
    return None


def openURL(url: str) -> bool:
    """使用系统浏览器打开 URL"""
    return True


def notify(msg: str, title: str = "", id: str = ""):
    """发送系统通知（后台生效）"""
    pass


def setClipboard(text: str) -> bool:
    """设置剪贴板文本（仅前台有效）"""
    return True


def getClipboard() -> str:
    """获取剪贴板文本（仅前台有效）"""
    return ""


def isLocked() -> bool:
    """是否锁屏"""
    return False


def lock() -> bool:
    """锁屏"""
    return True


def unlock() -> bool:
    """解锁"""
    return True


def getMemoryInfo() -> MemoryInfo:
    """获取内存使用信息（MB）：used/available/total/usagePercentage"""
    return {"used": 0, "available": 0, "total": 0, "usagePercentage": 0}


def getUsedMemory() -> int:
    """获取已使用内存（MB）"""
    return 0


def getAvailableMemory() -> int:
    """获取可用内存（MB）"""
    return 0


def getTotalMemory() -> int:
    """获取系统总内存（MB）"""
    return 0


def startAgent() -> bool:
    """启动 Agent 服务"""
    return True


def getAgentStatus() -> bool:
    """获取 Agent 状态（是否正在运行）"""
    return True


def setAgentSettings(params: Optional[AgentSettings] = None) -> bool:
    """设置 Agent 参数（质量/帧率/截图质量）"""
    return True
