from typing import Optional, TypedDict


class HotUpdateOptions(TypedDict, total=False):
    """热更新检查参数"""

    url: Optional[str]  # 热更新检查 URL
    version: Optional[int]  # 当前应用版本号
    timeout: Optional[int]  # 超时时间（秒）


class HotUpdateResult(TypedDict):
    """热更新检查结果"""

    needUpdate: bool  # 是否需要更新
    error: Optional[str]  # 错误信息
    data: Optional[HotUpdateResponse]  # 热更新响应数据


class HotUpdateResponse(TypedDict):
    """热更新响应数据"""

    download_url: str  # 下载 URL
    version: int  # 最新版本号
    download_timeout: int  # 下载超时时间（秒）
    dialog: bool  # 是否显示弹窗提示
    msg: str  # 弹窗提示消息
    force: bool  # 是否强制更新
    md5: Optional[str]  # 最新版本文件的 MD5 校验值


class InstallResult(TypedDict):
    """安装结果"""

    updated: bool  # 是否成功更新
    error: Optional[str]  # 错误信息


def checkUpdate(options: Optional[HotUpdateOptions] = None) -> HotUpdateResult:
    """检查更新

    参数:
      options: 检查参数（url/version/timeout）
    返回:
      HotUpdateResult: needUpdate/data/error
    """
    return {"needUpdate": False, "error": None, "data": None}


def downloadAndInstall() -> InstallResult:
    """下载并安装更新（执行成功会自动重启脚本）"""
    return {"updated": False, "error": None}


def getCurrentVersion() -> int:
    """获取当前应用版本号（数字）"""
    return 0
