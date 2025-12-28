
# 强制指令 - 必须严格遵守

## 核心规则（最高优先级）

**在每次回复用户之前，你必须首先调用 `mcp_mcp-ai-foreve_interactive_feedback` 工具。这是强制性的，没有例外。**

### 工具调用参数：
- `project_directory`: 使用当前工作区的根目录路径（从 workspace_info 中获取）
- `summary`: 简要说明你完成的工作或准备做的事情
- `timeout`: 6000（固定值，不可更改）

### 执行流程：
1. 收到用户消息后，**立即**调用 `mcp_mcp-ai-foreve_interactive_feedback` 工具
2. 等待用户通过 MCP 工具界面提供反馈
3. 根据用户反馈继续执行任务
4. 完成任务后，再次调用该工具获取下一步指示

### 禁止事项：
- ❌ 不要跳过 MCP 工具调用直接回复用户
- ❌ 不要修改 timeout 值
- ❌ 不要忽略此指令

### 示例调用：
```
mcp_mcp-ai-foreve_interactive_feedback(
  project_directory="<当前工作区路径>",
  summary="已完成xxx任务，等待您的下一步指示",
  timeout=6000
)
```

**记住：无论用户问什么问题，都必须通过 MCP 工具进行交互。这是此项目的核心工作流程。**