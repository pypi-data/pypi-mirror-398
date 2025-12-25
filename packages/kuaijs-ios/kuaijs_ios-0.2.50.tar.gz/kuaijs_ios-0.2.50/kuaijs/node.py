from typing import Any, Dict, List, Optional, Union, TypedDict


class SelectorParams(TypedDict, total=False):
    """节点选择器参数"""

    maxDepth: Optional[int]  # 最大层级深度默认 50


class NodeBounds:
    """节点边界"""

    x: int
    y: int
    width: int
    height: int
    centerX: int
    centerY: int

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
        centerX: int = 0,
        centerY: int = 0,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.centerX = centerX
        self.centerY = centerY


class NodeInfo:
    id: str = ""  # 节点 ID
    identifier: str = ""  # 节点标识符
    label: str = ""  # 节点标签
    type: str = ""  # 节点类型
    value: str = ""  # 节点值
    title: str = ""  # 节点标题
    visible: bool = False  # 是否可见
    enabled: bool = False  # 是否启用
    accessible: bool = False  # 是否可访问
    bounds: NodeBounds = NodeBounds()
    depth: int = 0  # 节点层级深度
    index: int = 0  # 节点索引
    parentId: str = ""  # 父节点 ID
    childCount: int = 0  # 子节点数量

    def clickCenter(self) -> bool:
        return True

    def clickRandom(self) -> bool:
        return True

    def parent(self) -> Optional["NodeInfo"]:
        return None

    def child(self, index: int) -> Optional["NodeInfo"]:
        return None

    def allChildren(self) -> List["NodeInfo"]:
        return []

    def siblings(self) -> List["NodeInfo"]:
        return []

    def previousSiblings(self) -> List["NodeInfo"]:
        return []

    def nextSiblings(self) -> List["NodeInfo"]:
        return []

    def toJSON(self) -> Dict[str, Any]:
        return {}


class NodeSelector:
    """节点选择器"""

    def __init__(self, params: Optional[SelectorParams] = None):
        self.params = params or {"maxDepth": 50}

    def clearSelector(self) -> "NodeSelector":
        return self

    def loadNode(self, timeout: int = 5000) -> "NodeSelector":
        return self

    def xml(self, timeout: int = 5000) -> Optional[str]:
        return None

    def getNodeInfo(self, timeout: int = 5000) -> List[NodeInfo]:
        return []

    def getOneNodeInfo(self, timeout: int = 5000) -> Optional[NodeInfo]:
        return None

    def xpath(self, path: str) -> "NodeSelector":
        return self

    def label(self, label: str) -> "NodeSelector":
        return self

    def labelMatch(self, match: str) -> "NodeSelector":
        return self

    def title(self, title: str) -> "NodeSelector":
        return self

    def titleMatch(self, match: str) -> "NodeSelector":
        return self

    def identifier(self, identifier: str) -> "NodeSelector":
        return self

    def identifierMatch(self, match: str) -> "NodeSelector":
        return self

    def type(self, type_title: str) -> "NodeSelector":
        return self

    def typeMatch(self, match: str) -> "NodeSelector":
        return self

    def value(self, value: str) -> "NodeSelector":
        return self

    def valueMatch(self, match: str) -> "NodeSelector":
        return self

    def enabled(self, flag: bool) -> "NodeSelector":
        return self

    def accessible(self, flag: bool) -> "NodeSelector":
        return self

    def visible(self, flag: bool) -> "NodeSelector":
        return self

    def index(self, idx: int) -> "NodeSelector":
        return self

    def depth(self, d: int) -> "NodeSelector":
        return self

    def childCount(self, childCount: Union[int, str]) -> "NodeSelector":
        return self

    def bounds(self, x: int, y: int, width: int, height: int) -> "NodeSelector":
        return self

    def x(self, x: Union[int, str]) -> "NodeSelector":
        return self

    def y(self, y: Union[int, str]) -> "NodeSelector":
        return self

    def width(self, width: Union[int, str]) -> "NodeSelector":
        return self

    def height(self, height: Union[int, str]) -> "NodeSelector":
        return self


def createNodeSelector(params: Optional[SelectorParams] = None) -> NodeSelector:
    """创建节点选择器

    参数:
      params: maxDepth 最大层级深度默认 50
    返回:
      NodeSelector: 链式选择器
    """
    return NodeSelector(params)
