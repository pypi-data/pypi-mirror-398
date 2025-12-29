"""
测试 MasterRpcClient 类
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from xmlrpc.client import Fault, ProtocolError

from src.lsyzwm_master_sdk.rpc_client import MasterRpcClient
from src.lsyzwm_master_sdk.exceptions import LsyzwmRpcError


RPC_SERVER_URL = "http://localhost:9020"


class TestMasterRpcClient:
    """测试 MasterRpcClient 类"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.client = MasterRpcClient(RPC_SERVER_URL, default_who="test_user")

    def test_init(self):
        """测试客户端初始化"""
        assert self.client.rpc_url == RPC_SERVER_URL
        assert self.client.default_who == "test_user"
        assert self.client.client is not None

    def test_parse_response_success(self):
        """测试解析成功响应"""
        response = json.dumps({"code": 200, "message": "成功", "data": {"key": "value"}, "error": False})
        result = self.client._parse_response(response)
        assert result["code"] == 200
        assert result["data"]["key"] == "value"

    def test_parse_response_error(self):
        """测试解析错误响应"""
        response = json.dumps({"code": -1, "message": "失败", "data": None, "error": True})
        with pytest.raises(LsyzwmRpcError) as exc_info:
            self.client._parse_response(response)

        assert exc_info.value.code == -1
        assert exc_info.value.message == "失败"

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_add_worker_task_success(self, mock_server_proxy):
        """测试添加 worker 任务 - 成功"""
        # 模拟成功响应
        mock_client = MagicMock()
        mock_client.add_worker_task.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"})

        assert result["code"] == 200
        mock_client.add_worker_task.assert_called_once()

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_add_worker_task_with_worker_sid(self, mock_server_proxy):
        """测试添加 worker 任务 - 指定 worker_sid"""
        mock_client = MagicMock()
        mock_client.add_worker_task.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"}, worker_sid=123)

        assert result["code"] == 200

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_remove_worker_task_success(self, mock_server_proxy):
        """测试移除 worker 任务 - 成功"""
        mock_client = MagicMock()
        mock_client.remove_worker_task.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.remove_worker_task(task_id="task_001")

        assert result["code"] == 200
        mock_client.remove_worker_task.assert_called_once()

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_remove_worker_instance_task_success(self, mock_server_proxy):
        """测试移除指定 worker 实例的任务 - 成功"""
        mock_client = MagicMock()
        mock_client.remove_worker_instance_task.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.remove_worker_instance_task(worker_name="test_worker", worker_sid=123, task_id="task_001")

        assert result["code"] == 200

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_get_worker_instance_task_success(self, mock_server_proxy):
        """测试获取 worker 实例任务 - 成功"""
        mock_client = MagicMock()
        mock_client.get_worker_instance_task.return_value = json.dumps({"code": 200, "message": "成功", "data": {"task_data": "value"}, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.get_worker_instance_task(worker_name="test_worker", worker_sid=123, task_id="task_001")

        assert result["code"] == 200
        assert result["data"]["task_data"] == "value"

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_add_cron_job_success(self, mock_server_proxy):
        """测试添加 cron 作业 - 成功"""
        mock_client = MagicMock()
        mock_client.add_cron_job.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.add_cron_job(job_id="job_001", worker_name="test_worker", payload={"data": "test"}, cron="0 * * * *")

        assert result["code"] == 200

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_add_interval_job_success(self, mock_server_proxy):
        """测试添加间隔作业 - 成功"""
        mock_client = MagicMock()
        mock_client.add_interval_job.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.add_interval_job(job_id="job_001", worker_name="test_worker", payload={"data": "test"}, hours=1)

        assert result["code"] == 200

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_add_delay_job_success(self, mock_server_proxy):
        """测试添加延迟作业 - 成功"""
        mock_client = MagicMock()
        mock_client.add_delay_job.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.add_delay_job(job_id="job_001", worker_name="test_worker", payload={"data": "test"}, delay_ts=60)

        assert result["code"] == 200

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_remove_job_success(self, mock_server_proxy):
        """测试移除作业 - 成功"""
        mock_client = MagicMock()
        mock_client.remove_job.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)
        result = client.remove_job(job_id="job_001")

        assert result["code"] == 200

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_connection_refused_error(self, mock_server_proxy):
        """测试连接被拒绝异常"""
        mock_client = MagicMock()
        mock_client.add_worker_task.side_effect = ConnectionRefusedError("Connection refused")
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)

        with pytest.raises(LsyzwmRpcError) as exc_info:
            client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"})

        assert exc_info.value.code == -1001
        assert "连接失败" in exc_info.value.message

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_protocol_error(self, mock_server_proxy):
        """测试协议错误异常"""
        mock_client = MagicMock()
        protocol_error = ProtocolError(url=RPC_SERVER_URL, errcode=404, errmsg="Not Found", headers={})
        mock_client.add_worker_task.side_effect = protocol_error
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)

        with pytest.raises(LsyzwmRpcError) as exc_info:
            client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"})

        assert exc_info.value.code == -1000
        assert "协议错误" in exc_info.value.message

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_xmlrpc_fault(self, mock_server_proxy):
        """测试 XMLRPC Fault 异常"""
        mock_client = MagicMock()
        fault = Fault(faultCode=500, faultString="Internal Server Error")
        mock_client.add_worker_task.side_effect = fault
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)

        with pytest.raises(LsyzwmRpcError) as exc_info:
            client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"})

        assert exc_info.value.code == 500
        assert "服务端错误" in exc_info.value.message

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_timeout_error(self, mock_server_proxy):
        """测试超时异常"""
        mock_client = MagicMock()
        mock_client.add_worker_task.side_effect = TimeoutError("Connection timeout")
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)

        with pytest.raises(LsyzwmRpcError) as exc_info:
            client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"})

        assert exc_info.value.code == -1002
        assert "超时" in exc_info.value.message

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_json_decode_error(self, mock_server_proxy):
        """测试 JSON 解析错误"""
        mock_client = MagicMock()
        mock_client.add_worker_task.return_value = "invalid json"
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)

        with pytest.raises(LsyzwmRpcError) as exc_info:
            client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"})

        assert exc_info.value.code == -1003
        assert "解析失败" in exc_info.value.message

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_business_error(self, mock_server_proxy):
        """测试业务逻辑错误（code != 200）"""
        mock_client = MagicMock()
        mock_client.add_worker_task.return_value = json.dumps({"code": 400, "message": "参数错误", "data": None, "error": True})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL)

        with pytest.raises(LsyzwmRpcError) as exc_info:
            client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"})

        assert exc_info.value.code == 400
        assert exc_info.value.message == "参数错误"

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_default_who_parameter(self, mock_server_proxy):
        """测试 default_who 参数的使用"""
        mock_client = MagicMock()
        mock_client.add_worker_task.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        # 使用默认的 default_who
        client = MasterRpcClient(RPC_SERVER_URL, default_who="admin")
        client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"})

        # 检查调用参数中的 who 参数
        call_args = mock_client.add_worker_task.call_args[0]
        assert call_args[4] == "admin"  # who 参数

    @patch("src.lsyzwm_master_sdk.rpc_client.ServerProxy")
    def test_custom_who_parameter(self, mock_server_proxy):
        """测试自定义 who 参数会覆盖 default_who"""
        mock_client = MagicMock()
        mock_client.add_worker_task.return_value = json.dumps({"code": 200, "message": "成功", "data": None, "error": False})
        mock_server_proxy.return_value = mock_client

        client = MasterRpcClient(RPC_SERVER_URL, default_who="admin")
        client.add_worker_task(task_id="task_001", worker_name="test_worker", payload={"data": "test"}, who="custom_user")

        # 检查调用参数中的 who 参数
        call_args = mock_client.add_worker_task.call_args[0]
        assert call_args[4] == "custom_user"  # who 参数


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
