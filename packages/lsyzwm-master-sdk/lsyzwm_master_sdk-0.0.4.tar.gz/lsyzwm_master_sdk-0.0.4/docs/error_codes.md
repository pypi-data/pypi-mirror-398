# 错误代码参考文档

本文档列出了 lsyzwm_master_sdk 中所有异常类的错误代码及其说明。

## 目录

- [LsyzwmRpcError - RPC 调用异常](#lsyzwmrpcerror---rpc-调用异常)
- [LsyzwmZooError - ZooKeeper 操作异常](#lsyzwmzooerror---zookeeper-操作异常)

---

## LsyzwmRpcError - RPC 调用异常

**错误码范围**: `-1000` ~ `-1999`

用于 `MasterRpcClient` 类中的 RPC 调用相关异常。

### 协议和连接错误

| 错误码 | 说明 | 触发场景 |
|-------|------|---------|
| -1000 | RPC 协议错误 | HTTP 协议错误，如 404、500 等状态码 |
| -1001 | RPC 连接失败 | 无法连接到服务器（连接被拒绝、远程断开、socket 错误）|
| -1002 | RPC 连接超时 | 连接或请求超时 |
| -1003 | RPC 响应解析失败 | 服务端返回的不是有效的 JSON 格式 |

### 其他错误

| 错误码 | 说明 | 触发场景 |
|-------|------|---------|
| -1999 | RPC 调用异常 | 其他未预期的错误 |
| 其他正整数 | XMLRPC 服务端错误 | 服务端返回的 Fault 错误码 |

### 业务逻辑错误

| 错误码 | 说明 | 触发场景 |
|-------|------|---------|
| 200 | 成功 | 操作成功完成 |
| 400 | 参数错误 | 请求参数验证失败 |
| -1 | 业务失败 | 通用业务逻辑错误 |

### 使用示例

```python
from lsyzwm_master_sdk.rpc_client import MasterRpcClient
from lsyzwm_master_sdk.exceptions import LsyzwmRpcError

client = MasterRpcClient("http://localhost:9020")

try:
    result = client.add_worker_task("task_001", "my_worker", {"data": "value"})
    print("成功:", result)
except LsyzwmRpcError as e:
    if e.code == -1001:
        print(f"连接失败: {e.message}")
        print(f"服务器地址: {e.data.get('url')}")
    elif e.code == -1000:
        print(f"协议错误: {e.message}")
        print(f"HTTP 错误码: {e.data.get('errcode')}")
    elif e.code == -1002:
        print(f"连接超时: {e.message}")
    elif e.code == -1003:
        print(f"响应解析失败: {e.message}")
    elif e.code == 400:
        print(f"参数错误: {e.message}")
    else:
        print(f"其他错误 [{e.code}]: {e.message}")
```

---

## LsyzwmZooError - ZooKeeper 操作异常

**错误码范围**: `-2001` ~ `-2099`

用于 `MasterZooClient` 类中的 ZooKeeper 操作相关异常。

### 连接管理错误

| 错误码 | 说明 | 触发场景 |
|-------|------|---------|
| -2001 | ZooKeeper 连接失败 | 启动连接时失败，无法连接到 ZooKeeper 服务器 |
| -2002 | ZooKeeper 未连接 | 尝试操作时发现客户端未连接 |

### 节点操作错误

| 错误码 | 说明 | 触发场景 |
|-------|------|---------|
| -2003 | 节点数据解码失败 | 节点数据无法解码为 UTF-8 字符串 |
| -2004 | 获取节点值失败 | 获取节点数据时发生错误 |
| -2005 | 设置节点值失败 | 设置或更新节点数据时发生错误 |
| -2006 | 节点已存在 | 尝试创建已存在的节点 |
| -2007 | 创建节点失败 | 创建节点时发生错误 |
| -2008 | 节点非空，无法删除 | 尝试非递归删除非空节点 |
| -2009 | 删除节点失败 | 删除节点时发生错误 |
| -2010 | 获取子节点失败 | 获取子节点列表时发生错误 |

### 数据解析错误

| 错误码 | 说明 | 触发场景 |
|-------|------|---------|
| -2011 | 任务 JSON 解析失败 | worker 任务数据 JSON 解析失败 |
| -2012 | 缓存 JSON 解析失败 | worker 缓存数据 JSON 解析失败 |
| -2013 | 实例缓存 JSON 解析失败 | worker 实例缓存数据 JSON 解析失败 |

### 使用示例

```python
from lsyzwm_master_sdk.zoo_client import MasterZooClient
from lsyzwm_master_sdk.exceptions import LsyzwmZooError

try:
    with MasterZooClient("localhost:2181") as client:
        # 添加任务
        client.add_task_node("my_worker", "task_001", {"data": "value"}, worker_sid=1)
        
        # 获取任务
        task = client.get_worker_instance_task("my_worker", 1, "task_001")
        print("任务数据:", task)
        
except LsyzwmZooError as e:
    if e.code == -2001:
        print(f"连接失败: {e.message}")
        print(f"ZooKeeper 地址: {e.data.get('hosts')}")
    elif e.code == -2002:
        print(f"未连接: {e.message}")
    elif e.code == -2003:
        print(f"数据解码失败: {e.message}")
    elif e.code == -2006:
        print(f"节点已存在: {e.message}")
        print(f"节点路径: {e.data.get('path')}")
    elif e.code == -2008:
        print(f"节点非空: {e.message}")
    elif e.code in [-2011, -2012, -2013]:
        print(f"JSON 解析失败: {e.message}")
    else:
        print(f"其他错误 [{e.code}]: {e.message}")
```

---

## 异常类属性

所有异常类都包含以下属性：

### 属性说明

| 属性 | 类型 | 说明 |
|-----|------|------|
| `message` | `str` | 错误消息描述 |
| `code` | `int` | 错误代码 |
| `data` | `Any` | 附加数据（可选），通常是字典，包含错误的详细信息 |

### 字符串表示

```python
try:
    # 某些操作
    pass
except (LsyzwmRpcError, LsyzwmZooError) as e:
    # 直接打印异常会显示: [Code 错误码] 错误消息
    print(e)  # 例如: [Code -2001] ZooKeeper 连接失败: Connection refused
    
    # 访问具体属性
    print(f"错误码: {e.code}")
    print(f"消息: {e.message}")
    print(f"详情: {e.data}")
```

---

## 错误处理最佳实践

### 1. 分层异常处理

```python
from lsyzwm_master_sdk.rpc_client import MasterRpcClient
from lsyzwm_master_sdk.zoo_client import MasterZooClient
from lsyzwm_master_sdk.exceptions import LsyzwmRpcError, LsyzwmZooError

def handle_rpc_operation():
    """处理 RPC 操作"""
    client = MasterRpcClient("http://localhost:9020")
    try:
        return client.add_worker_task("task_001", "worker", {"data": "test"})
    except LsyzwmRpcError as e:
        # 处理 RPC 特定错误
        if e.code == -1001:
            # 连接失败，可能需要重试或告警
            raise ConnectionError(f"RPC 服务不可用: {e.message}")
        raise

def handle_zk_operation():
    """处理 ZooKeeper 操作"""
    try:
        with MasterZooClient("localhost:2181") as client:
            return client.get_worker_instance_task("worker", 1, "task_001")
    except LsyzwmZooError as e:
        # 处理 ZooKeeper 特定错误
        if e.code == -2001:
            # ZK 连接失败
            raise ConnectionError(f"ZooKeeper 服务不可用: {e.message}")
        raise
```

### 2. 统一错误处理

```python
def unified_error_handler(func):
    """统一错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (LsyzwmRpcError, LsyzwmZooError) as e:
            # 记录错误日志
            logger.error(f"操作失败: {e}", extra={
                "error_code": e.code,
                "error_data": e.data
            })
            
            # 根据错误码进行特定处理
            if e.code in [-1001, -2001]:  # 连接错误
                # 触发告警
                alert_system.send_alert(f"服务连接失败: {e.message}")
            
            raise
    return wrapper

@unified_error_handler
def my_operation():
    # 执行操作
    pass
```

### 3. 错误重试机制

```python
import time
from typing import Callable, Any

def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """连接错误时重试装饰器"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (LsyzwmRpcError, LsyzwmZooError) as e:
                    # 只重试连接相关错误
                    if e.code in [-1001, -1002, -2001]:
                        last_exception = e
                        if attempt < max_retries - 1:
                            time.sleep(delay * (attempt + 1))
                            continue
                    raise
            raise last_exception
        return wrapper
    return decorator

@retry_on_connection_error(max_retries=3, delay=2.0)
def reliable_rpc_call():
    client = MasterRpcClient("http://localhost:9020")
    return client.add_worker_task("task_001", "worker", {"data": "test"})
```

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|-----|------|---------|
| 1.0.0 | 2025-11-27 | 初始版本，定义 RPC 和 ZooKeeper 错误码 |

---

## 相关文档

- [API 参考文档](./api_reference.md)
- [快速开始指南](./quick_start.md)
- [使用示例](./examples.md)
