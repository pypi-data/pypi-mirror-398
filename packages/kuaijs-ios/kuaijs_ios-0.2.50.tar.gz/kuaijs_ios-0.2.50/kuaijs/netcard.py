from typing import Optional, TypedDict


class CardInfo(TypedDict):
    """卡密信息"""

    cardNo: str  # 卡号
    batchCard: str  # 批量码
    remark: str  # 备注
    activeTime: str  # 激活时间yyyy-MM-dd HH:mm:ss
    expireTime: str  # 过期时间yyyy-MM-dd HH:mm:ss


def verify(cardNo: str) -> bool:
    """验证卡密"""
    return True


def getCardInfo() -> Optional[CardInfo]:
    """获取卡密信息（验证通过后可用）"""
    return None


def setCardRemark(remark: str) -> bool:
    """设置卡密备注"""
    return True


def setValue(key: str, value: str) -> str:
    """设置值（成功返回设置的 value）"""
    return value


def getValue(key: str) -> str:
    """获取值（失败返回空字符串）"""
    return ""
