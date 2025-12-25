from typing import List, TypedDict


class VoiceInfo(TypedDict):
    """语音信息"""

    identifier: str  # 语音标识符
    name: str  # 语音名称
    language: str  # 语音语言（例如 "zh-CN"）
    quality: int  # 语音质量（0=低，1=中，2=高）


def speak(
    text: str,
    rate: float = 0.5,
    pitch: float = 1.0,
    volume: float = 1.0,
    language: str = "zh-CN",
) -> bool:
    """播放文本转语音

    参数默认值:
      rate: 0.5
      pitch: 1.0
      volume: 1.0
      language: "zh-CN"
    """
    return True


def waitEnd():
    """等待当前语音播放结束"""
    pass


def stop():
    """停止当前播放"""
    pass


def isSpeaking() -> bool:
    """是否正在播放"""
    return False


def getAvailableVoices() -> List[VoiceInfo]:
    """获取可用的语音列表"""
    return []


def setVoice(voiceIdentifier: str) -> bool:
    """设置语音（identifier）"""
    return True


def free():
    """释放 TTS 资源"""
    pass
