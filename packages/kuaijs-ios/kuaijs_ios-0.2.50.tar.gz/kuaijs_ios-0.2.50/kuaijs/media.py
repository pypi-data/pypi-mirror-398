"""媒体管理：相册与音频"""


# 保存图片/视频到相册
def saveImageToAlbum(imageId: str) -> bool:
    """保存图像到相册"""
    return True


def saveVideoToAlbumPath(path: str) -> bool:
    """保存视频路径到相册"""
    return True


# 清空相册图片/视频
def deleteAllPhotos() -> bool:
    """清空相册中的图片"""
    return True


def deleteAllVideos() -> bool:
    """清空相册中的视频"""
    return True


# 播放/停止MP3；同步播放（等待结束）
def playMp3(path: str, loop: bool) -> bool:
    """播放 MP3（异步）"""
    return True


def stopMp3() -> bool:
    """停止播放 MP3"""
    return True


def playMp3WaitEnd(path: str, loop: bool) -> bool:
    """同步播放 MP3（等待结束）"""
    return True


def isMp3Playing() -> bool:
    """是否正在播放 MP3"""
    return False
