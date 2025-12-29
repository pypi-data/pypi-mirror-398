# Interactive Feedback MCP

一个功能强大的 MCP (Model Context Protocol) 服务器,提供交互式反馈界面,支持工作空间管理、任务追踪和检查点恢复。

## ✨ 核心特性

- 🎯 **交互式反馈界面**: 基于 PySide6 的现代化 UI,支持文本、图片等多种反馈方式
- 📁 **工作空间管理**: 完整的工作空间生命周期管理,支持阶段切换
- ✅ **任务追踪**: 强大的任务管理系统,支持依赖关系、优先级、并行执行
- 💾 **检查点恢复**: 创建、恢复、对比工作检查点,确保工作安全
- 🔄 **工作流支持**: 模板化工作流,支持自定义工作流程
- 📊 **会话管理**: 完整的会话历史记录和统计

## 🚀 快速开始

### 方式一：使用 uv tool 安装（推荐）

#### 安装 feedback-mcp

```bash
# 使用清华镜像（推荐，国内速度快）
uv tool install feedback-mcp@latest --index https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
uv tool install feedback-mcp@latest --index https://mirrors.aliyun.com/pypi/simple/

# 验证安装
uv tool list | grep feedback
which feedback-mcp

# 更新版本
uv tool upgrade feedback-mcp
```

**优势：**
- ✅ 只占用 1.1GB 空间（不会重复缓存）
- ✅ 启动速度快 10-30 倍
- ✅ 使用国内镜像下载速度快（1-3分钟 vs 10-30分钟）
- ✅ 一次安装，长期使用
- ✅ 自动管理 Python 版本（支持 3.10-3.12）

**可选：配置全局镜像**

如果不想每次都加 `--index` 参数，可以配置 `~/.config/uv/uv.toml`：

```toml
[[index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

配置后直接运行 `uv tool install feedback-mcp@latest` 即可。

### 方式二：使用 pip 安装

```bash
# 使用清华镜像安装
pip install feedback-mcp -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或配置 pip 全局镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install feedback-mcp
```

### 配置 MCP 服务器

在你的 MCP 客户端配置文件（如 `.mcp.json`）中添加：

#### 使用 uv tool 方式（推荐）

```json
{
  "mcpServers": {
    "feedback": {
      "command": "feedback-mcp",
      "args": ["--ide", "qoder"],
      "timeout": 30000,
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```


**参数说明：**
- `--ide`: IDE 名称，可选值：`qoder`、`cursor`、`vscode` 等
- `timeout`: 超时时间（毫秒），建议 30000 以上
- `autoApprove`: 自动批准的工具列表

### 配置 Stop Hook

在项目的 `hooks/hooks.json` 文件中配置停止钩子：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uvx --from feedback-mcp --with feedback-mcp python -m stop_hook"
          }
        ]
      }
    ]
  }
}
```

**注意：**
- `uvx` 会自动选择合适的 Python 版本（3.10-3.12）
- 如需指定版本可添加 `--python 3.11` 参数
- 如果使用 `uv tool install` 方式，参考上文中的路径配置
- 如果使用 pip 全局安装，使用 `python3 -m stop_hook` 即可
- Stop Hook 用于在会话结束时触发反馈提示

### 使用示例

安装配置完成后，AI 助手可以通过 `interactive_feedback` 工具与你交互：

```python
# AI 助手自动调用 feedback 工具
# 弹出交互式反馈窗口
# 支持文本输入、预定义选项、文件选择等多种交互方式
```

## 📦 主要功能

### 1. 工作空间管理

- 创建工作空间并设置目标
- 管理工作空间的不同阶段
- 记录工作记忆和相关文件
- 支持多个并行工作空间

### 2. 任务管理

- 创建和更新任务列表
- 设置任务依赖关系和优先级
- 支持任务并行执行
- 实时任务状态追踪

### 3. 检查点系统

- 创建工作检查点快照
- 恢复到历史检查点
- 对比不同检查点的差异
- 自动收集相关文件

### 4. 工作流引擎

- 预定义工作流模板
- 自定义工作流步骤
- 工作流状态管理
- 步骤依赖和执行控制

## 🔧 系统要求

- Python >= 3.10, < 3.13 (支持 3.10, 3.11, 3.12)
- PySide6 >= 6.8.0
- FastMCP >= 2.5.1

## 🐛 常见问题

### 1. 磁盘空间占用过大

**问题：** `~/.cache/uv/` 目录占用大量磁盘空间（可能达到 100GB+）

**原因：** 使用 `uvx` 方式会为每次运行创建独立的虚拟环境缓存

**解决方案：**
```bash
# 清理 uv 缓存
uv cache clean

# 迁移到 uv tool install 方式（推荐）
uv tool install feedback-mcp@latest
```

迁移后磁盘占用从 ~125GB 降至 ~1.1GB，启动速度提升 10-30 倍。

### 2. 安装速度慢

**问题：** 下载 PySide6 等大型依赖包速度很慢

**解决方案：** 配置国内镜像加速（见上文"配置国内镜像加速"章节）

### 3. Stop Hook 不工作

**问题：** 会话结束时没有弹出反馈窗口

**排查步骤：**
```bash
# 1. 检查 hooks.json 配置是否正确
cat hooks/hooks.json

# 2. 测试 stop_hook 模块是否可用
~/.local/share/uv/tools/feedback-mcp/bin/python -m stop_hook

# 3. 检查 Python 路径是否正确
which python
ls -la ~/.local/share/uv/tools/feedback-mcp/bin/python
```

**解决方案：** 确保 hooks.json 中的 Python 路径与实际安装位置一致

### 4. 权限问题

**问题：** `permission denied: feedback-mcp`

**解决方案：**
```bash
# 添加执行权限
chmod +x ~/.local/bin/feedback-mcp

# 确保 ~/.local/bin 在 PATH 中
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 5. 版本更新

**更新到最新版本：**
```bash
# 使用 uv tool
uv tool upgrade feedback-mcp

# 或重新安装特定版本
uv tool install feedback-mcp@1.0.4 --force

# 使用 pip
pip install --upgrade feedback-mcp -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6. 从 uvx 迁移到 uv tool

如果你之前使用 `uvx` 方式，建议迁移到 `uv tool install`：

**迁移步骤：**
1. 清理旧缓存：`uv cache clean`
2. 安装工具：`uv tool install feedback-mcp@latest`
3. 更新 `.mcp.json`：将 `command` 从 `"uvx"` 改为 `"feedback-mcp"`
4. 更新 `hooks.json`：使用完整的 Python 路径

详细迁移指南请参考项目中的 `MIGRATION_SUMMARY.md` 文档。

## 🔍 调试模式

启用调试日志：

```bash
# 设置环境变量
export DEBUG=1
feedback-mcp --ide qoder

# 查看日志
tail -f /path/to/feedback.log
```

## 📝 开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/interactive-feedback-mcp.git
cd interactive-feedback-mcp

# 安装开发依赖
pip install -e ".[dev]"

# 运行服务器
python -m src-min.server
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License

## 🔗 相关链接

- [GitHub Repository](https://github.com/yourusername/interactive-feedback-mcp)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Issue Tracker](https://github.com/yourusername/interactive-feedback-mcp/issues)
