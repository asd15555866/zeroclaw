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

    # ── 工具名映射（用户可见的工具名）──
    "shell": "shell终端","file_read": "读文件","file_write": "写文件",
    "file_edit": "编辑文件","file_download": "下载文件","file_upload": "上传文件",
    "file_upload_bundle": "文件上传集","filesystem": "文件系统",
    "glob_search": "glob搜索","content_search": "内容搜索",
    "cron_add": "添加定时任务","cron_list": "列出定时任务",
    "cron_remove": "删除定时任务","cron_update": "更新定时任务",
    "cron_run": "运行定时任务","cron_runs": "定时任务历史",
    "memory_store": "存储记忆","memory_recall": "召回记忆",
    "memory_forget": "遗忘记忆","memory_export": "导出记忆",
    "memory_purge": "清理记忆","query_echo": "查询回显",
    "schedule": "计划任务","send_message_to_peer": "发送同伴消息",
    "model_routing_config": "模型路由配置","model_switch_trigger": "模型切换触发",
    "child_model_switch": "子模型切换",
    "todo_write": "写待办",
    "sop_execute": "执行SOP","sop_list": "列出SOP","sop_status": "SOP状态",
    "sop_advance": "推进SOP","sop_approve": "审批SOP","sop_workshop": "SOP编辑器",
    "read_skill": "读技能","skill_manage": "管理技能","skills_list": "技能列表",
    "skill_view": "查看技能","skill_tool": "技能工具","tool_search": "搜索工具",
    "skill_http":"技能HTTP","skill_verify":"验证技能",
    "security_ops": "安全操作","safety": "安全检查",
    "ask_user": "询问用户","escalate_to_human": "转人工",
    "browser": "浏览器","browser_open": "打开浏览器","browser_delegate": "浏览器代理",
    "web_fetch": "网页抓取","web_search_tool": "网页搜索",
    "screenshot": "截图","text_browser": "文本浏览器",
    "http_request": "HTTP请求","proxy_config": "代理配置",
    "calculator": "计算器","datetime": "日期时间",
    "docker": "Docker","postgres": "PostgreSQL","sqlite": "SQLite",
    "qdrant": "Qdrant","prometheus": "Prometheus",
    "git": "Git","git_forge": "Git Forge","github": "GitHub",
    "gitea": "Gitea","jira": "Jira","notion": "Notion",
    "email": "邮件","email_read": "读邮件","email_search": "搜邮件",
    "webhook": "Webhook","broadcast": "广播",
    "canvas": "画布","workspace": "工作区",
    "gpio_read": "GPIO读","gpio_write": "GPIO写",
    "gpio_rpi_blink": "树莓派闪烁","gpio_rpi_read": "树莓派读",
    "gpio_rpi_write": "树莓派写","gpio_aardvark": "Aardvark",
    "i2c_read": "I2C读","i2c_scan": "I2C扫描","i2c_write": "I2C写",
    "spi_transfer": "SPI传输",
    "hardware_board_info": "板卡信息","hardware_capabilities": "硬件能力",
    "hardware_memory_map": "内存映射","hardware_memory_read": "内存读取",
    "rpi_system_info": "树莓派系统","pico_flash": "Pico烧录",
    "arduino_upload": "Arduino上传","device_exec": "设备执行",
    "device_read_code": "读设备代码","device_write_code": "写设备代码",
    "read_device": "读设备","set_device": "设置设备",
    "voice_call": "语音通话","voice_wake": "语音唤醒",
    "speak": "朗读","listen": "监听","sense": "传感",
    "image_gen": "图片生成","image_info": "图片信息",
    "sessions_current": "当前会话","sessions_delete": "删除会话",
    "sessions_history": "会话历史","sessions_list": "会话列表",
    "sessions_reset": "重置会话","sessions_send": "发送会话",
    "data_management": "数据管理","datasheet": "数据表",
    "cloud_ops": "云端操作","cloudflare": "Cloudflare",
    "cloud_patterns": "云端模式",
    "ngrok": "Ngrok","tailscale": "Tailscale","openvpn": "OpenVPN",
    "bubblewrap": "沙箱","firejail": "Firejail","landlock": "Landlock",
    "sandbox-exec": "沙箱执行",
    "backup": "备份","restore": "恢复",
    "log": "日志","poll": "轮询","status": "状态",
    "weather": "天气","look": "查看",
    "otel": "OpenTelemetry","lucid": "Lucid","markdown": "Markdown",
    "discord": "Discord","telegram": "Telegram","slack": "Slack",
    "wechat": "微信","whatsapp": "WhatsApp","signal": "Signal",
    "matrix": "Matrix","irc": "IRC","bluesky": "Bluesky",
    "twitter": "X/Twitter","reddit": "Reddit","nostr": "Nostr",
    "line": "Line","dingtalk": "钉钉","feishu": "飞书",
    "twitch": "Twitch","mattermost": "Mattermost",
    "nextcloud_talk": "Nextcloud Talk","mochat": "MoChat",
    "wecom": "企业微信","wecom_ws": "企业微信WS","wati": "WATI",
    "imessage": "iMessage","linkedin": "LinkedIn",
    "channel_notify": "频道通知","channel_room": "频道房间",
    "channel_media": "频道媒体","edit_channel": "编辑频道",
    "room_management": "房间管理","reaction": "表情反应",
    "schedule_message": "定时消息","send_via": "发送方式",
    "mcp_prompts": "MCP提示","mcp_resources": "MCP资源",
    "recording": "录制","event_capture": "事件捕获",
    "report_template": "报告模板","project_intel": "项目情报",
    "google": "Google","google_workspace": "Google Workspace",
    "google_drive": "Google Drive","gmail_push": "Gmail推送",
    "linq": "Linq","driver": "驱动","gated": "门控",
    "identity": "身份","identity_capture": "身份捕获",
    "tool_honesty": "工具诚实度","acp": "ACP协议",
    "ordered": "有序","stateful": "有状态",
    "codex_cli": "Codex CLI","gemini_cli": "Gemini CLI",
    "opencode_cli": "OpenCode CLI","claude_code": "Claude Code",
    "claude_code_runner": "Claude Code Runner",
    "rust": "Rust","wasm": "WASM","runtime": "运行时",
    "composio": "Composio插件","knowledge": "知识库",
    "voice": "语音","look": "查看","keyed": "键控",
    "multifile": "多文件","tool_search": "搜索工具",
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

    # ── 8. fn name(&self) -> &str { "tool_name" } —— 工具名 ──
    if 'fn name(&self)' in content:
        content = re.sub(
            r'(fn name\(&self\)\s*->\s*&str\s*\{\s*)"([^"]+)"(\s*\})',
            lambda m: f'{m.group(1)}"{DICT.get(m.group(2), m.group(2))}"{m.group(3)}',
            content
        )
    
    # ── 9. fn description(&self) -> &str { "长描述" } —— 工具描述 ──
    # 只翻译字典里的整词，避免碎片化
    if 'fn description(&self)' in content:
        content = re.sub(
            r'(fn description\(&self\)\s*->\s*&str\s*\{\s*)"([^"]+)"(\s*\})',
            lambda m: f'{m.group(1)}"{translate_word(m.group(2))}"{m.group(3)}',
            content
        )

    # ── 10. sections.rs: humanize_section_key 的 match arm ──
    if 'pub fn humanize_section_key' in content:
        labels_zh = {
            'providers.models': '模型提供商',
            'providers.routes': '模型路由',
            'embeddings.routes': '嵌入路由',
            'risk_profiles': '风险配置',
            'runtime_profiles': '运行时配置',
            'memory': '记忆',
            'skills': '技能',
            'skill_bundles': '技能集',
            'providers.tts': '语音合成',
            'providers.transcription': '语音识别',
            'channels': '频道',
            'hardware': '硬件',
            'agents': '智能体',
            'peer_groups': '同伴组',
            'tunnel': '隧道',
            'cron': '定时任务',
            'mcp': 'MCP',
            'mcp.servers': 'MCP 服务器',
            'mcp.bundles': 'MCP 服务集',
            'mcp_bundles': 'MCP 服务集',
            'mcp_servers': 'MCP 服务器',
            'knowledge.bundles': '知识库集',
            'knowledge_bundles': '知识库集',
            'backup': '备份',
            'cloud_ops': '云端运维',
            'conversational_ai': '对话 AI',
            'cost': '费用',
            'data_retention': '数据保留',
            'eval': '评估',
            'heartbeat': '心跳',
            'hooks': '钩子',
            'observability': '可观测性',
            'onboard_state': '首次设置',
            'peripherals': '外设',
            'sop_approval': 'SOP 审批',
            'escalation': '升级通知',
            'unattended_upgrades': '自动升级',
            'trust': '信任',
            'pipeline': '管线',
            'pacing': '限速',
            'lifestate': '生命周期',
            'file_download': '文件下载',
            'file_upload': '文件上传',
            'file_upload_bundle': '文件上传集',
            'query_classification': '查询分类',
            'reliability': '可靠性',
            'cost_ops': '费用控制',
            'runtime': '运行时',
            'gateway': '网关',
            'companion_network_peers': '同伴网络节点',
        }
        for key, label in labels_zh.items():
            if f'"{key}" => return "{label}"' not in content:
                content = content.replace(
                    f'"{key}" => return',
                    f'"{key}" => return "{label}".to_string(),\n        _ => {{}}\n    }}\n    #[allow(unreachable_code)]\n    fn __unused() {{}}',
                    1
                )
                # Simpler approach: just replace if pattern exists
                pattern_en = f'"{key}" => return "{label.replace("模型提供商", "Model providers").replace("频道", "Channels").replace("记忆", "Memory").replace("技能", "Skills")}"'
                # Skip - too complex. Just inject new arm.
        
        # Direct injection of Chinese labels at start of match block
        match_pos = content.find('match key {', content.find('pub fn humanize_section_key'))
        if match_pos != -1:
            insert_pos = match_pos + len('match key {') + 1
            new_arms = '\n'
            for key, label in list(labels_zh.items())[:20]:  # 只插入前20个避免太长
                new_arms += f'        "{key}" => return "{label}".to_string(),\n'
            if new_arms not in content:
                content = content[:insert_pos] + new_arms + content[insert_pos:]
    
    # ── 11. sections.rs: SectionGroup::label() ──
    if 'pub const fn label(self) -> &' in content and 'Self::Foundation' in content:
        content = content.replace('Self::Foundation => "Foundation"', 'Self::Foundation => "基础"')
        content = content.replace('Self::Agent => "Agent"', 'Self::Agent => "智能体"')
        content = content.replace('Self::MultiAgent => "Multi-agent"', 'Self::MultiAgent => "多智能体"')
        content = content.replace('Self::Tools => "Tools"', 'Self::Tools => "工具"')
        content = content.replace('Self::Integrations => "Integrations"', 'Self::Integrations => "集成"')
        content = content.replace('Self::Network => "Network"', 'Self::Network => "网络"')
        content = content.replace('Self::Storage => "Storage"', 'Self::Storage => "存储"')
        content = content.replace('Self::Operations => "Operations"', 'Self::Operations => "运维"')
        content = content.replace('Self::Other => "Other"', 'Self::Other => "其他"')
    
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