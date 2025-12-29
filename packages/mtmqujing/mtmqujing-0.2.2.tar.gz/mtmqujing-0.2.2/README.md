# mtmqujing

一个用于调用远程服务的Python客户端库，支持同步和异步两种调用方式。

## 安装

基础安装（仅同步功能）：
```bash
pip install mtmqujing
```

包含异步功能的完整安装：
```bash
pip install mtmqujing[async]
```

或者单独安装异步依赖：
```bash
pip install aiohttp>=3.8.0
```

## 使用方法

### 同步版本

```python
from mtmqujing import QujingByHttp

# 创建客户端
client = QujingByHttp(host="localhost", port_config=61000)

# 获取包的进程ID
packages = ["your_package"]
ports = client.get_pid(packages)
print(f"端口信息: {ports}")

# 设置目标应用
result = client.set_app(packages)
print(f"设置结果: {result}")

# 调用远程函数
if ports:
    port = list(ports.values())[0]
    data = {"function": "your_function", "args": {"param": "value"}}
    response = client.invoke(port, data)
    print(f"调用结果: {response}")
```

### 异步版本

```python
import asyncio
from mtmqujing import AsyncQujingByHttp

async def main():
    # 创建异步客户端
    client = AsyncQujingByHttp(host="localhost", port_config=61000)
    
    # 异步获取包的进程ID
    packages = ["your_package"]
    ports = await client.get_pid(packages)
    print(f"端口信息: {ports}")
    
    # 异步设置目标应用
    result = await client.set_app(packages)
    print(f"设置结果: {result}")
    
    # 异步调用远程函数
    if ports:
        port = list(ports.values())[0]
        data = {"function": "your_function", "args": {"param": "value"}}
        response = await client.invoke(port, data)
        print(f"调用结果: {response}")

# 运行异步函数
asyncio.run(main())
```

### 并发调用（异步版本的优势）

```python
import asyncio
from mtmqujing import AsyncQujingByHttp

async def concurrent_calls():
    client = AsyncQujingByHttp(host="localhost", port_config=61000)
    
    # 同时发起多个异步调用
    packages_list = [["package1"], ["package2"], ["package3"]]
    tasks = [client.get_pid(packages) for packages in packages_list]
    results = await asyncio.gather(*tasks)
    
    print(f"并发调用结果: {results}")

asyncio.run(concurrent_calls())
```

## API 文档

### QujingByHttp (同步版本)

#### `__init__(host, port_config=61000, protocol="http")`
初始化客户端。

- `host`: 服务器地址
- `port_config`: 配置端口，默认61000
- `protocol`: 协议，默认"http"

#### `get_pid(packages, **kwargs)`
获取包名对应的进程号（端口号）。

- `packages`: 包名列表
- 返回: 字典，包名到端口号的映射

#### `set_app(packages, **kwargs)`
设置目标应用。

- `packages`: 包名列表
- 返回: 布尔值，表示是否设置成功

#### `invoke(port_invoke, data, **kwargs)`
调用目标应用的函数。

- `port_invoke`: 调用端口
- `data`: 调用数据
- 返回: 字典，包含响应数据和数据类型

### AsyncQujingByHttp (异步版本)

异步版本的API与同步版本完全相同，只是所有方法都是异步的（需要使用`await`关键字）。

## 数据转换工具

库还提供了`FormatConvert`类用于各种数据格式转换：

```python
from mtmqujing.convert import FormatConvert

# Base64编码/解码
encoded = FormatConvert.bytes2base64(b"hello")
decoded = FormatConvert.base642bytes(encoded)

# JSON与字符串转换
json_str = FormatConvert.json2str({"key": "value"})
data = FormatConvert.str2json(json_str)

# Base64与JSON转换
b64_json = FormatConvert.json2base64({"key": "value"})
json_data = FormatConvert.base642json(b64_json)

# Gzip压缩相关转换
compressed = FormatConvert.gzip_json_to_base64({"key": "value"})
decompressed = FormatConvert.ungzip_base64_to_json(compressed)
```

## 错误处理

当调用失败时，会抛出`QujingInvokeError`异常：

```python
from mtmqujing.exceptions import QujingInvokeError

try:
    response = client.invoke(port, data)
except QujingInvokeError as e:
    print(f"调用失败: {e}")
```

## 许可证

MIT License
