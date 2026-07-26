#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions: 扫描 crates/ 下全部 .rs 文件，按属性翻译用户可见 UI 文本。

翻译属性:
  1. help:  "..."                        → 面板帮助文本
  2. label: "..." 或 label: "..."        → 按钮/预设标签
  3. #[group = "..."]                    → 侧边栏分组名
  4. /// 文档注释                          → 字段/结构体描述
  5. #[display_name = "..."]             → 集成显示名
  6. #[description = "..."]              → 集成描述
  7. #[integration(category = "...")]     → 分类名
  8. hint = "..."  (在配置字段中)          → 路由提示
  9. #[strum(serialize = "...")]          → 枚举标签
"""

import re, os, sys, glob

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DICT = {
    # ── group ──
    "Foundation": "基础","Storage": "存储","Sessions": "会话",
    "Tools": "工具","Operations": "运维","Security": "安全",
    "Other": "其他","Agent": "智能体","Reporting": "报告",
    "Orchestration": "编排","Multimodal": "多模态",
    "Locales": "区域设置","FileTransfer": "文件传输",
    "Network": "网络","Multi-agent": "多智能体",

    # ── category ──
    "ToolsAutomation": "工具与自动化","ChatPlatform": "聊天平台",
    "AIModel": "AI 模型","PlatformService": "平台服务",
    "All": "全部","DeveloperTool": "开发者工具",
    "FileSystem": "文件系统","MessagePlatform": "消息平台",
    "VoiceAudio": "语音音频","HardwarePeripheral": "硬件外设",
    "DevTool": "开发者工具","WebBrowser": "网页浏览器",
    "Code": "代码","Search": "搜索","Media": "媒体",

    # ── display_name / label / hint ──
    "Locked Down": "严格锁定","Balanced": "均衡","YOLO": "无限制",
    "Tight": "紧凑","Local Small": "本地小模型","Unbounded": "无限制",
    "Browser": "浏览器","Shell": "Shell","FileSystem": "文件系统",
    "CodeInterpreter": "代码解释器","WebSearch": "网页搜索",
    "ImageGeneration": "图片生成","AudioTranscription": "语音转录",
    "TextToSpeech": "文字转语音","WebScraping": "网页抓取",
    "Email": "邮件","Calculator": "计算器","Database": "数据库",
    "HTTP Client": "HTTP 客户端","Docker": "Docker",
    "reasoning": "推理","fast": "快速","semantic": "语义",
    "vision": "视觉","reliable": "可靠",
    "Approve": "批准","Deny": "拒绝",
    "Edit": "编辑","Revise": "修订",
    "Guidance for the re-draft": "修改指导意见",
    "none": "无","Original": "原始","Revised": "修订版",
    "pass": "通过","fail": "失败",

    # ── nav ──
    "Model providers": "模型提供商","Model routes": "模型路由",
    "Embedding routes": "嵌入路由","Risk profiles": "风险配置",
    "Runtime profiles": "运行时配置","Memory": "记忆",
    "Skills": "技能","Skill bundles": "技能集","MCP": "MCP",
    "MCP servers": "MCP 服务器","MCP bundles": "MCP 服务集",
    "Knowledge bundles": "知识库集","TTS providers": "语音合成",
    "Transcription providers": "语音识别","Channels": "频道",
    "Hardware": "硬件","Agents": "智能体","Peer groups": "同伴组",
    "Tunnel": "隧道","Cron": "定时任务","Backup": "备份",
    "Cloud ops": "云端运维","Conversational ai": "对话 AI",
    "Cost": "费用","Data retention": "数据保留","Eval": "评估",
    "Heartbeat": "心跳","Hooks": "钩子","Observability": "可观测性",
    "Onboard state": "首次设置","Peripherals": "外设",
    "SOP approval": "SOP 审批","Escalation": "升级通知",
    "Unattended upgrades": "自动升级","Trust": "信任",
    "Pipeline": "管线","Pacing": "限速","Lifestate": "生命周期",
    "File download": "文件下载","File upload": "文件上传",
    "File upload bundle": "文件上传集","Query classification": "查询分类",
    "Reliability": "可靠性","Cost ops": "费用控制",
    "Runtime": "运行时","Gateway": "网关",
    "Companion network peers": "同伴网络节点",

    # ── 词组 (长句中的常见部分) ──
    "Pick a model provider to configure": "选择一个模型提供商进行配置",
    "Multiple aliases per provider are supported": "每个提供商支持多个别名",
    "Named model routing hints": "命名的模型路由提示",
    "Each route maps a hint to a specific provider": "每个路由将提示映射到特定的提供商",
    "Use `hint:<name>` as the model parameter": "使用 `hint:<name>` 作为模型参数",
    "Named embedding routing hints": "命名的嵌入路由提示",
    "Named risk profiles binding allowlists": "命名的风险配置文件",
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
    "Scheduled tasks": "定时任务",
    "Localhost only": "仅本机",
    "no public tunnel": "无公网隧道",
    "Node capability definitions": "节点能力定义",

    # ── 单词 ──
    "configuration": "配置","settings": "设置","tool": "工具",
    "backend": "后端","provider": "提供商","model": "模型",
    "agent": "智能体","channel": "频道","skill": "技能",
    "bundle": "集","profile": "配置","group": "分组",
    "endpoint": "端点","source": "来源","target": "目标",
    "server": "服务器","storage": "存储","memory": "记忆",
    "backup": "备份","monitoring": "监控","logging": "日志",
    "sandbox": "沙箱","browser": "浏览器","gateway": "网关",
    "pairing": "配对","notification": "通知","audit": "审计",
    "evaluation": "评估","pipeline": "管线","pacing": "限速",
    "heartbeat": "心跳","hooks": "钩子","cron": "定时任务",
    "download": "下载","upload": "上传","export": "导出",
    "import": "导入","create": "创建","delete": "删除",
    "update": "更新","enable": "启用","disable": "禁用",
    "allowed": "允许","denied": "禁止","require": "需要",
    "optional": "可选","default": "默认","custom": "自定义",
    "secret": "密钥","token": "令牌","password": "密码",
    "key": "键","value": "值","path": "路径","host": "主机",
    "port": "端口","url": "地址","name": "名称","type": "类型",
    "file": "文件","directory": "目录","folder": "文件夹",
    "string": "字符串","number": "数字","boolean": "布尔",
    "timeout": "超时","interval": "间隔","delay": "延迟",
    "retry": "重试","limit": "限制","threshold": "阈值",
    "maximum": "最大","minimum": "最小","rate": "速率",
    "compression": "压缩","retention": "保留","persistence": "持久化",
    "concurrent": "并发","dispatch": "调度","scheduling": "调度",
    "identity": "身份","trust": "信任","escalation": "升级",
    "recovery": "恢复","detection": "检测",
    "seconds": "秒","minutes": "分钟","hours": "小时",
    "days": "天","bytes": "字节","milliseconds": "毫秒",
    "single-node": "单节点","multi-instance": "多实例",
    "file-based": "基于文件","zero-config": "零配置",
    "human-readable": "可读", "vector": "向量",
    "SQLite": "SQLite","Postgres": "Postgres",
    "Qdrant": "Qdrant","Markdown": "Markdown",
    "Lucid": "Lucid","WASM": "WASM","HTTP": "HTTP",
    "CLI": "CLI","API": "API","JSON": "JSON",
    "OpenAI": "OpenAI","Anthropic": "Anthropic",
    "Ollama": "Ollama","Prometheus": "Prometheus",
    "OpenTelemetry": "OpenTelemetry",
    "Telegram": "Telegram","Discord": "Discord",
    "MQTT": "MQTT","WeChat": "微信",
    "Arduino": "Arduino","STM32": "STM32","GPIO": "GPIO",
}


def translate_text(text):
    """逐词 + 词组替换"""
    if not text or not re.search(r'[a-zA-Z]{3,}', text):
        return text
    
    result = text
    for en, zh in sorted(DICT.items(), key=lambda x: -len(x[0])):
        if ' ' in en and en in result:
            result = result.replace(en, zh)
    
    words = result.split()
    out = []
    for w in words:
        s = w.rstrip('.,!?;:()[]{}')
        sfx = w[len(s):]
        out.append(DICT.get(s.strip(), s) + sfx)
    
    return ' '.join(out)


def translate_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False
    
    original = content
    
    # ── 1. help:  "..." ── (sections.rs, presets.rs)
    if 'help:' in content:
        content = re.sub(
            r'(help:\s+)"(.*?)"\s*,',
            lambda m: f'{m.group(1)}"{translate_text(m.group(2))}",',
            content, flags=re.DOTALL
        )
    
    # ── 2. label: "..." ── (all .rs: presets, runtime labels, gateway)
    if 'label:' in content:
        content = re.sub(
            r'(label:\s+)"(.*?)"\s*,',
            lambda m: f'{m.group(1)}"{translate_text(m.group(2))}",',
            content
        )
    
    # ── 3. #[group = "..."] ── (schema.rs)
    if 'group =' in content:
        content = re.sub(
            r'(group\s*=\s*)"([^"]+)"',
            lambda m: f'{m.group(1)}"{DICT.get(m.group(2), m.group(2))}"',
            content
        )
    
    # ── 4. /// doc comment ── (schema.rs — long English only)
    if '///' in content:
        content = re.sub(
            r'/// (.+)',
            lambda m: f'/// {translate_text(m.group(1))}' if re.search(r'[a-zA-Z]{10,}', m.group(1)) else m.group(0),
            content
        )
    
    # ── 5. display_name / description / category ── (all .rs)
    for attr in ['display_name', 'description', 'category']:
        if attr + ' =' in content:
            content = re.sub(
                rf'({attr}\s*=\s*)"([^"]+)"',
                lambda m: f'{m.group(1)}"{DICT.get(m.group(2), translate_text(m.group(2)))}"',
                content
            )
    
    # ── 6. hint = "..." ── (schema.rs 字段提示)
    if 'hint =' in content:
        content = re.sub(
            r'(hint\s*=\s*)"([^"]+)"',
            lambda m: f'{m.group(1)}"{DICT.get(m.group(2), m.group(2))}"',
            content
        )
    
    # ── 7. description: Some("...") ── (gateway api_sections)
    if 'description:' in content:
        content = re.sub(
            r'(description:\s*Some\()"([^"]+)"',
            lambda m: f'{m.group(1)}"{translate_text(m.group(2))}"',
            content
        )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    rs_files = glob.glob(os.path.join(WORKSPACE, 'crates', '**', '*.rs'), recursive=True)
    
    done = 0
    for fp in sorted(rs_files):
        if translate_file(fp):
            done += 1
            rel = fp.replace(WORKSPACE + os.sep, '')
            print(f"  [OK] {rel}")
    
    print(f"\nTranslated: {done}/{len(rs_files)} files")

if __name__ == "__main__":
    main()
