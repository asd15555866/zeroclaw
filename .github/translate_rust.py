#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 自动翻译 ZeroClaw Rust 源码中的 UI 文本为中文。

不硬编码——按 Rust 属性自动提取并翻译：
  - help: "..."        → sections.rs 里的面板描述
  - #[group = "..."]   → schema.rs 里的侧边栏分组名
  - /// 文档注释        → schema.rs 里的字段描述
"""

import re, os, sys

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(__file__)))

# ====== 已知翻译字典（属性 → 中文） ======
WORD_DICT = {
    # ── group 标签 ──
    "Foundation": "基础",
    "Storage": "存储",
    "Sessions": "会话",
    "Tools": "工具",
    "Operations": "运维",
    "Security": "安全",
    "Other": "其他",
    "Agent": "智能体",
    "Reporting": "报告",
    "Orchestration": "编排",
    "Multimodal": "多模态",
    "Locales": "语言区域",
    "FileTransfer": "文件传输",

    # ── 常见词组 ──
    "Model providers": "模型提供商",
    "Model routes": "模型路由",
    "Embedding routes": "嵌入路由",
    "Risk profiles": "风险配置",
    "Runtime profiles": "运行时配置",
    "Memory": "记忆",
    "Skills": "技能",
    "Skill bundles": "技能集",
    "MCP": "MCP",
    "MCP servers": "MCP 服务器",
    "MCP bundles": "MCP 服务集",
    "Knowledge bundles": "知识库集",
    "TTS providers": "语音合成",
    "Transcription providers": "语音识别",
    "Channels": "频道",
    "Hardware": "硬件",
    "Agents": "智能体",
    "Peer groups": "同伴组",
    "Tunnel": "隧道",
    "Cron": "定时任务",
    "Backup": "备份",
    "Cloud ops": "云端运维",
    "Conversational ai": "对话 AI",
    "Cost": "费用",
    "Data retention": "数据保留",
    "Eval": "评估",
    "Heartbeat": "心跳",
    "Hooks": "钩子",
    "Observability": "可观测性",
    "Onboard state": "首次设置状态",
    "Peripherals": "外设",
    "SOP approval": "SOP 审批",
    "Escalation": "升级通知",
    "Unattended upgrades": "自动升级",
    "Trust": "信任",
    "Pipeline": "管线",
    "Pacing": "限速",
    "Locales": "区域设置",
    "Lifestate": "生命周期",
    "File download": "文件下载",
    "File upload": "文件上传",
    "File upload bundle": "文件上传集",
    "Query classification": "查询分类",
    "Reliability": "可靠性",
    
    # ── 常用 tech 词 ──
    "configuration": "配置",
    "settings": "设置",
    "tool": "工具",
    "backend": "后端",
    "provider": "提供商",
    "model": "模型",
    "agent": "智能体",
    "channel": "频道",
    "skill": "技能",
    "bundle": "集",
    "profile": "配置",
    "group": "分组",
    "endpoint": "端点",
    "source": "来源",
    "target": "目标",
    "server": "服务器",
    "Auto-update": "自动更新",
    "Cooldown": "冷却",
    "Enable": "启用",
    "Disable": "禁用",
    "Maximum": "最大",
    "Minimum": "最小",
    "Interval": "间隔",
    "Timeout": "超时",
    "Threshold": "阈值",
    "Limit": "限制",
    "Rate": "速率",
    "Delay": "延迟",
    "Retry": "重试",
    "Compression": "压缩",
    "Retention": "保留",
    "Persistence": "持久化",
    "Token": "令牌",
    "Sandbox": "沙箱",
    "Sandboxing": "沙箱化",
    "Browser": "浏览器",
    "Gateway": "网关",
    "pairing": "配对",
    "Secret": "密钥",
    "Leak": "泄露",
    "Detection": "检测",
    "Sensitivity": "灵敏度",
    "Escalation": "升级",
    "Notification": "通知",
    "Audit": "审计",
    "Create": "创建",
    "Update": "更新",
    "Delete": "删除",
    "Export": "导出",
    "Import": "导入",
    "Download": "下载",
    "Upload": "上传",
    "Path": "路径",
    "Directory": "目录",
    "URL": "地址",
    "Port": "端口",
    "Host": "主机",
    "Username": "用户名",
    "Password": "密码",
    "File": "文件",
    "String": "字符串",
    "Number": "数字",
    "Boolean": "布尔值",
    "Milliseconds": "毫秒",
    "Seconds": "秒",
    "Minutes": "分钟",
    "Hours": "小时",
    "Days": "天",
    "Bytes": "字节",
    "Date": "日期",
    "Key": "键",
    "Value": "值",
    "Name": "名称",
    "Type": "类型",
    "Single-node": "单节点",
    "Multi-instance": "多实例",
    "Daily": "每日",
    "Monthly": "每月",
    "Warning": "警告",
    "Recovery": "恢复",
    "Storage": "存储",
    "Persistence": "持久化",
    "Concurrent": "并发",
    "Throttle": "限流",
    "Acknowledgment": "确认",
    "Retain": "保留",
    "Unassigned": "未分配",
    "Assigned": "已分配",
    "Peers": "同伴",
    "Persona": "角色",
    "Dispatchable": "可调度",
    "Zero-config": "零配置",
    "Offline": "离线",
    "Started": "已启动",
    "Rolling": "滚动",
    "Wildcard": "通配符",
    "Allowlists": "白名单",
    "Denylists": "黑名单",
    "Approval": "审批",
    "Vector": "向量",
    "Markdown": "Markdown",
    "Human-readable": "可读",
    "Auto-update": "自动更新",
    "Periodic": "周期",
    "Security": "安全",
    "Identity": "身份",
    "Alert": "警报",
    "Standard Operating Procedure": "标准操作流程",
    "SOP": "SOP",
    "Classification": "分类",
    "Prometheus": "Prometheus",
    "OpenTelemetry": "OpenTelemetry",
    "Traces": "追踪",
    "Metrics": "指标",
    "SQLite": "SQLite",
    "Postgres": "Postgres",
    "Qdrant": "Qdrant",
    "Lucid": "Lucid",
    "Multimodal": "多模态",
    "Transcription": "转录",
    "Text-to-speech": "文字转语音",
    "Speech-to-text": "语音转文字",
    "Anthropic": "Anthropic",
    "OpenAI": "OpenAI",
    "OpenRouter": "OpenRouter",
    "Ollama": "Ollama",
    "ElevenLabs": "ElevenLabs",
    "Google": "Google",
    "Edge": "Edge",
    "Piper": "Piper",
    "Groq": "Groq",
    "Deepgram": "Deepgram",
    "AssemblyAI": "AssemblyAI",
    "Whisper": "Whisper",
    "Arduino": "Arduino",
    "STM32": "STM32",
    "GPIO": "GPIO",
    "WebAssembly": "WebAssembly",
    "WASM": "WASM",
    "WebSocket": "WebSocket",
}


def lookup_phrase(phrase):
    """把常见英文词组替换成中文"""
    words = phrase.split()
    result = []
    for w in words:
        clean = w.strip('.,!?;:()[]{}')
        if clean in WORD_DICT:
            result.append(WORD_DICT[clean])
        else:
            result.append(w)
    return ' '.join(result)


def translate_help_string(content):
    """翻译 sections.rs 中 help: '...' 里的文字"""
    def replace_help(m):
        indent = m.group(1)
        text = m.group(2)
        # 逐行处理
        lines = text.split('\n')
        lines = [lookup_phrase(l.strip()) for l in lines]
        new_text = '\n'.join(f'{indent}    {l}' for l in lines)
        return f'{indent}help:  {new_text},'
    
    # 匹配 help:  "..." 或 help:  "..."\n  "..." 模式(续行)
    pattern = re.compile(r'(\s*)help:\s+(".*?")\s*,', re.DOTALL)
    result = pattern.sub(replace_help, content)
    return result


def translate_group_attr(content):
    """翻译 schema.rs 中 #[group = "xxx"] 里的分组名"""
    def replace_group(m):
        before = m.group(1)
        label = m.group(2)
        if label in WORD_DICT:
            return f'{before}"{WORD_DICT[label]}"'
        return m.group(0)
    
    return re.sub(r'(group\s*=\s*)"([^"]+)"', replace_group, content)


def translate_doc_comment(content):
    """翻译 schema.rs 里 /// 文档注释"""
    def replace_doc(m):
        text = m.group(1).strip()
        if text and re.search(r'[a-zA-Z]{5,}', text):
            return f'/// {lookup_phrase(text)}'
        return m.group(0)
    
    return re.sub(r'/// (.+)', replace_doc, content)


def translate_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    if 'sections.rs' in filepath:
        content = translate_help_string(content)
    
    if 'schema.rs' in filepath:
        content = translate_group_attr(content)
        content = translate_doc_comment(content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    targets = [
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'sections.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'schema.rs'),
    ]

    done = 0
    for fp in targets:
        if translate_file(fp):
            done += 1
            print(f"[TRANSLATED] {os.path.basename(fp)}")
        else:
            print(f"[NO-CHANGE] {os.path.basename(fp)}")

    print(f"\nDone: {done}/{len(targets)} translated.")
    if done == 0:
        print("WARN: No translations applied. Check pattern matching.")

if __name__ == "__main__":
    main()
