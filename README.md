# tiny-agent

agent.py 初版由 Claude 辅助编写，我逐行读懂后自己做了修改；学习过程见 LEARNING.md 和 logs/。

从零写一个 coding agent，每一课加一个现代 agent 的核心机制。只用 Python 标准库。

## 运行

先确认 `claude` 命令行已登录（终端里运行 `claude`，按提示 `/login`），然后：

```bash
mkdir -p playground && cd playground
python3 ../agent.py "写一个斐波那契函数和单元测试，并运行测试直到通过"
```

每次执行命令或写文件前都会问你 `[y/N]`。设置 `YOLO=1` 可以跳过确认（只在 playground 里这么做）。

## 课程路线

| 课 | 加入的机制 | 对应 Claude Code / Codex 里的什么 |
|---|---|---|
| 1 | 循环 + bash / 读写文件工具 | agent loop |
| 2 | 原生 function calling，替换手写 JSON 协议 | tool use API |
| 3 | 精确编辑工具 + 危险命令拦截 | Edit 工具、权限系统 |
| 4 | 上下文压缩 | auto-compact |
| 5 | todo 列表与计划模式 | TodoWrite、plan mode |
| 6 | 项目记忆与 skills | CLAUDE.md / AGENTS.md、skills |
| 7 | sub-agent 与并行 map-reduce | Task / sub-agent |
| 8 | MCP 客户端 | MCP |
| 9 | 后台任务与沙箱 | background shell、sandbox |
| 10 | headless 模式、运行日志、小型评测集 | `claude -p`、`codex exec` |
