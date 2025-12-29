import json
import random
from typing import Dict, Optional, Union, List, Callable

from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
from kazoo.exceptions import NoNodeError, NodeExistsError, NotEmptyError
from kazoo.recipe.watchers import ChildrenWatch

from .exceptions import LsyzwmZooError, LsyzwmZooNodeExistsError


class MasterZooClient:
    """Master ZooKeeper Client SDK - 方便上层服务操作 ZooKeeper"""

    # 配置常量
    DEFAULT_TIMEOUT = 10.0  # 会话超时(秒)

    # ZooKeeper 路径常量
    WORKERS_PATH = "/lsyzwm/workers"
    TASKS_PATH = "/lsyzwm/tasks"
    CACHES_PATH = "/lsyzwm/caches"
    DELAY_JOBS_PATH = "/lsyzwm/delay_jobs"

    def __init__(self, zk_hosts: str, timeout: float = None, connection_listener=None):
        """初始化 Master ZooKeeper 客户端

        Args:
            zk_hosts: ZooKeeper 服务器地址列表，逗号分隔，例如 'localhost:2181'
            timeout: 会话超时时间（秒），默认 10.0
            connection_listener: 自定义连接状态监听器函数，接收一个 state 参数（可选）
        """
        self.hosts = zk_hosts
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.zk: Optional[KazooClient] = None
        self._connection_listener_added = False
        self._custom_connection_listener = connection_listener

    def _connection_listener(self, state):
        """连接状态监听器"""
        if self._custom_connection_listener:
            self._custom_connection_listener(state)

    def start(self) -> None:
        """启动 ZooKeeper 连接

        Raises:
            LsyzwmZooError: 当连接失败时
        """
        try:
            self.zk = KazooClient(
                hosts=self.hosts,
                timeout=self.timeout,
                connection_retry={"max_tries": -1},  # 无限重试
            )
            if not self._connection_listener_added:
                self.zk.add_listener(self._connection_listener)
                self._connection_listener_added = True
            self.zk.start()
        except Exception as e:
            raise LsyzwmZooError(message=f"ZooKeeper 连接失败: {str(e)}", code=-2001, data={"hosts": self.hosts, "error": str(e)})

    def stop(self) -> None:
        """停止 ZooKeeper 连接"""
        if self.zk:
            self.zk.stop()
            self.zk.close()
            self.zk = None

    def is_connected(self) -> bool:
        """检查 ZooKeeper 连接状态

        Returns:
            True 如果已连接，否则 False
        """
        return self.zk is not None and self.zk.connected

    def _ensure_connected(self):
        """确保 ZooKeeper 已连接

        Raises:
            LsyzwmZooError: 当未连接时
        """
        if not self.is_connected():
            raise LsyzwmZooError(message="ZooKeeper 未连接", code=-2002, data=None)

    def _get_node_value(self, node_path: str) -> Optional[str]:
        """获取 ZooKeeper 节点的值（私有方法）

        Args:
            node_path: 节点路径

        Returns:
            节点值(UTF-8字符串)，如果节点不存在则返回 None

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        self._ensure_connected()
        try:
            data, stat = self.zk.get(node_path)
            if not data:
                return None

            if isinstance(data, bytes):
                return data.decode("utf-8")
            return data
        except NoNodeError:
            return None
        except UnicodeDecodeError as e:
            raise LsyzwmZooError(message=f"节点数据解码失败: {node_path}", code=-2003, data={"path": node_path, "error": str(e)})
        except Exception as e:
            raise LsyzwmZooError(message=f"获取节点值失败: {node_path} - {str(e)}", code=-2004, data={"path": node_path, "error": str(e)})

    def _set_node_value(self, node_path: str, payload: Optional[Union[str, Dict]] = None) -> None:
        """设置 ZooKeeper 节点值（不存在则创建，存在则更新）（私有方法）

        Args:
            node_path: 节点路径
            payload: 节点数据（字符串或字典，可以为 None）

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        self._ensure_connected()
        try:
            # 处理数据类型转换
            if payload is None:
                data = b""
            elif isinstance(payload, str):
                data = payload.encode("utf-8")
            elif isinstance(payload, dict):
                data = json.dumps(payload).encode("utf-8")
            else:
                raise TypeError(f"payload 类型不正确，期望 str、dict 或 None，实际为 {type(payload).__name__}")

            # 检查节点是否存在
            if self.zk.exists(node_path):
                self.zk.set(node_path, data)
            else:
                self.zk.create(node_path, value=data, makepath=True)
        except Exception as e:
            raise LsyzwmZooError(message=f"设置节点值失败: {node_path} - {str(e)}", code=-2005, data={"path": node_path, "error": str(e)})

    def _create_node(self, node_path: str, payload: Optional[Union[str, Dict]] = None, ephemeral: bool = False) -> None:
        """创建 ZooKeeper 节点（私有方法）

        Args:
            node_path: 节点路径
            payload: 节点数据（字符串或字典，可以为 None）
            ephemeral: 是否创建临时节点，默认 False

        Raises:
            LsyzwmZooError: 当节点已存在或创建失败时
        """
        self._ensure_connected()
        try:
            if payload is None:
                data = b""
            elif isinstance(payload, str):
                data = payload.encode("utf-8")
            elif isinstance(payload, dict):
                data = json.dumps(payload).encode("utf-8")
            else:
                raise TypeError(f"payload 类型不正确，期望 str、dict 或 None，实际为 {type(payload).__name__}")

            self.zk.create(node_path, value=data, ephemeral=ephemeral, makepath=True)
        except NodeExistsError:
            raise LsyzwmZooNodeExistsError(message=f"节点已存在: {node_path}", data={"path": node_path})
        except Exception as e:
            raise LsyzwmZooError(message=f"创建节点失败: {node_path} - {str(e)}", code=-2007, data={"path": node_path, "error": str(e)})

    def _delete_node(self, node_path: str, recursive: bool = True) -> None:
        """删除 ZooKeeper 节点（私有方法）

        Args:
            node_path: 节点路径
            recursive: 是否递归删除子节点，默认 True

        Raises:
            LsyzwmZooError: 当删除失败时
        """
        self._ensure_connected()
        try:
            self.zk.delete(node_path, recursive=recursive)
        except NoNodeError:
            pass
        except NotEmptyError:
            raise LsyzwmZooError(message=f"节点非空，无法删除: {node_path}", code=-2008, data={"path": node_path})
        except Exception as e:
            raise LsyzwmZooError(message=f"删除节点失败: {node_path} - {str(e)}", code=-2009, data={"path": node_path, "error": str(e)})

    def exists(self, node_path: str) -> bool:
        """检查节点是否存在

        Args:
            node_path: 节点路径

        Returns:
            True 如果节点存在，否则 False
        """
        self._ensure_connected()
        return self.zk.exists(node_path) is not None

    def get_children(self, node_path: str) -> List[str]:
        """获取节点的子节点列表

        Args:
            node_path: 节点路径

        Returns:
            子节点名称列表

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        self._ensure_connected()
        try:
            return self.zk.get_children(node_path)
        except NoNodeError:
            return []
        except Exception as e:
            raise LsyzwmZooError(message=f"获取子节点失败: {node_path} - {str(e)}", code=-2010, data={"path": node_path, "error": str(e)})

    def register_worker(self, worker_name: str, worker_sid: int) -> None:
        """注册 worker 实例（创建临时节点）

        Args:
            worker_name: worker 名称
            worker_sid: worker 实例 ID

        Raises:
            LsyzwmZooNodeExistsError: worker 实例已存在（可能是重复的 worker_sid 或程序未正常退出）
            LsyzwmZooError: 创建节点失败
        """
        worker_id = f"{worker_name}-{worker_sid}"
        worker_path = f"{self.WORKERS_PATH}/{worker_id}"
        self._create_node(worker_path, payload=None, ephemeral=True)

    def watch_worker_tasks(self, worker_name: str, worker_sid: int, callback: Callable[[List[str]], None]) -> ChildrenWatch:
        """监听 worker 实例的任务节点变化

        Args:
            worker_name: worker 名称
            worker_sid: worker 实例 ID
            callback: 回调函数，接收子节点列表作为参数

        Returns:
            ChildrenWatch 对象

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        self._ensure_connected()
        worker_id = f"{worker_name}-{worker_sid}"
        task_node_path = f"{self.TASKS_PATH}/{worker_id}"

        # 确保任务节点路径存在
        if not self.exists(task_node_path):
            try:
                self.zk.ensure_path(task_node_path)
            except Exception as e:
                raise LsyzwmZooError(message=f"创建任务节点路径失败: {task_node_path} - {str(e)}", code=-2014, data={"path": task_node_path, "error": str(e)})

        # 创建并返回 ChildrenWatch
        try:
            return ChildrenWatch(self.zk, task_node_path, callback)
        except Exception as e:
            raise LsyzwmZooError(message=f"创建任务监听器失败: {task_node_path} - {str(e)}", code=-2015, data={"path": task_node_path, "error": str(e)})

    def add_task_node(self, worker_name: str, task_id: str, payload: Dict, worker_sid: Optional[int] = None) -> None:
        """添加任务节点

        Args:
            worker_name: worker 名称
            task_id: 任务 ID
            payload: 任务负载数据
            worker_sid: worker 实例 ID（可选，如果为空则随机选择一个在线实例）

        Raises:
            LsyzwmZooError: 当添加失败时
        """
        # 如果指定了 worker_sid，直接使用
        if worker_sid is not None:
            worker_id = f"{worker_name}-{worker_sid}"
        else:
            # 获取该 worker 的所有实例
            worker_instances = self.get_worker_instances(worker_name)

            # 如果没有在线实例，使用默认实例名，否则从在线实例中随机选择一个
            if not worker_instances:
                worker_id = f"{worker_name}-1"
            else:
                worker_id = random.choice(worker_instances)

        task_path = f"{self.TASKS_PATH}/{worker_id}/{task_id}"
        self._create_node(task_path, payload)

    def remove_task_node(self, task_id: str) -> None:
        """移除任务节点（搜索所有 worker）

        Args:
            task_id: 任务 ID

        Raises:
            LsyzwmZooError: 当移除失败时
        """
        # 遍历所有 worker，查找并删除任务
        if not self.exists(self.TASKS_PATH):
            return

        workers = self.get_children(self.TASKS_PATH)
        found = False

        for worker_id in workers:
            task_path = f"{self.TASKS_PATH}/{worker_id}/{task_id}"
            if self.exists(task_path):
                self._delete_node(task_path)
                found = True

        if not found:
            pass

    def remove_worker_instance_task(self, worker_name: str, worker_sid: int, task_id: str) -> None:
        """移除指定 worker 实例的任务

        Args:
            worker_name: worker 名称
            worker_sid: worker 实例 ID
            task_id: 任务 ID

        Raises:
            LsyzwmZooError: 当移除失败时
        """
        worker_id = f"{worker_name}-{worker_sid}"
        task_path = f"{self.TASKS_PATH}/{worker_id}/{task_id}"
        self._delete_node(task_path)

    def get_worker_instance_task(self, worker_name: str, worker_sid: int, task_id: str, as_json: bool = True) -> Optional[Union[str, Dict]]:
        """获取指定 worker 实例的任务值

        Args:
            worker_name: worker 名称
            worker_sid: worker 实例 ID
            task_id: 任务 ID
            as_json: 是否解析为 JSON，默认 True

        Returns:
            任务数据（字符串或字典），如果不存在则返回 None

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        worker_id = f"{worker_name}-{worker_sid}"
        task_path = f"{self.TASKS_PATH}/{worker_id}/{task_id}"

        value = self._get_node_value(task_path)
        if value is None:
            return None

        if as_json:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise LsyzwmZooError(message=f"JSON 解析失败: {task_path}", code=-2011, data={"path": task_path, "error": str(e)})

        return value

    def get_registered_workers(self) -> List[str]:
        """获取已注册的 worker 列表

        Returns:
            worker ID 列表
        """
        return self.get_children(self.WORKERS_PATH)

    def get_worker_instances(self, worker_name: str) -> List[str]:
        """获取指定 worker 的所有实例

        Args:
            worker_name: worker 名称

        Returns:
            匹配的 worker 实例列表（格式: worker_name-实例id）

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        all_workers = self.get_registered_workers()
        # 过滤出匹配 worker_name 的实例（格式: worker_name-实例id）
        worker_instances = [w for w in all_workers if w.startswith(f"{worker_name}-")]
        return worker_instances

    def get_worker_cache_value(self, worker_name: str, cache_id: str, as_json: bool = False) -> Optional[Union[str, Dict]]:
        """获取 worker 缓存节点值

        Args:
            worker_name: worker 名称
            cache_id: 缓存 ID
            as_json: 是否解析为 JSON，默认 False

        Returns:
            缓存数据（字符串或字典），如果不存在则返回 None

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        cache_path = f"{self.CACHES_PATH}/{worker_name}/{cache_id}"
        value = self._get_node_value(cache_path)

        if value is None:
            return None

        if as_json:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise LsyzwmZooError(message=f"JSON 解析失败: {cache_path}", code=-2012, data={"path": cache_path, "error": str(e)})

        return value

    def set_worker_cache_value(self, worker_name: str, cache_id: str, payload: Optional[Union[str, Dict]] = None) -> None:
        """设置 worker 缓存节点值

        Args:
            worker_name: worker 名称
            cache_id: 缓存 ID
            payload: 缓存数据（字符串或字典，可以为 None）

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        cache_path = f"{self.CACHES_PATH}/{worker_name}/{cache_id}"
        self._set_node_value(cache_path, payload)

    def get_worker_instance_cache_value(self, worker_name: str, worker_sid: int, cache_id: str, as_json: bool = False) -> Optional[Union[str, Dict]]:
        """获取 worker 实例缓存节点值

        Args:
            worker_name: worker 名称
            worker_sid: worker 实例 ID
            cache_id: 缓存 ID
            as_json: 是否解析为 JSON，默认 False

        Returns:
            缓存数据（字符串或字典），如果不存在则返回 None

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        worker_id = f"{worker_name}-{worker_sid}"
        cache_path = f"{self.CACHES_PATH}/{worker_id}/{cache_id}"
        value = self._get_node_value(cache_path)

        if value is None:
            return None

        if as_json:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise LsyzwmZooError(message=f"JSON 解析失败: {cache_path}", code=-2013, data={"path": cache_path, "error": str(e)})

        return value

    def set_worker_instance_cache_value(self, worker_name: str, worker_sid: int, cache_id: str, payload: Optional[Union[str, Dict]] = None) -> None:
        """设置 worker 实例缓存节点值

        Args:
            worker_name: worker 名称
            worker_sid: worker 实例 ID
            cache_id: 缓存 ID
            payload: 缓存数据（字符串或字典，可以为 None）

        Raises:
            LsyzwmZooError: 当操作失败时
        """
        worker_id = f"{worker_name}-{worker_sid}"
        cache_path = f"{self.CACHES_PATH}/{worker_id}/{cache_id}"
        self._set_node_value(cache_path, payload)

    def create_delay_job_node(self, job_id: str, worker_name: str, payload: Dict, delay_ts: int, ts: int, who: str, worker_sid: Optional[int] = None) -> None:
        """创建延时任务节点

        Args:
            job_id: 任务 ID
            worker_name: worker 名称
            payload: 任务负载数据
            delay_ts: 延迟时间戳
            ts: 创建时间戳
            who: 创建者标识
            worker_sid: worker 实例 ID（可选）

        Raises:
            LsyzwmZooError: 当创建失败时
        """
        node_value = {"job_id": job_id, "worker_name": worker_name, "worker_sid": worker_sid, "payload": payload, "delay_ts": delay_ts, "ts": ts, "who": who}
        node_path = f"{self.DELAY_JOBS_PATH}/{worker_name}/{job_id}"
        self._create_node(node_path, node_value)

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
        return False
