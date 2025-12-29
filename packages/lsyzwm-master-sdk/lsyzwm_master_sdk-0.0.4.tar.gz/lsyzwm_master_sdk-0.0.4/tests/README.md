# 测试说明

## 安装测试依赖

```bash
pip install -e ".[test]"
```

## 运行测试

### 运行所有测试
```bash
pytest tests/
```

### 运行指定测试文件
```bash
pytest tests/test_rpc_client.py
```

### 运行指定测试类
```bash
pytest tests/test_rpc_client.py::TestMasterRpcClient
```

### 运行指定测试方法
```bash
pytest tests/test_rpc_client.py::TestMasterRpcClient::test_add_worker_task_success
```

### 显示详细输出
```bash
pytest tests/ -v
```

### 显示测试覆盖率
```bash
pytest tests/ --cov=src/lsyzwm_master_sdk --cov-report=html
```

## 测试覆盖范围

### test_rpc_client.py
测试 `MasterRpcClient` 类的所有功能：

#### Worker 任务管理
- ✓ 添加 worker 任务（成功/失败）
- ✓ 添加 worker 任务（指定 worker_sid）
- ✓ 移除 worker 任务
- ✓ 移除指定 worker 实例的任务
- ✓ 获取 worker 实例的任务值

#### 定时作业管理
- ✓ 添加 cron 定时作业
- ✓ 添加间隔执行作业
- ✓ 添加延迟作业
- ✓ 移除作业

#### 异常处理
- ✓ 连接被拒绝异常（-1001）
- ✓ 协议错误异常（-1000）
- ✓ XMLRPC Fault 异常
- ✓ 超时异常（-1002）
- ✓ JSON 解析错误（-1003）
- ✓ 业务逻辑错误（code != 200）

#### 参数测试
- ✓ default_who 参数
- ✓ 自定义 who 参数覆盖 default_who

## 注意事项

1. 测试使用 mock 模拟 RPC 服务器，不需要真实的服务器运行
2. RPC_SERVER_URL 设置为 `http://localhost:9020`
3. 所有测试都是独立的，互不影响
