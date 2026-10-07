#!/usr/bin/env python3
"""tiny-agent 第 1 课：最小 coding agent。

整个 agent 就是一个循环：
    1. 把对话历史拼成 prompt 发给模型
    2. 模型回一个 JSON，说明它想调用哪个工具
    3. 我们执行这个工具，拿到输出
    4. 把输出追加进历史，回到第 1 步，直到模型说 done

模型后端用的是 `claude -p`（Claude Code 的无界面模式），并关掉了它自带的全部工具，
所以它在这里只是一个"会说话的大脑"，所有动手的事都由本文件里的代码完成。
只用 Python 标准库，不需要安装任何依赖。
"""

import json
import os
import subprocess
import sys

MAX_TURNS = 30  # 防止死循环：最多让模型思考-行动 30 轮

SYSTEM_PROMPT = """你是一个在用户电脑终端里工作的编程助手，工作目录就是当前目录。
你每一轮只能做一件事，并且只输出一个 JSON 对象，不要输出任何其他文字：

运行 shell 命令： {"tool": "bash", "command": "ls -la"}
读取文件：       {"tool": "read_file", "path": "main.py"}
写入整个文件：   {"tool": "write_file", "path": "main.py", "content": "文件的完整内容"}
任务完成：       {"tool": "done", "message": "给用户的简短总结"}

工具的执行结果会在下一轮以 [tool] 消息发给你。
写完代码后要真正运行它或运行测试来验证，确认无误后再输出 done。"""


# ---------- 第 1 步：调用模型 ----------

def render(history):
    """把对话历史拼成一段纯文本。claude -p 每次调用都是全新会话，不记得上一轮，
    所以每一轮都要把完整历史重新发一遍——这就是"上下文"。"""
    return "\n\n".join(f"[{m['role']}]\n{m['content']}" for m in history)


def call_model(history):
    proc = subprocess.run(
        ["claude", "-p",
         "--tools", "",                     # 关掉 Claude Code 自带的工具
         "--strict-mcp-config",             # 不加载连接器/MCP，避免无关信息混进上下文
         "--system-prompt", SYSTEM_PROMPT,
         "--output-format", "json"],
        input=render(history), capture_output=True, text=True, timeout=600,
    )
    data = json.loads(proc.stdout)
    if data.get("is_error"):
        raise RuntimeError(f"模型调用失败：{data.get('result')}")
    return data["result"]


# ---------- 第 2 步：解析模型输出 ----------

def parse_action(text):
    """模型偶尔会在 JSON 外面包一层 ```json ... ``` 或多说一句话，
    所以取第一个 { 到最后一个 } 之间的内容来解析。失败就返回 None。"""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


# ---------- 第 3 步：执行工具 ----------

def run_tool(action):
    tool = action.get("tool")
    try:
        if tool == "bash":
            p = subprocess.run(action["command"], shell=True,
                               capture_output=True, text=True, timeout=120)
            output = (p.stdout + p.stderr)[-5000:]  # 输出太长只保留结尾，省上下文
            return f"exit code: {p.returncode}\n{output}"
        if tool == "read_file":
            with open(action["path"], encoding="utf-8") as f:
                return f.read()[:20000]
        if tool == "write_file":
            path = action["path"]
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(action["content"])
            return f"已写入 {path}（{len(action['content'])} 个字符）"
        return f"未知工具：{tool}"
    except Exception as e:
        # 出错不崩溃，而是把错误当作工具输出交还给模型，让它自己想办法
        return f"工具执行出错：{type(e).__name__}: {e}"


def confirm(action):
    """人在回路（human in the loop）：执行前先问你。设置 YOLO=1 可跳过确认。"""
    if os.environ.get("YOLO") == "1":
        return True
    return input("  执行吗？[y/N] ").strip().lower() == "y"


def describe(action):
    if action.get("tool") == "bash":
        return f"bash: {action.get('command')}"
    if action.get("tool") == "write_file":
        return f"write_file: {action.get('path')}"
    return f"{action.get('tool')}: {action.get('path', '')}"


# ---------- 主循环：把上面三步串起来 ----------

def main():
    task = " ".join(sys.argv[1:]) or input("任务：")
    history = [{"role": "user", "content": task}]

    for turn in range(1, MAX_TURNS + 1):
        reply = call_model(history)
        history.append({"role": "assistant", "content": reply})

        action = parse_action(reply)
        if action is None:
            print(f"[第 {turn} 轮] 模型输出格式不对，提醒它重来")
            history.append({"role": "tool", "content": "格式错误：只能输出一个 JSON 对象。"})
            continue

        if action.get("tool") == "done":
            print(f"\n完成：{action.get('message')}")
            return

        print(f"[第 {turn} 轮] {describe(action)}")
        result = run_tool(action) if confirm(action) else "用户拒绝执行这个操作，换个办法。"
        print("  " + result[:300].replace("\n", "\n  "))
        history.append({"role": "tool", "content": result})
        print(f"  [上下文] 当前历史共{len(render(history))} 个字符")

    print(f"\n达到最大轮数 {MAX_TURNS}，停止。")


if __name__ == "__main__":
    main()
