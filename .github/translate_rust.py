#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 自动翻译 ZeroClaw Rust 源码中的 UI 文本为中文。

扫描整个 crates/ 目录，按以下模式提取并翻译：
  1. help:  "..."             → 面板帮助文本 (sections.rs, presets.rs)
  2. label: "..."             → 预设标签 (presets.rs)
  3. #[group = "..."]         → 侧边栏分组名 (schema.rs)
  4. /// 文档注释               → 结构体/字段描述 (schema.rs)
  5. #[display_name = "..."]  → 集成显示名 (schema.rs)
  6. #[description = "..."]   → 集成描述 (schema.rs)
  7. #[strum(serialize = "...")] → 枚举标签
  8. pub struct/enum 的 /// 注释
"""

import re, os, sys, glob

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ====== 翻译字典 ======
DICT = {
    # ── group 标签 ──
    "Foundation": "基础", "Storage": "存储", "Sessions": "会话",
    "Tools": "工具", "Operations": "运维", "Security": "安全",
    "Other": "其他", "Agent": "智能体", "Reporting": "报告",
    "Orchestration": "编排", "Multimodal": "多模态",
    "Locales": "语言区域", "FileTransfer": "文件传输",
    "Network": "网络", "Multi-agent": "多智能体",

    # ── nav 标签 ──
    "Model providers": "模型提供商", "Model routes": "模型路由",
    "Embedding routes": "嵌入路由", "Risk profiles": "风险配置",
    "Runtime profiles": "运行时配置", "Memory": "记忆",
    "Skills": "技能", "Skill bundles": "技能集", "MCP": "MCP",
    "MCP servers": "MCP 服务器", "MCP bundles": "MCP 服务集",
    "Knowledge bundles": "知识库集", "TTS providers": "语音合成",
    "Transcription providers": "语音识别", "Channels": "频道",
    "Hardware": "硬件", "Agents": "智能体", "Peer groups": "同伴组",
    "Tunnel": "隧道", "Cron": "定时任务", "Backup": "备份",
    "Cloud ops": "云端运维", "Conversational ai": "对话 AI",
    "Cost": "费用", "Data retention": "数据保留", "Eval": "评估",
    "Heartbeat": "心跳", "Hooks": "钩子", "Observability": "可观测性",
    "Onboard state": "首次设置", "Peripherals": "外设",
    "SOP approval": "SOP 审批", "Escalation": "升级通知",
    "Unattended upgrades": "自动升级", "Trust": "信任",
    "Pipeline": "管线", "Pacing": "限速", "Lifestate": "生命周期",
    "File download": "文件下载", "File upload": "文件上传",
    "File upload bundle": "文件上传集", "Query classification": "查询分类",
    "Reliability": "可靠性", "Cost ops": "费用控制",
    "Runtime": "运行时", "Gateway": "网关",
    "Companion network peers": "同伴网络节点",

    # ── display_name ──
    "Browser": "浏览器", "Shell": "Shell", "FileSystem": "文件系统",
    "CodeInterpreter": "代码解释器", "WebSearch": "网页搜索",
    "ImageGeneration": "图片生成", "AudioTranscription": "语音转录",
    "TextToSpeech": "文字转语音", "WebScraping": "网页抓取",
    "Email": "邮件", "Calculator": "计算器",
    "Database": "数据库", "HTTP Client": "HTTP 客户端",

    # ── description ──
    "Chrome/Chromium control": "Chrome/Chromium 控制",
    "Execute shell commands": "执行 Shell 命令",
    "Read and write files": "读写文件",
    "Run Python code in a sandbox": "在沙箱中运行 Python 代码",
    "Search the web": "搜索互联网",
    "Generate images using AI": "使用 AI 生成图片",
    "Transcribe audio files": "转录音频文件",
    "Convert text to speech": "文字转语音",
    "Extract data from websites": "从网站提取数据",
    "Send emails": "发送邮件",
    "Perform calculations": "执行计算",
    "Run SQL queries": "执行 SQL 查询",
    "Make HTTP requests": "发送 HTTP 请求",
    "Unattended-upgrade configuration": "自动升级配置",
    "Translation engine configuration": "翻译引擎配置",
    "File upload bundle tool configuration": "文件上传集工具配置",
    "Latency and timeout configuration": "延迟和超时配置",
    "Task classification configuration": "任务分类配置",
    "Command-line session recording configuration": "命令行录制配置",
    "Observability configuration": "可观测性配置",
    "State management configuration": "状态管理配置",
    "Auto-install configuration": "自动安装配置",
    "Evaluation harness configuration": "评估框架配置",
    "Cloud operations configuration": "云端运维配置",
    "Cost management configuration": "费用管理配置",
    "Policy-based data retention": "基于策略的数据保留",
    "Unattended upgrade configuration": "自动升级配置",

    # ── 词组 ──
    "Pick a model provider to configure": "选择一个模型提供商进行配置",
    "Multiple aliases per": "每个提供商支持多个别名",
    "are supported": "支持",
    "can coexist": "可共存",
    "Named model routing hints": "命名的模型路由提示",
    "Each route maps": "每个路由映射",
    "Use `hint:<name>`": "使用 `hint:<name>`",
    "Named embedding routing hints": "命名的嵌入路由提示",
    "Named risk profiles binding": "命名的风险配置文件",
    "Named runtime tuning profiles": "命名的运行时调优配置",
    "SQLite is the safe default": "SQLite 是安全默认",
    "Pick Postgres for shared": "共享部署请选 Postgres",
    "Qdrant for vector search": "向量搜索用 Qdrant",
    "Persistent memory backend": "持久化记忆后端",
    "Skills tool settings": "技能工具设置",
    "Add skill BUNDLES under": "在下方添加技能集",
    "Named bundles of skill files": "命名的技能文件集",
    "Model Context Protocol settings": "模型上下文协议设置",
    "Named bundles of MCP servers": "命名的 MCP 服务集",
    "Named bundles of knowledge sources": "命名的知识源集",
    "Text-to-speech providers": "文字转语音提供商",
    "Speech-to-text providers": "语音转文字提供商",
    "Pick which chat platforms": "选择监听的聊天平台",
    "Optional: hardware peripherals": "可选：硬件外设",
    "mutual opt-in": "双向确认",
    "Scheduled tasks": "定时任务",

    # ── 单词 ──
    "configuration": "配置", "settings": "设置", "tool": "工具",
    "backend": "后端", "provider": "提供商", "model": "模型",
    "agent": "智能体", "channel": "频道", "skill": "技能",
    "bundle": "集", "profile": "配置", "group": "分组",
    "endpoint": "端点", "source": "来源", "target": "目标",
    "server": "服务器", "storage": "存储", "memory": "记忆",
    "backup": "备份", "monitoring": "监控", "logging": "日志",
    "sandbox": "沙箱", "browser": "浏览器", "gateway": "网关",
    "pairing": "配对", "notification": "通知", "audit": "审计",
    "evaluation": "评估", "pipeline": "管线", "pacing": "限速",
    "heartbeat": "心跳", "hooks": "钩子", "cron": "定时任务",
    "download": "下载", "upload": "上传", "export": "导出",
    "import": "导入", "create": "创建", "delete": "删除",
    "update": "更新", "enable": "启用", "disable": "禁用",
    "allowed": "允许", "denied": "禁止", "require": "需要",
    "optional": "可选", "default": "默认", "custom": "自定义",
    "secret": "密钥", "token": "令牌", "password": "密码",
    "key": "键", "value": "值", "path": "路径", "host": "主机",
    "port": "端口", "url": "地址", "name": "名称", "type": "类型",
    "file": "文件", "directory": "目录", "folder": "文件夹",
    "string": "字符串", "number": "数字", "boolean": "布尔",
    "timeout": "超时", "interval": "间隔", "delay": "延迟",
    "retry": "重试", "limit": "限制", "threshold": "阈值",
    "maximum": "最大", "minimum": "最小", "rate": "速率",
    "compression": "压缩", "retention": "保留", "persistence": "持久化",
    "concurrent": "并发", "dispatch": "调度", "scheduling": "调度",
    "identity": "身份", "trust": "信任", "escalation": "升级",
    "recovery": "恢复", "detection": "检测",
    "seconds": "秒", "minutes": "分钟", "hours": "小时",
    "days": "天", "bytes": "字节", "milliseconds": "毫秒",
    "single-node": "单节点", "multi-instance": "多实例",
    "file-based": "基于文件", "zero-config": "零配置",
    "human-readable": "可读文件", "vector": "向量",
    "SQLite": "SQLite", "Postgres": "Postgres",
    "Qdrant": "Qdrant", "Markdown": "Markdown",
    "Lucid": "Lucid", "MCP": "MCP", "SOP": "SOP",
    "WASM": "WASM", "WebAssembly": "WebAssembly",
    "WebSocket": "WebSocket", "HTTP": "HTTP", "CLI": "CLI",
    "API": "API", "JSON": "JSON", "YAML": "YAML",
    "OpenAI": "OpenAI", "Anthropic": "Anthropic",
    "Ollama": "Ollama", "Prometheus": "Prometheus",
    "OpenTelemetry": "OpenTelemetry", "WeChat": "微信",
    "Telegram": "Telegram", "Discord": "Discord",
    "Email": "邮件", "MQTT": "MQTT",
}


def translate_text(text):
    """用字典逐词+词组翻译一段英文"""
    if not text or not re.search(r'[a-zA-Z]{3,}', text):
        return text
    
    result = text
    
    # 词组优先
    sorted_phrases = sorted(DICT.items(), key=lambda x: -len(x[0]))
    for en, zh in sorted_phrases:
        if ' ' in en and en in result:
            result = result.replace(en, zh)
    
    # 单词
    words = result.split()
    translated = []
    for w in words:
        stripped = w.rstrip('.,!?;:()[]{}')
        suffix = w[len(stripped):]
        clean = stripped.strip()
        if clean in DICT:
            translated.append(DICT[clean] + suffix)
        else:
            translated.append(w)
    
    return ' '.join(translated)


def translate_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False

    original = content
    basename = os.path.basename(filepath)

    # === 1. sections.rs: help:  "..." ===
    if basename in ('sections.rs', 'presets.rs'):
        def repl_help(m):
            return f'{m.group(1)}help:  "{translate_text(m.group(2))}",'
        content = re.sub(r'(help:\s+)"(.*?)"\s*,', repl_help, content, flags=re.DOTALL)

    # === 2. presets.rs: label: "..." ===
    if basename == 'presets.rs':
        def repl_label(m):
            return f'{m.group(1)}label: "{translate_text(m.group(2))}",'
        content = re.sub(r'(label:\s+)"(.*?)"\s*,', repl_label, content)

    # === 3. schema.rs: #[group = "..."] ===
    if basename == 'schema.rs':
        def repl_group(m):
            label = m.group(2)
            return f'{m.group(1)}"{DICT.get(label, label)}"'
        content = re.sub(r'(group\s*=\s*)"([^"]+)"', repl_group, content)

    # === 4. schema.rs: /// doc comment ===
    if basename == 'schema.rs':
        def repl_doc(m):
            t = m.group(1).strip()
            return f'/// {translate_text(t)}' if re.search(r'[a-zA-Z]{5,}', t) else m.group(0)
        content = re.sub(r'/// (.+)', repl_doc, content)

    # === 5. 所有 .rs: #[display_name = "..."] / #[description = "..."] ===
    for attr in ['display_name', 'description']:
        def make_repl(attr_name):
            return lambda m: f'{m.group(1)}"{translate_text(m.group(2))}"'
        content = re.sub(
            rf'({attr}\s*=\s*)"([^"]+)"',
            make_repl(attr),
            content
        )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    # 扫描所有 .rs 文件
    crates_dir = os.path.join(WORKSPACE, 'crates')
    rs_files = glob.glob(os.path.join(crates_dir, '**', '*.rs'), recursive=True)

    # 优先处理最重要的文件
    priority = [
        os.path.join(crates_dir, 'zeroclaw-config', 'src', 'sections.rs'),
        os.path.join(crates_dir, 'zeroclaw-config', 'src', 'presets.rs'),
        os.path.join(crates_dir, 'zeroclaw-config', 'src', 'schema.rs'),
    ]
    other = [f for f in rs_files if f not in priority]

    total = 0
    for fp in priority + other:
        if translate_file(fp):
            total += 1
            rel = fp.replace(WORKSPACE + os.sep, '')
            print(f"  [OK] {rel}")

    print(f"\nTranslated: {total}/{len(rs_files)} files.")

if __name__ == "__main__":
    main()
