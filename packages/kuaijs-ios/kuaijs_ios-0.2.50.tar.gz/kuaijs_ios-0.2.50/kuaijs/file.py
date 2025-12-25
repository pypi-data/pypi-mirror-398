from typing import List, Optional, Literal


def getInternalDir(
    type: Literal["documents", "library", "temp", "libraryCaches"],
) -> str:
    """获取内部目录路径

    参数:
      type: 目录类型
    返回:
      str: 路径
    """
    return ""


def getDataDir() -> str:
    """获取应用数据目录路径"""
    return ""


def getDataFile(file: str) -> str:
    """获取应用数据文件路径"""
    return ""


def create(path: str) -> bool:
    """创建文件"""
    return True


def mkdirs(path: str) -> bool:
    """递归创建目录"""
    return True


def deleteAllFile(path: str) -> bool:
    """删除文件或目录（谨慎）"""
    return True


def readFile(path: str) -> Optional[str]:
    """读取文件内容（UTF-8）"""
    return None


def readResFile(fileName: str) -> Optional[str]:
    """读取资源文件内容（UTF-8）"""
    return None


def deleteLine(path: str, line: int, contains: Optional[str] = None) -> bool:
    """删除指定行或包含关键字的行

    参数:
      line: 行号（>=0 删除对应行；<0 时忽略行号）
      contains: 包含关键字（当行号<0时生效）
    """
    return True


def listDir(path: str, recursion: bool) -> List[str]:
    """列出目录文件"""
    return []


def writeFile(path: str, data: str) -> bool:
    """写入文件（覆盖，UTF-8）"""
    return True


def appendLine(path: str, data: str) -> bool:
    """追加一行（UTF-8）"""
    return True


def readLine(path: str, lineNo: int) -> Optional[str]:
    """读取指定行（0 基）"""
    return None


def readAllLines(path: str) -> Optional[List[str]]:
    """读取所有行"""
    return None


def exists(path: str) -> bool:
    """文件或目录是否存在"""
    return False


def copy(src: str, dest: str) -> bool:
    """复制文件"""
    return True


def fileMD5(path: str) -> Optional[str]:
    """计算文件 MD5（十六进制字符串）"""
    return None
