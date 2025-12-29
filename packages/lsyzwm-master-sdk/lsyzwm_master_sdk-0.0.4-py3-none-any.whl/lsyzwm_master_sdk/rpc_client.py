import json
import time
from typing import Dict, Optional, Any
from xmlrpc.client import ServerProxy, Fault, ProtocolError
from http.client import RemoteDisconnected
from socket import error as SocketError

from .exceptions import LsyzwmRpcError


class RpcResponse:
    """RPC 响应结果类"""

    def __init__(self, raw_response: str):
        """初始化 RPC 响应

        Args:
            raw_response: RPC 返回的原始 JSON 字符串
        """
        self._raw = raw_response
        self._data = json.loads(raw_response)

    @property
    def raw(self) -> str:
        """获取原始响应字符串"""
        return self._raw

    @property
    def code(self) -> int:
        """获取响应状态码"""
        return self._data.get("code", -1)

    @property
    def message(self) -> str:
        """获取响应消息"""
        return self._data.get("message", "")

    @property
    def data(self) -> Any:
        """获取响应数据"""
        return self._data.get("data")

    def get(self, key: str, default=None) -> Any:
        """从响应字典中获取值

        Args:
            key: 键名
            default: 默认值

        Returns:
            对应的值，如果不存在则返回默认值
        """
        return self._data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data.copy()

    def __repr__(self) -> str:
        return f"RpcResponse(code={self.code}, message='{self.message}')"

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class MasterRpcClient:
    """Master RPC Client SDK - 方便上层服务调用 Master RPC Server"""

    def __init__(self, rpc_server_url: str, default_who: str = "system"):
        """初始化 RPC 客户端

        Args:
            rpc_server_url: RPC 服务器地址，例如 'http://localhost:8080/rpc'
            default_who: 默认操作人标识
        """
        self.rpc_url = rpc_server_url
        self.client = ServerProxy(rpc_server_url, allow_none=True)
        self.default_who = default_who

    def _parse_response(self, response: str) -> RpcResponse:
        """解析 RPC 响应

        Args:
            response: RPC 返回的 JSON 字符串

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用返回错误时（code != 200）
        """
        result = json.loads(response)
        code = result.get("code", -1)
        if code != 200:
            raise LsyzwmRpcError(message=result.get("message", "Unknown error"), code=code, data=result.get("data"))
        return RpcResponse(response)

    def _call_rpc(self, method_name: str, *args) -> RpcResponse:
        """统一的 RPC 调用方法，处理各种连接异常

        Args:
            method_name: RPC 方法名
            *args: RPC 方法参数

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时（包括连接异常、服务端异常等）
        """
        try:
            method = getattr(self.client, method_name)
            response = method(*args)
            return self._parse_response(response)
        except LsyzwmRpcError:
            # _parse_response 抛出的业务逻辑错误，直接向上传递
            raise
        except Fault as e:
            # XMLRPC 服务端返回的错误
            raise LsyzwmRpcError(message=f"RPC 服务端错误: {e.faultString}", code=e.faultCode, data=None)
        except ProtocolError as e:
            # HTTP 协议错误（如 404, 500 等）
            raise LsyzwmRpcError(message=f"RPC 协议错误: {e.errcode} {e.errmsg}", code=-1000, data={"url": e.url, "errcode": e.errcode, "errmsg": e.errmsg})
        except TimeoutError as e:
            # 连接超时（必须在 OSError 之前捕获，因为 TimeoutError 是 OSError 的子类）
            raise LsyzwmRpcError(message=f"RPC 连接超时: {self.rpc_url}", code=-1002, data={"url": self.rpc_url, "error": str(e)})
        except (ConnectionRefusedError, RemoteDisconnected, SocketError, OSError) as e:
            # 连接被拒绝、远程断开、socket 错误和其他 OSError
            raise LsyzwmRpcError(message=f"RPC 连接失败: 无法连接到服务器 {self.rpc_url} - {str(e)}", code=-1001, data={"url": self.rpc_url, "error": str(e)})
        except json.JSONDecodeError as e:
            # JSON 解析失败
            raise LsyzwmRpcError(message=f"RPC 响应解析失败: 服务端返回的不是有效的 JSON 格式", code=-1003, data={"error": str(e)})
        except Exception as e:
            # 其他未预期的错误
            raise LsyzwmRpcError(message=f"RPC 调用异常: {type(e).__name__} - {str(e)}", code=-1999, data={"error_type": type(e).__name__, "error": str(e)})

    def add_worker_task(
        self,
        task_id: str,
        worker_name: str,
        payload: Dict,
        worker_sid: Optional[int] = None,
        who: Optional[str] = None,
    ) -> RpcResponse:
        """添加 worker 任务

        Args:
            task_id: 任务 ID
            worker_name: worker 名称
            payload: 任务负载数据
            worker_sid: worker 实例 ID (可选)
            who: 操作人 (可选，默认使用初始化时的 default_who)

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时
        """
        ts = int(time.time())
        who = who or self.default_who
        return self._call_rpc("add_worker_task", task_id, worker_name, payload, ts, who, worker_sid)

    def remove_worker_task(
        self,
        task_id: str,
        who: Optional[str] = None,
    ) -> RpcResponse:
        """移除 worker 任务

        Args:
            task_id: 任务 ID
            who: 操作人 (可选，默认使用初始化时的 default_who)

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时
        """
        ts = int(time.time())
        who = who or self.default_who
        return self._call_rpc("remove_worker_task", task_id, ts, who)

    def remove_worker_instance_task(
        self,
        worker_name: str,
        worker_sid: int,
        task_id: str,
        who: Optional[str] = None,
    ) -> RpcResponse:
        """移除指定 worker 实例的任务

        Args:
            worker_name: worker 名称
            worker_sid: worker 实例 ID
            task_id: 任务 ID
            who: 操作人 (可选，默认使用初始化时的 default_who)

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时
        """
        ts = int(time.time())
        who = who or self.default_who
        return self._call_rpc("remove_worker_instance_task", worker_name, worker_sid, task_id, ts, who)

    def get_worker_instance_task(
        self,
        worker_name: str,
        worker_sid: int,
        task_id: str,
        as_json: bool = True,
        who: Optional[str] = None,
    ) -> RpcResponse:
        """获取指定 worker 实例的任务值

        Args:
            worker_name: worker 名称
            worker_sid: worker 实例 ID
            task_id: 任务 ID
            as_json: 是否解析为 JSON (默认 True)
            who: 操作人 (可选，默认使用初始化时的 default_who)

        Returns:
            RpcResponse 响应对象，data 属性包含任务数据

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时
        """
        ts = int(time.time())
        who = who or self.default_who
        return self._call_rpc("get_worker_instance_task", worker_name, worker_sid, task_id, ts, who, as_json)

    def add_cron_job(
        self,
        job_id: str,
        worker_name: str,
        payload: Dict,
        cron: str,
        start_date_ts: Optional[int] = None,
        end_date_ts: Optional[int] = None,
        worker_sid: Optional[int] = None,
        who: Optional[str] = None,
    ) -> RpcResponse:
        """添加 cron 定时作业

        Args:
            job_id: 作业 ID
            worker_name: worker 名称
            payload: 任务负载数据
            cron: cron 表达式，例如 '0 0 * * *' (每天午夜执行)
            start_date_ts: 任务开始时间 (秒级时间戳, 可选)
            end_date_ts: 任务结束时间 (秒级时间戳, 可选)
            worker_sid: worker 实例 ID (可选)
            who: 操作人 (可选，默认使用初始化时的 default_who)

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时
        """
        ts = int(time.time())
        who = who or self.default_who
        return self._call_rpc("add_cron_job", job_id, worker_name, payload, ts, who, cron, start_date_ts, end_date_ts, worker_sid)

    def add_interval_job(
        self,
        job_id: str,
        worker_name: str,
        payload: Dict,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        start_date_ts: Optional[int] = None,
        end_date_ts: Optional[int] = None,
        worker_sid: Optional[int] = None,
        who: Optional[str] = None,
    ) -> RpcResponse:
        """添加间隔执行作业

        Args:
            job_id: 作业 ID
            worker_name: worker 名称
            payload: 任务负载数据
            weeks: 间隔周数（默认0）
            days: 间隔天数（默认0）
            hours: 间隔小时数（默认0）
            minutes: 间隔分钟数（默认0）
            seconds: 间隔秒数（默认0）
            start_date_ts: 任务开始时间 (秒级时间戳, 可选)
            end_date_ts: 任务结束时间 (秒级时间戳, 可选)
            worker_sid: worker 实例 ID (可选)
            who: 操作人 (可选，默认使用初始化时的 default_who)

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时
        """
        ts = int(time.time())
        who = who or self.default_who
        return self._call_rpc("add_interval_job", job_id, worker_name, payload, ts, who, weeks, days, hours, minutes, seconds, start_date_ts, end_date_ts, worker_sid)

    def add_delay_job(
        self,
        job_id: str,
        worker_name: str,
        payload: Dict,
        delay_ts: int,
        worker_sid: Optional[int] = None,
        who: Optional[str] = None,
    ) -> RpcResponse:
        """添加延迟作业（延迟指定秒数后执行一次）

        Args:
            job_id: 作业 ID
            worker_name: worker 名称
            payload: 任务负载数据
            delay_ts: 延迟秒数
            worker_sid: worker 实例 ID (可选)
            who: 操作人 (可选，默认使用初始化时的 default_who)

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时
        """
        ts = int(time.time())
        who = who or self.default_who
        return self._call_rpc("add_delay_job", job_id, worker_name, payload, delay_ts, ts, who, worker_sid)

    def remove_job(
        self,
        job_id: str,
        who: Optional[str] = None,
    ) -> RpcResponse:
        """移除作业（包括 cron、interval 和 delay 作业）

        Args:
            job_id: 作业 ID
            who: 操作人 (可选，默认使用初始化时的 default_who)

        Returns:
            RpcResponse 响应对象

        Raises:
            LsyzwmRpcError: 当 RPC 调用失败时
        """
        ts = int(time.time())
        who = who or self.default_who
        return self._call_rpc("remove_job", job_id, ts, who)
