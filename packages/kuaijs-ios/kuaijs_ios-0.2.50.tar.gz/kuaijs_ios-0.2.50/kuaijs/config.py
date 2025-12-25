from typing import Any, Dict, Optional
from typing_extensions import deprecated


def all() -> Dict[str, Any]:
    """获取所有配置

    返回:
      Dict[str, Any]: 配置映射

    示例:
      from kuaijs import config
      cfg = config.all()
    """
    return {}


def set(key: str, value: Any) -> bool:
    """设置配置值

    参数:
      key: 配置键
      value: 配置值
    返回:
      bool: 是否设置成功

    示例:
      from kuaijs import config
      ok = config.set("maxRetries", 5)
    """
    return True


def get(key: str) -> Any | None:
    """获取配置值

    参数:
      key: 配置键
    返回:
      Any | None: 配置值

    示例:
      from kuaijs import config
      v = config.get("maxRetries")
    """
    return None


def remove(key: str) -> bool:
    """删除配置值

    参数:
      key: 配置键
    返回:
      bool: 是否删除成功

    示例:
      from kuaijs import config
      ok = config.remove("tempKey")
    """
    return True


@deprecated("Use config.get(key) instead")
def readConfigInt(key: str) -> int:
    """读取整数配置（已废弃，请使用 config.get(key) 替代）

    参数:
      key: 配置键
    返回:
      int: 配置值

    示例:
      from kuaijs import config
      v = config.readConfigInt("maxRetries")
    """
    return 0


@deprecated("Use config.get(key) instead")
def readConfigDouble(key: str) -> float:
    """读取浮点配置（已废弃，请使用 config.get(key) 替代）"""
    return 0.0


@deprecated("Use config.get(key) instead")
def readConfigString(key: str) -> Optional[str]:
    """读取字符串配置（已废弃，请使用 config.get(key) 替代）"""
    return None


@deprecated("Use config.get(key) instead")
def readConfigBool(key: str) -> bool:
    """读取布尔配置（已废弃，请使用 config.get(key) 替代）"""
    return False


@deprecated("Use config.all() instead")
def getConfigJSON() -> Dict[str, Any]:
    """获取所有配置 JSON（已废弃，请使用 config.all() 替代）"""
    return {}


@deprecated("Use config.set(key, value) instead")
def updateConfig(key: str, value: Any) -> bool:
    """更新配置值（已废弃，请使用 config.set(key, value) 替代）"""
    return True


@deprecated("Use config.remove(key) instead")
def deleteConfig(key: str) -> bool:
    """删除配置（已废弃，请使用 config.remove(key) 替代）"""
    return True
