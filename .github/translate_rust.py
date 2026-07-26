#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Actions 自动翻译 ZeroClaw Rust 源码中的英文字段为中文"""

import re, os, sys

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", "/home/runner/work/zeroclaw/zeroclaw")

# ====== 翻译字典 ======
TRANSLATIONS = {
    # ── Sections 分组名 ──
    "Pick a model provider to configure": "选择一个模型提供商进行配置",
    "Multiple aliases per provider are supported": "每个提供商支持多个别名",
    "anthropic.production and anthropic.dev can coexist": "例如 anthropic.production 和 anthropic.dev 可共存",
    "Named model routing hints": "命名的模型路由提示",
    "Each route maps a hint to a specific provider + model combo": "每个路由将提示映射到特定的提供商和模型组合",
    "Use `hint:<name>` as the model parameter to dispatch through a route": "使用 `hint:<name>` 作为模型参数以通过路由调度",
    "Named embedding routing hints": "命名的嵌入路由提示",
    "Each route maps a hint to an embedding-capable provider": "每个路由将提示映射到支持嵌入的提供商",
    "Use `hint:<name>` as the embedding_model parameter": "使用 `hint:<name>` 作为 embedding_model 参数",
    "Named risk profiles binding allowlists, denylists, and approval thresholds": "命名的风险配置，绑定白名单、黑名单和审批阈值",
    "Agents reference one via `agents.<alias>.risk_profile`": "智能体通过 `agents.<alias>.risk_profile` 引用",
    "Named runtime tuning profiles": "命名的运行时调优配置",
    "token limits, retry policy, timeouts": "令牌限制、重试策略、超时",
    "Agents reference one via `agents.<alias>.runtime_profile`": "智能体通过 `agents.<alias>.runtime_profile` 引用",
    "SQLite is the safe default for single-node installs": "SQLite 是单节点安装的安全默认选择",
    "file-based, zero-config, no extra services": "基于文件，零配置，无需额外服务",
    "Pick Postgres for shared or multi-instance deployments": "对于共享或多实例部署请选择 Postgres",
    "Qdrant for vector search": "向量搜索用 Qdrant",
    "Markdown or Lucid for human-readable files": "Markdown 或 Lucid 用于可读文件",
    "Each backend supports multiple aliased instances": "每个后端支持多个别名实例",
    "agents reference them via `memory.storage_ref`": "智能体通过 `memory.storage_ref` 引用",
    "Persistent memory backend": "持久化记忆后端",
    "SQLite is the default; pick `none` to disable long-term recall entirely": "SQLite 是默认选项；选择 `none` 可完全禁用长期记忆",
    "Skills tool settings": "技能工具设置",
    "where skill markdown lives on disk": "技能 Markdown 文件所在路径",
    "defaults to the data dir": "默认为数据目录",
    "how the skills loader handles community repositories": "技能加载器如何处理社区仓库",
    "Add skill BUNDLES under `skill-bundles` below": "在下方 `skill-bundles` 中添加技能集",
    "Named bundles of skill files": "命名的技能文件集",
    "Agents reference a bundle to load a set of capabilities at startup": "智能体引用一个技能集以在启动时加载",
    "Model Context Protocol settings": "模型上下文协议设置",
    "Toggle `enabled` and pick deferred or eager loading": "切换 `enabled` 并选择延迟或立即加载",
    "Individual MCP servers live under `mcp.servers[]`": "各 MCP 服务器在 `mcp.servers[]` 下配置",
    "Named bundles of MCP servers": "命名的 MCP 服务集",
    "granted to agents that list the bundle in their `mcp_bundles`": "授予在其 `mcp_bundles` 中列出该服务集的智能体",
    "Secure by default: an agent gets only the servers its bundles grant": "默认安全：智能体只能使用其服务集授予的服务器",
    "with no bundle it gets no MCP servers": "没有服务集则不获得 MCP 服务器",
    "Named bundles of knowledge sources": "命名的知识源集",
    "RAG indexes, doc folders": "RAG 索引、文档文件夹",
    "Agents reference a bundle to surface relevant snippets at inference time": "智能体引用知识源集在推理时展示相关内容",
    "Text-to-speech providers": "文本转语音提供商",
    "OpenAI, ElevenLabs, Google, Edge, Piper": "OpenAI、ElevenLabs、Google、Edge、Piper",
    "Configure one per voice / language": "每种语音/语言配置一个",
    "agents reference them by alias": "智能体通过别名引用",
    "Speech-to-text providers": "语音转文本提供商",
    "OpenAI Whisper, Groq, Deepgram, AssemblyAI, Google, local Whisper": "OpenAI Whisper、Groq、Deepgram、AssemblyAI、Google、本地 Whisper",
    "Configure one per pipeline": "每个管线配置一个",
    "Pick which chat platforms ZeroClaw should listen on": "选择 ZeroClaw 监听的聊天平台",
    "Global channel settings live on `[channels]`": "全局频道设置在 `[channels]` 下",
    "each configured platform still gets its own alias": "每个已配置的平台仍然有自己的别名",
    "Optional: hardware peripherals": "可选：硬件外设",
    "Arduino, STM32, GPIO, etc.": "Arduino、STM32、GPIO 等",
    "Skip if you don't need them": "如不需要可跳过",
    "An agent binds a model provider, profiles, bundles, and channels into one dispatchable unit": "智能体将模型提供商、配置、技能集和频道绑定为一个可调度的单元",
    "Add one per persona; reuse the same alias across channels to share state": "每个角色添加一个；跨频道复用同一别名以共享状态",
    "Named groups binding a channel, member agents, and external peers": "命名的分组绑定频道、成员智能体和外部同伴",
    "Mutual opt-in: two agents become peers only when both appear in the same group": "双向确认：只有两个智能体同时出现在同一分组才算同伴",
    "Scheduled tasks": "定时任务",
    "Each cron entry binds a schedule expression to a prompt, channel, and target": "每个 Cron 条目将调度表达式绑定到提示词、频道和目标",

    # ── Schema 字段描述 ──
    "Observability backend configuration": "可观测性后端配置",
    "Backup tool configuration": "备份工具配置",
    "Pacing controls for slow/local LLM workloads": "慢速/本地 LLM 负载的限速控制",
    "Pipeline tool configuration": "管线工具配置",
    "Heartbeat configuration for periodic health pings": "周期性健康检查的心跳配置",
    "Hooks configuration (lifecycle hooks and built-in hook toggles)": "钩子配置（生命周期钩子和内置钩子开关）",
    "File download tool configuration": "文件下载工具配置",
    "File upload tool configuration": "文件上传工具配置",
    "Operations / monitoring": "运维 / 监控",
    "Security configuration": "安全配置",
    "Cloud operations configuration": "云端运维配置",
    "Cost tracking configuration": "费用追踪配置",
    "Data retention configuration": "数据保留配置",
    "Eval harness configuration": "评估框架配置",
    "Peripherals configuration": "外设配置",
    "Trust configuration": "信任配置",
    "Unattended upgrades configuration": "自动升级配置",
    "Escalation configuration": "升级通知配置",
    "Runtime configuration": "运行时配置",
    "Identity configuration": "身份配置",
    "Multimodal configuration": "多模态配置",
    "Browser configuration": "浏览器配置",
    "Sandbox configuration": "沙箱配置",
    "Notifications configuration": "通知配置",
    "Gateway configuration": "网关配置",
    "WebAuthn configuration": "WebAuthn 配置",
    "SOP (Standard Operating Procedure) configuration": "SOP（标准操作流程）配置",
    "Query classification configuration": "查询分类配置",
    "Tool permission grid": "工具权限网格",

    # ── 字段标签 (Schema field names → human readable) ──
    "Enable automatic skill creation": "启用自动技能创建",
    "Allow scripts in skill execution": "允许在技能执行中运行脚本",
    "Cooldown duration between skill creations": "技能创建之间的冷却时间",
    "Maximum number of automatic skills": "自动技能的最大数量",
    "Skill creation prompt template": "技能创建提示词模板",
    "Skill directory path on disk": "磁盘上的技能目录路径",
    "Community repository URL": "社区仓库地址",
    "Auto-update interval for community skills": "社区技能的自动更新间隔",
    "Enable periodic health pings": "启用周期性健康检查",
    "Health ping interval in seconds": "健康检查间隔（秒）",
    "Health ping timeout in seconds": "健康检查超时（秒）",
    "Target endpoint for health pings": "健康检查的目标端点",
    "Enable automatic backups": "启用自动备份",
    "Backup interval in hours": "备份间隔（小时）",
    "Maximum number of backup files to retain": "保留的备份文件最大数量",
    "Backup target directory": "备份目标目录",
    "Backup compression enabled": "启用备份压缩",
    "Enable cost tracking": "启用费用追踪",
    "Daily cost limit in USD": "每日费用上限（美元）",
    "Monthly cost limit in USD": "每月费用上限（美元）",
    "Warning threshold percentage": "警告阈值百分比",
    "Enable hooks system": "启用钩子系统",
    "Pre-request hook": "请求前钩子",
    "Post-response hook": "响应后钩子",
    "Error recovery hook": "错误恢复钩子",
    "Enable pacing for slow models": "为慢速模型启用限速",
    "Maximum concurrent requests": "最大并发请求数",
    "Request rate limit per minute": "每分钟请求速率限制",
    "Retry delay in milliseconds": "重试延迟（毫秒）",
    "Maximum retry attempts": "最大重试次数",
    "Enable observability": "启用可观测性",
    "Observability backend type": "可观测性后端类型",
    "OpenTelemetry endpoint URL": "OpenTelemetry 端点地址",
    "Service name for traces/metrics": "追踪/指标的服务名称",
    "Log persistence mode": "日志持久化模式",
    "Log file path": "日志文件路径",
    "Maximum log entries": "最大日志条目数",
    "Rotate logs daily": "每日轮转日志",
    "Maximum retained log files": "最大保留日志文件数",
    "Sandbox type": "沙箱类型",
    "Enable sandbox for shell commands": "为 Shell 命令启用沙箱",
    "Sandbox timeout in seconds": "沙箱超时（秒）",
    "Allowed filesystem paths": "允许的文件系统路径",
    "Denied filesystem paths": "禁止的文件系统路径",
    "Enable browser automation": "启用浏览器自动化",
    "Browser timeout in seconds": "浏览器超时（秒）",
    "Browser sandbox enabled": "浏览器沙箱已启用",
    "Gateway host binding address": "网关绑定地址",
    "Gateway listening port": "网关端口",
    "Require pairing for connections": "要求配对认证",
    "Allow public network binding": "允许公网绑定",
    "Allow remote administration": "允许远程管理",
    "Paired access tokens": "已配对的访问令牌",
    "Enable trust scoring": "启用信任评分",
    "Initial trust score": "初始信任分数",
    "Trust score decay rate": "信任分数衰减率",
    "Regression threshold for trust": "信任回归阈值",
    "Enable escalation notifications": "启用升级通知",
    "Escalation alert channels": "升级通知频道",
    "Maximum escalation retries": "最大升级重试次数",
    "Escalation timeout": "升级超时",
    "Enable security auditing": "启用安全审计",
    "Audit log file path": "审计日志文件路径",
    "Maximum audit log size": "最大审计日志大小",
    "Enable secret leak detection": "启用密钥泄露检测",
    "Leak detection sensitivity": "泄露检测灵敏度",
    "Enable session persistence": "启用会话持久化",
    "Session backend type": "会话后端类型",
    "Session TTL in hours": "会话有效期（小时）",
    "Message timeout in seconds": "消息超时（秒）",
    "Maximum concurrent conversations per channel": "每频道最大并发对话数",
    "Show acknowledgment reactions": "显示确认反应",
    "Show tool call details in channel": "在频道中显示工具调用详情",
    "Enable file download tool": "启用文件下载工具",
    "Maximum download file size in bytes": "最大下载文件大小（字节）",
    "Allowed download domains": "允许的下载域名",
    "Download timeout in seconds": "下载超时（秒）",
    "Enable file upload tool": "启用文件上传工具",
    "Maximum upload file size in bytes": "最大上传文件大小（字节）",
    "Allowed upload MIME types": "允许的上传 MIME 类型",
    "Upload destination path": "上传目标路径",
}

def translate_file(filepath):
    """翻译单个 Rust 文件的英文字段"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return False

    original = content
    for en_text, zh_text in TRANSLATIONS.items():
        # 在 Rust 的 `help:` 字符串或文档注释 `///` 中替换
        content = content.replace(en_text, zh_text)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    targets = [
        f"{WORKSPACE}/crates/zeroclaw-config/src/sections.rs",
        f"{WORKSPACE}/crates/zeroclaw-config/src/schema.rs",
    ]

    translated = 0
    for fp in targets:
        if translate_file(fp):
            translated += 1
            print(f"[OK] Translated: {os.path.basename(fp)}")

    print(f"\nDone. {translated}/{len(targets)} files translated.")

    if translated == 0:
        print("Warning: No translations applied. Check the key strings match.")

if __name__ == "__main__":
    main()
