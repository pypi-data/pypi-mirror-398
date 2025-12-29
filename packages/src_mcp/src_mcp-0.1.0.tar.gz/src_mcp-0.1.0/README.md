# My MCP Server

这是一个自定义的 MCP (Model Context Protocol) 服务器，支持三种传输方式，可以与 Cherry Studio 等 AI 客户端配合使用。

## 三种传输方式

| 模式 | 传输方式 | 适用场景 | 端口 |
|------|----------|----------|------|
| STUDIO | stdio | 桌面应用本地配置（如 Cherry Studio） | 无 |
| SSE | Server-Sent Events | 需要实时推送的场景 | 8080 |
| StreamableHttp | HTTP RESTful API | Web 应用和 HTTP 交互 | 3000 |

## 功能

所有模式都提供以下工具：

- `hello_world` - 返回问候消息
- `echo` - 回显消息（用于测试）
- `get_time` - 获取当前时间
- `calculate` - 执行数学计算
- `store_data` - 存储数据
- `retrieve_data` - 检索数据

## 安装

1. 创建虚拟环境：
```bash
python -m venv venv
venv\Scripts\activate
```

2. 安装依赖：
```bash
pip install -e .
```

3. 安装额外的 HTTP 服务器依赖（用于 SSE 和 HTTP 模式）：
```bash
pip install uvicorn starlette
```

## 运行

### 方式一：使用启动菜单（推荐）

```bash
start.bat
```

根据提示选择要启动的模式。

### 方式二：直接运行特定模式

**STUDIO 模式（stdio）：**
```bash
python server_studio.py
```

**SSE 模式：**
```bash
python server_sse.py
```

**StreamableHttp 模式：**
```bash
python server_streamable.py
```

## 在 Cherry Studio 中配置

### STUDIO 模式（stdio）

1. 打开 Cherry Studio
2. 进入「设置」→「MCP 服务器」
3. 点击「添加服务器」
4. 选择「命令」方式
5. 配置以下信息：
   - 命令：`python`
   - 参数：`C:\Users\ASUS\Documents\trae_projects\4\my-mcp-server\server_studio.py`
   - 环境变量：（可选）
6. 点击「保存」

### SSE 模式

1. 先启动服务器：`python server_sse.py`
2. 打开 Cherry Studio
3. 进入「设置」→「MCP 服务器」
4. 点击「添加服务器」
5. 选择「URL」方式
6. 配置以下信息：
   - URL：`http://localhost:8080/sse`
7. 点击「保存」

### StreamableHttp 模式

1. 先启动服务器：`python server_streamable.py`
2. 打开 Cherry Studio
3. 进入「设置」→「MCP 服务器」
4. 点击「添加服务器」
5. 选择「URL」方式
6. 配置以下信息：
   - URL：`http://localhost:3000/mcp`
7. 点击「保存」

## 测试连接

启动服务器后，可以使用以下方法测试：

1. **STUDIO 模式**：在 Cherry Studio 中添加服务器后，查看工具列表是否包含上述工具
2. **SSE 模式**：访问 http://localhost:8080/messages 查看服务器状态
3. **StreamableHttp 模式**：访问 http://localhost:3000/health 查看服务器状态

## 添加自定义工具

编辑对应的服务器文件，在 `main()` 函数之前使用 `@app.tool()` 装饰器添加自定义工具：

```python
@app.tool()
def your_tool_name(param1: str, param2: int) -> str:
    """工具描述"""
    # 工具实现
    return "结果"
```

## 文件结构

```
my-mcp-server/
├── server_studio.py      # STUDIO 模式 (stdio)
├── server_sse.py         # SSE 模式
├── server_streamable.py  # StreamableHttp 模式
├── start.bat             # 启动菜单
├── pyproject.toml        # 项目配置
└── README.md             # 说明文档
```

## 故障排除

### 端口被占用

如果启动时提示端口被占用，可以修改对应文件中的端口号：
- SSE 模式：修改 `server_sse.py` 中的 `port=8080`
- StreamableHttp 模式：修改 `server_streamable.py` 中的 `port=3000`

### 连接失败

1. 确保服务器已启动
2. 检查端口是否正确
3. 防火墙是否允许相应端口
4. 查看服务器控制台输出的错误信息
