class LsyzwmRpcError(Exception):
    """RPC 调用异常"""

    def __init__(self, message: str, code: int = -1, data=None):
        """初始化 RPC 异常

        Args:
            message: 错误消息
            code: 错误代码
            data: 附加数据
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data

    def __str__(self):
        return f"[Code {self.code}] {self.message}"


class LsyzwmZooError(Exception):
    """ZooKeeper 操作异常"""

    def __init__(self, message: str, code: int = -1, data=None):
        """初始化 ZooKeeper 异常

        Args:
            message: 错误消息
            code: 错误代码
            data: 附加数据
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data

    def __str__(self):
        return f"[Code {self.code}] {self.message}"


class LsyzwmZooNodeExistsError(LsyzwmZooError):
    """ZooKeeper 节点已存在异常"""

    def __init__(self, message: str, data=None):
        """初始化节点已存在异常

        Args:
            message: 错误消息
            data: 附加数据
        """
        super().__init__(message=message, code=-2006, data=data)
