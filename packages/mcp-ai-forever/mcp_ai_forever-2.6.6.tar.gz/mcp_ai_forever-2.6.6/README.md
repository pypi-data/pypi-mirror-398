# MCP AI Forever

**🌸 动漫粉蓝主题 | 智能 AI 交互工具**

## 🎯 核心功能

这是一个 [MCP 服务器](https://modelcontextprotocol.io/)，提供 **Web UI 交互界面**，用于 AI 辅助开发中的用户反馈和命令执行。

### ✨ 主要特性

- 🎨 **动漫粉蓝主题** - 精美的视觉体验
- 💬 **实时交互** - WebSocket 实时通信
- 👑 **VIP 功能** - 会员时间显示
- 🌐 **多语言支持** - 中文/英文

## 🚀 快速开始

### 安装
```bash
pip install mcp-ai-forever
```

或使用 uvx：
```bash
uvx mcp-ai-forever
```

### MCP 配置

在 VS Code 的 `mcp.json` 中添加：

```json
{
  "servers": {
    "mcp-ai-forever": {
      "command": "uvx",
      "args": ["mcp-ai-forever"],
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MCP_DEBUG` | 调试模式 | `false` |
| `MCP_WEB_HOST` | 绑定地址 | `127.0.0.1` |
| `MCP_WEB_PORT` | Web 端口 | `8765` |
| `MCP_LANGUAGE` | 界面语言 | 自动检测 |

## 📧 联系方式

- **邮箱**: dr.bsucs@gmail.com
- **QQ**: 494588788

## 📄 许可证

MIT License
