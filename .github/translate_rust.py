#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions: 扫描 crates/ 下全部 .rs 文件，按属性翻译 UI 文本。

翻译策略：
  - 单词/词组属性（label, group, hint, display_name, category）→ 字典逐词
  - 长句属性（help:, ///, description =）→ 跳过字典，整句交给 AI 翻译
"""

import re, os, sys, glob

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 单字段名 / 词组 字典（用于 label/hint/group/display_name/category）
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

    # ── display_name / hint / 单词 ──
    "Browser": "浏览器","Shell": "Shell","Email": "邮件",
    "Docker": "Docker","Calculator": "计算器","Database": "数据库",
    "HTTP Client": "HTTP 客户端",
    "WebSearch": "网页搜索","ImageGeneration": "图片生成",
    "TextToSpeech": "文字转语音","AudioTranscription": "语音转录",
    "WebScraping": "网页抓取","CodeInterpreter": "代码解释器",
    
    "Locked Down": "严格锁定","YOLO": "无限制",
    "Tight": "紧凑","Local Small": "本地小模型","Unbounded": "无限制",
    
    "reasoning": "推理","fast": "快速","semantic": "语义",
    "vision": "视觉","reliable": "可靠","websearch": "网页搜索",
    
    "Enabled": "已启用","Disabled": "已禁用",
    "Allow": "允许","Deny": "拒绝","Approve": "批准","Edit": "编辑",
    
    "Model providers": "模型提供商","Model routes": "模型路由",
    "Embedding routes": "嵌入路由","Risk profiles": "风险配置",
    "Runtime profiles": "运行时配置","Memory": "记忆",
    "Skills": "技能","Skill bundles": "技能集","MCP": "MCP",
    "MCP servers": "MCP 服务器","MCP bundles": "MCP 服务集",
    "Knowledge bundles": "知识库集","TTS providers": "语音合成",
    "Transcription providers": "语音识别","Channels": "频道",
    "Hardware": "硬件","Agents": "智能体","Peer groups": "同伴组",
    "Tunnel": "隧道","Cron": "定时任务","Backup": "备份",
    "Cloud ops": "云端运维","Cost": "费用","Heartbeat": "心跳",
    "Hooks": "钩子","Observability": "可观测性","Peripherals": "外设",
    "Trust": "信任","Pipeline": "管线","Pacing": "限速",
    "Escalation": "升级通知","Reliability": "可靠性",
    "File download": "文件下载","File upload": "文件上传",
    
    "OpenAI": "OpenAI","Anthropic": "Anthropic",
    "Ollama": "Ollama","Prometheus": "Prometheus",
    "OpenTelemetry": "OpenTelemetry","SQLite": "SQLite",
    "Postgres": "Postgres","Qdrant": "Qdrant",
    "Markdown": "Markdown","WebSocket": "WebSocket",
    "Telegram": "Telegram","Discord": "Discord",
    "MQTT": "MQTT","WeChat": "微信",
    
    # 在字段描述中只翻译单字段路径的标识符
    "advanced": "高级","Enabled": "已启用","Disable": "禁用",
}


def translate_word(text):
    """仅替换完整单词（用于单字段名）"""
    if not text:
        return text
    
    result = text
    for en, zh in sorted(DICT.items(), key=lambda x: -len(x[0])):
        # 整词替换（单词边界）
        if ' ' in en:
            if en in result:
                result = result.replace(en, zh)
        else:
            # 单单词：完整匹配
            pattern = re.compile(r'\b' + re.escape(en) + r'\b')
            result = pattern.sub(zh, result)
    return result


def translate_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False
    
    original = content
    
    # ── 1. help:  "..." —— 长句，跳过字典，留给 AI ──
    # 不处理，让 ai_translate_fallback.py 处理
    
    # ── 2. label: "..." —— 单字段名，用字典 ──
    if 'label:' in content:
        content = re.sub(
            r'(label:\s+)"([^"]+)"',
            lambda m: f'{m.group(1)}"{translate_word(m.group(2))}"',
            content
        )
    
    # ── 3. #[group = "..."] ──
    if 'group =' in content:
        content = re.sub(
            r'(group\s*=\s*)"([^"]+)"',
            lambda m: f'{m.group(1)}"{DICT.get(m.group(2), m.group(2))}"',
            content
        )
    
    # ── 4. /// doc comment —— 长句描述，不处理，留给 AI ──
    # 不处理，让 ai_translate_fallback.py 处理
    
    # ── 5. display_name / category (短值) ──
    for attr in ['display_name', 'category']:
        if attr + ' =' in content:
            content = re.sub(
                rf'({attr}\s*=\s*)"([^"]+)"',
                lambda m: f'{m.group(1)}"{DICT.get(m.group(2), m.group(2))}"',
                content
            )
    
    # ── 6. description = "..." (短) / hint = "..." ──
    # 短值（≤ 5个单词）才用字典；长句留给 AI
    if 'hint =' in content or 'description =' in content:
        for attr in ['hint', 'description']:
            pattern = re.compile(rf'({attr}\s*=\s*)"([^"]{{1,80}})"')
            def smart_repl(m, attr_name=attr):
                val = m.group(2)
                if ' ' in val or len(val) > 30:
                    # 长句让 AI 翻译
                    return m.group(0)
                return f'{m.group(1)}"{DICT.get(val, val)}"'
            content = pattern.sub(smart_repl, content)
    
    # ── 7. description: Some("...") —— gateway 选项 ──
    if 'description:' in content:
        content = re.sub(
            r'(description:\s*Some\()"([^"]+)"',
            lambda m: f'{m.group(1)}"{DICT.get(m.group(2), translate_word(m.group(2)))}"',
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
    
    print(f"\nTranslated: {done}/{len(rs_files)} files (字典)")
    print("Long sentences (help:, ///) skipped - handled by AI step")

if __name__ == "__main__":
    main()