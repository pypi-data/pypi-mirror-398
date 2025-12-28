# MCP服务配置指南

本指南将帮助您将抖音语音识别服务配置为MCP（Model Context Protocol）服务器，以便在Claude Desktop等支持MCP的应用中使用。

## 前置要求

- Python 3.8 或更高版本
- 已获取 `RAPIDAPI_KEY` 和 `DASHSCOPE_API_KEY`

## 安装方式

### 方式1：通过 pip 安装（推荐）

```bash
pip install douyin-summary-mcp
```

安装后，MCP服务器命令 `douyin-summary-mcp` 将自动可用。

**验证安装：**
```bash
which douyin-summary-mcp
# 应该输出命令的路径，例如：/usr/local/bin/douyin-summary-mcp
```

### 方式2：从源码安装

```bash
git clone <repository-url>
cd douyin-summary-mcp
pip install -e .
```

**注意：** 如果使用虚拟环境，请确保在虚拟环境中安装，或者使用全局 Python 环境。

## 配置步骤

### 1. 配置Claude Desktop

#### macOS配置

编辑配置文件：`~/Library/Application Support/Claude/claude_desktop_config.json`

#### Windows配置

编辑配置文件：`%APPDATA%\Claude\claude_desktop_config.json`

#### Linux配置

编辑配置文件：`~/.config/Claude/claude_desktop_config.json`

### 2. 添加MCP服务器配置

在配置文件中添加以下内容（如果文件不存在，请创建它）：

#### 如果通过 pip 安装（推荐）：

```json
{
  "mcpServers": {
    "douyin-summary": {
      "command": "douyin-summary-mcp",
      "env": {
        "RAPIDAPI_KEY": "your_rapidapi_key_here",
        "DASHSCOPE_API_KEY": "your_dashscope_api_key_here"
      }
    }
  }
}
```

#### 如果从源码安装：

```json
{
  "mcpServers": {
    "douyin-summary": {
      "command": "python3",
      "args": [
        "/path/to/douyin-summary-mcp/mcp_server.py"
      ],
      "env": {
        "RAPIDAPI_KEY": "your_rapidapi_key_here",
        "DASHSCOPE_API_KEY": "your_dashscope_api_key_here"
      }
    }
  }
}
```

**重要提示：**
- 如果通过pip安装，直接使用 `douyin-summary-mcp` 命令，无需指定路径
- 如果从源码安装，将 `/path/to/douyin-summary-mcp/mcp_server.py` 替换为实际的绝对路径
- 将 `your_rapidapi_key_here` 和 `your_dashscope_api_key_here` 替换为您的实际API密钥

### 3. 配置 Cursor（如果使用 Cursor IDE）

编辑配置文件：`~/.cursor/mcp.json`（Linux/macOS）或 `%APPDATA%\Cursor\mcp.json`（Windows）

```json
{
  "mcpServers": {
    "douyin-summary": {
      "command": "douyin-summary-mcp",
      "env": {
        "RAPIDAPI_KEY": "your_rapidapi_key_here",
        "DASHSCOPE_API_KEY": "your_dashscope_api_key_here"
      }
    }
  }
}
```

**重要提示：**
- 确保 `douyin-summary-mcp` 命令在系统 PATH 中可用
- 如果使用虚拟环境，需要确保虚拟环境的 bin 目录在 PATH 中
- 或者使用完整路径：`"/path/to/venv/bin/douyin-summary-mcp"`

### 4. 重启应用

配置完成后，重启 Claude Desktop 或 Cursor 应用程序以使配置生效。

## 使用方法

配置完成后，您可以在Claude Desktop中：

1. 使用 `@douyin-summary` 工具
2. 提供抖音分享文本作为参数
3. 工具会自动处理并返回：
   - 提取的抖音链接
   - MP3音频地址
   - 语音识别的原始文本
   - 格式化后的对话JSON数组（包含说话人角色和内容）

## 验证配置

您可以通过以下方式验证MCP服务器是否正常工作：

```bash
# 设置环境变量
export RAPIDAPI_KEY="your_key"
export DASHSCOPE_API_KEY="your_key"

# 测试MCP服务器（需要手动发送JSON-RPC请求）
douyin-summary-mcp
```

或者如果从源码安装：

```bash
python3 mcp_server.py
```

## 故障排除

### 问题1: MCP服务器无法启动

- 检查Python路径是否正确
- 确认所有依赖已安装（`pip install douyin-summary-mcp`）
- 检查API Keys是否正确配置

### 问题2: 工具调用失败

- 检查环境变量是否正确设置
- 查看Claude Desktop的日志输出
- 确认API Keys有效且有足够的额度

### 问题3: 找不到命令（ENOENT错误）

如果通过pip安装后找不到 `douyin-summary-mcp` 命令，或出现 `spawn douyin-summary-mcp ENOENT` 错误：

**解决方案：**

1. **确认命令已安装：**
   ```bash
   pip show douyin-summary-mcp
   which douyin-summary-mcp  # Linux/macOS
   where douyin-summary-mcp   # Windows
   ```

2. **如果命令不存在，重新安装：**
   ```bash
   pip install --upgrade douyin-summary-mcp
   ```

3. **如果使用虚拟环境，确保虚拟环境的bin目录在PATH中：**
   ```bash
   # Linux/macOS
   export PATH="$HOME/.local/bin:$PATH"
   # 或
   export PATH="/path/to/venv/bin:$PATH"
   ```

4. **在配置中使用完整路径：**
   ```json
   {
     "mcpServers": {
       "douyin-summary": {
         "command": "/usr/local/bin/douyin-summary-mcp",
         "env": {
           "RAPIDAPI_KEY": "your_key",
           "DASHSCOPE_API_KEY": "your_key"
         }
       }
     }
   }
   ```

5. **检查Python的Scripts目录是否在PATH中（Windows）：**
- 尝试使用完整路径：`python -m douyin_summary_mcp.mcp_server`
- 重新安装：`pip install --force-reinstall douyin-summary-mcp`

### 问题4: 找不到模块

- 确保使用正确的Python解释器
- 检查项目路径是否正确
- 确认所有依赖已安装

## 安全提示

⚠️ **重要安全提示：**

- 不要将包含API Keys的配置文件提交到版本控制系统
- 使用环境变量或安全的密钥管理工具
- 定期轮换API Keys
- 限制API Keys的权限范围

## 获取API Keys

- **RAPIDAPI_KEY**: 访问 [RapidAPI Douyin API](https://rapidapi.com/manhgdev/api/douyin-api-app-web)，订阅服务并获取API Key
- **DASHSCOPE_API_KEY**: 访问 [阿里云DashScope](https://help.aliyun.com/zh/model-studio/get-api-key)，获取API Key

## 更新

如果通过pip安装，更新到最新版本：

```bash
pip install --upgrade douyin-summary-mcp
```

