/**
 * sourceTranslator.ts — Web 端源码文本翻译层
 *
 * 不修改 Rust 源码，在 API 响应到达 React 组件之前，
 * 将 Rust 硬编码的英文文本（工具描述、配置字段标签、section 标题）
 * 替换为中文显示。
 *
 * 注入点：api.ts 中的 getTools() / fetchConfigSchema() / getSections()
 *
 * 注意：工具名（name）保留英文，因为它是 LLM function-calling 的标识符。
 *       只翻译 description（描述文本）。
 */

import type { ToolSpec } from '../types/api';

// ---------------------------------------------------------------------------
// 1. 工具描述翻译映射表（84 条，完整覆盖）
//    key = 工具名（fn name() 返回值），value = 中文描述
// ---------------------------------------------------------------------------

const toolDescriptionMap: Record<string, string> = {
  ask_user: '向用户提问并等待回复。将问题发送到消息通道并阻塞，直到用户回复或超时。可提供选项以获得结构化回复。',
  backup: '创建、列出、验证和恢复工作区备份',
  browser_delegate: '将基于浏览器的任务委托给支持浏览器的 CLI，用于与 Teams、Outlook、Jira、Confluence 等 Web 应用交互',
  browser_open: '在系统浏览器中打开已批准的 HTTP/HTTPS URL。安全限制：仅允许白名单域名、禁止本地/私有主机、禁止抓取。',
  calculator: '执行算术和统计计算。支持 25 个函数：add、subtract、divide、multiply、pow、sqrt、abs、modulo、round、log、ln、exp、factorial、sum、average、median、mode、min、max、range、variance、stdev、percentile、count、percentage_change、clamp。需要计算数值结果时使用此工具，而非猜测。',
  canvas: '将渲染内容（HTML、SVG、Markdown）推送到用户可实时查看的 Web 画布。操作：render（推送内容）、snapshot（获取当前内容）、clear（重置画布）、eval（在画布上下文中执行 JS 表达式）。每个画布由 canvas_id 字符串标识。',
  claude_code_runner: '在 tmux 会话中启动 Claude Code 任务，支持实时 Slack 进度更新和 SSH 交接。立即返回会话 ID 和 attach 命令。',
  claude_code: '将编码任务委托给 Claude Code（claude -p）。支持文件编辑、bash 执行、结构化输出和多轮会话。适用于需要 Claude Code 完整智能体循环的复杂编码工作。',
  cloud_ops: '云转型咨询工具。分析 IaC 计划、评估迁移路径、审查成本，并对照 Well-Architected Framework 支柱检查架构。只读：不创建或修改云资源。',
  cloud_patterns: '云模式库。给定工作负载描述，推荐适用的云原生架构模式（容器化、无服务器、数据库现代化等）。',
  codex_cli: '将编码任务委托给 Codex CLI（codex exec）。支持文件编辑和 bash 执行。适用于需要 Codex 完整智能体循环的复杂编码工作。',
  composio: '通过 Composio 在 1000+ 应用上执行操作（Gmail、Notion、GitHub、Slack 等）。action=\'list\' 查看可用操作（含参数名）；action=\'execute\' 配合 action_name/tool_slug 和 params 执行操作；不确定参数时传 \'text\' 和自然语言描述（Composio 通过 NLP 解析正确参数）；action=\'list_accounts\' 或 action=\'connected_accounts\' 列出 OAuth 已连接账户；action=\'connect\' 配合 app/auth_config_id 获取 OAuth URL。省略 connected_account_id 时自动解析。',
  content_search: '在工作区内按正则模式搜索文件内容。支持 ripgrep（rg）或内部回退。输出模式：\'content\'（匹配行及上下文）、\'files_with_matches\'（仅文件路径）、\'count\'（每文件匹配数）。示例：pattern=\'fn main\', include=\'*.rs\', output_mode=\'content\'。',
  data_management: '工作区数据保留、清除和存储统计',
  discord_search: '搜索 Discord 消息历史。返回匹配关键词查询的消息，可按 channel_id、author_id 或时间范围筛选。',
  email_read: '按 UID（来自 email_search 结果）获取邮件完整内容。返回发件人、主题、日期、正文和附件名。不会将邮件标记为已读。',
  email_search: '在已配置的 IMAP 邮箱中搜索邮件。不会修改任何邮件（保留已读状态）。用于检查是否有人发了消息、按主题查找邮件或查看会话。返回每条匹配的发件人、主题、日期和 UID。',
  escalate_to_human: '将情况升级给人工操作员并路由紧急程度。向当前通道发送结构化消息。高/紧急级别还会通知 `[escalation] alert_channels` 中列出的所有通道。可选择阻塞等待人工回复。',
  file_edit: '通过精确字符串匹配替换来编辑文件',
  file_upload_bundle: '将 N 个本地文件作为单个 multipart/form-data 请求上传。所有文件在一次 HTTP 往返中发送；但事务性（全有或全无）语义取决于接收端点。适用于多文件交付物（HTML + CSS + JS、报告 + 图表）。文件路径保留在主机上；字节不加载到模型上下文。返回 HTTP 状态码和截断的响应正文。',
  file_upload: '通过 multipart/form-data 将本地文件上传到已配置的远程端点。文件路径保留在主机上；字节不加载到模型上下文。返回 HTTP 状态码和截断的响应正文，以便调用方提取接收方回显的任何 URL 或标识符。',
  file_write: '将内容写入工作区中的文件。默认文本模式；设置 encoding="base64" 可通过解码 base64 内容写入二进制文件（如 .xlsx/.docx）。',
  gemini_cli: '将编码任务委托给 Gemini CLI（gemini -p）。支持文件编辑和 shell 执行。适用于需要 Gemini CLI 完整智能体循环的复杂编码工作。',
  git_forge: '通过 git 通道操作 git forge（GitHub/Gitea）。操作：\'describe\' 返回资源/操作网格和端点结构；类型化调用接收 {resource, action, repo, ...} 用于 milestone/label/issue/pull/review/reviewer/comment（超出裸 2xx 的验证）；\'raw\' 接收 {method, path, body} 用于尚未类型化的任何端点。不确定时先调用 \'describe\'。通过通道 key 命名 git 通道（默认 \'git\'）。',
  git_operations: '执行结构化 Git 操作（status、diff、log、branch、commit、add、checkout、stash、worktree）。提供解析后的 JSON 输出，并集成安全策略以控制自主权限。',
  glob_search: '在工作区内搜索匹配 glob 模式的文件。返回相对于工作区根目录的匹配文件路径排序列表。示例：\'**/*.rs\'（所有 Rust 文件）、\'src/**/mod.rs\'（src 下所有 mod.rs）。',
  google_workspace: '通过 gws CLI 与 Google Workspace 服务（Drive、Gmail、Calendar、Sheets、Docs 等）交互。需要 gws 已安装并认证。重要：Gmail 命令为 4 段且需要 sub_resource。列出 Gmail 邮件时使用 service=gmail, resource=users, sub_resource=messages, method=list（即 `gws gmail users messages list`）。缺少 sub_resource 时 Gmail 调用会失败。Drive、Calendar 和 Sheets 为 3 段，不使用 sub_resource。',
  hardware_board_info: '返回已连接硬件的完整开发板信息（芯片、架构、内存映射）。使用场景：用户询问"开发板信息"、"我有什么板"、"已连接硬件"、"芯片信息"、"什么硬件"或"内存映射"。',
  hardware_memory_map: '返回已连接硬件的内存映射（Flash 和 RAM 地址范围）。使用场景：用户询问"内存高低地址"、"内存映射"、"地址空间"或"可读地址"。返回数据手册中的 Flash/RAM 范围。',
  hardware_memory_read: '通过 USB 从 Nucleo 读取实际内存/寄存器值。使用场景：用户要求"读取寄存器值"、"读取地址处的内存"、"转储内存"、"低地址 0-126"或"给出地址和值"。返回十六进制转储。需要 Nucleo 通过 USB 连接并启用 probe 功能。参数：address（十六进制，如 0x20000000 表示 RAM 起始）、length（字节数，默认 128）。',
  http_request: '向外部 API 发起 HTTP 请求。支持 GET、POST、PUT、DELETE、PATCH、HEAD、OPTIONS 方法。安全限制：仅允许白名单域名、除非显式配置否则阻止本地/私有主机、可配置超时和响应大小限制。',
  image_gen: '使用 fal.ai（Flux 模型）根据文本提示生成图片。将结果保存到工作区 images 目录并返回文件路径。',
  image_info: '读取图片文件元数据（格式、尺寸、大小）。图片还通过内联图片标记提供给支持视觉的模型。',
  jira: '与 Jira 交互：读取工单、使用 JQL 搜索、添加评论、列出项目和每个工单的状态流转、在工作流中流转工单、以及创建新工单。',
  knowledge: '管理架构决策、解决方案模式、经验教训、专家和关系链接的知识图谱。',
  linkedin: '管理 LinkedIn：创建帖子、列出帖子、评论、反应、删除帖子、查看互动、获取个人资料信息、以及读取已配置的内容策略。需要 .env 文件中的 LINKEDIN_* 凭证。',
  llm_task: '通过 LLM 运行提示（无工具访问）并返回响应。可选择根据 JSON Schema 验证输出。适用于结构化数据提取、分类、摘要和转换任务。',
  fake: '假工具',
  mcp_prompts: '列出或获取已连接 MCP 服务器暴露的提示。action=list [server,cursor] 返回可用提示（名称前缀为 `<server>__<name>`）；action=get name=<prefixed-name> arguments={...} 返回解析后的提示消息。',
  mcp_resources: '列出或读取已连接 MCP 服务器暴露的资源。action=list [server,cursor] 返回可用资源（URI 前缀为 `<server>__<uri>`）；action=read uri=<prefixed-uri> 返回资源内容。',
  memory_export: '将可见记忆导出为 JSON 数组，用于 GDPR 第 20 条数据可移植性。支持按命名空间、会话、类别和时间范围筛选。返回通过当前记忆读取策略的结构化、机器可读的 JSON 条目数组。',
  memory_forget: '按键删除记忆。用于删除过时事实或敏感数据。返回是否找到并删除了该记忆。',
  memory_purge: '删除命名空间或会话中的所有记忆。用于批量删除按租户或按会话的数据。返回已删除条目数。警告：此操作不可撤销。',
  memory_recall: '在长期记忆中搜索相关事实、偏好或上下文。返回按相关性排序的评分结果。支持关键词搜索、省略查询或裸 \'*\' 的近期召回、仅时间查询（since/until）或两者兼有。',
  memory_store: '将事实、偏好或笔记存储到长期记忆。类别 \'core\' 用于永久事实，\'daily\' 用于会话笔记，\'conversation\' 用于聊天上下文，或自定义类别名。',
  model_routing_config: '管理默认模型设置、基于场景的 model_provider/model 路由、分类规则和别名的智能体配置',
  notion: '与 Notion 交互：查询数据库、读取/创建/更新页面、以及搜索工作区。',
  opencode_cli: '将编码任务委托给 OpenCode CLI（opencode run）。支持文件编辑和 bash 执行。适用于需要 OpenCode 完整智能体循环的复杂编码工作。',
  poll: '在消息通道中创建投票。Telegram/Discord 使用原生投票；其他通道格式化为带 emoji 反应投票的编号文本消息。在声明支持 elicitation.form 的 ACP 通道上，工具会阻塞直到用户选择并返回 JSON 编码的结果字符串（含 `question`、`answer`（或多选时的 `answers`）和 `channel` 键）；否则返回人类可读的确认字符串。',
  project_intel: '项目交付智能：生成状态报告、检测风险、起草客户更新、总结冲刺和估算工作量。只读分析工具。',
  proxy_config: '管理 ZeroClaw 代理设置（范围：environment | zeroclaw | services），包括运行时和进程环境变量应用',
  pushover: '向你的设备发送 Pushover 通知。需要 .env 文件中的 PUSHOVER_TOKEN 和 PUSHOVER_USER_KEY。',
  reaction: '在任何活跃通道的消息上添加或移除 emoji 反应。提供通道名（如 \'discord\'、\'slack\'）、平台通道 ID、平台消息 ID 和 emoji（Unicode 字符或平台短代码）。',
  report_template: '使用自定义变量渲染报告模板。支持 weekly_status、sprint_review、risk_register、milestone_report，语言 en/de/fr/it。',
  screenshot: '截取当前屏幕。返回文件路径和 base64 编码的 PNG 数据。',
  send_via: '控制本回合回复投递到哪里和如何投递，或向另一个通道发送额外消息。使用时机：当用户要求特定回复格式或目标时（如"文字回复"、"语音发送"、"仅文字"、"发到我的邮箱"、"转到 Discord"），在响应开始时调用此工具。无需等用户说出工具名；从自然语言推断意图，就像被问天气时使用天气工具一样。无 `body`（路由指令 — 影响本回合主回复）：send_via(modality: "text") 即使在纯语音对端也以文字回复；send_via(modality: "voice") 即使在纯文字对端也以语音回复；send_via(target: "discord.main") 将回复重定向到另一通道；send_via(target: "discord.main", modality: "voice") 重定向并强制模态。无 `body` 时至少需要 `target` 或 `modality` 之一。有 `body`（即时分发 — 主回复仍发到来源通道）：send_via(target: "email.default", body: "...") 向别处发送独立内容。有 `body` 时 `target` 必填。`target` 必须是通道别名（如 telegram.default）或当前智能体所属的对等节点组名。`modality` 默认为对等节点组的 output_modality。',
  sessions_list: '列出所有活跃对话会话及其通道、最后活动时间和消息数。',
  text_browser: '使用文本浏览器（lynx、links 或 w3m）将网页渲染为纯文本。适用于无图形浏览器的无头/SSH 环境。自动检测可用浏览器或使用已配置的偏好。',
  tool_search: '获取延迟加载的 MCP 工具的完整 schema 定义以便调用。使用 "select:name1,name2" 精确匹配或关键词搜索。',
  weather: '获取全球任意地点的当前天气状况和最多 3 天预报。支持城市名（任何语言或文字）、机场 IATA 代码（如 \'LAX\'）、GPS 坐标（如 \'51.5,-0.1\'）、邮编和基于域名的地理定位。无需 API 密钥。默认公制单位（°C、km/h、mm），可按请求切换为英制（°F、mph、英寸）。',
  web_fetch: '抓取网页并返回纯文本内容。HTML 页面自动转换为可读文本。JSON 和纯文本响应原样返回。仅 GET 请求；跟随重定向。对 JS 重度/反爬站点回退到 Firecrawl（如已启用）。安全：仅允许白名单域名、禁止本地/私有主机。',
  web_search_tool: '搜索网络获取信息。返回相关搜索结果，含标题、URL 和描述。用于查找最新信息、新闻或研究主题。',
  counting: '计数调用次数',
  cron_add: '创建定时 cron 任务（shell 或 agent），支持 cron/at/after/every 调度。job_type=\'agent\' 配合提示可按计划运行 AI 智能体。对于"10 分钟后"或"2 小时后"等相对一次性提醒，使用 schedule={"kind":"after","after_seconds":...}；运行时在工具执行时用实时时钟解析。要投递输出到已配置通道，设置 delivery={"mode":"announce","channel":"discord","to":"<channel_id_or_chat_id>"}。对于需要线程化到原始会话的 webhook 投递，还需设置 delivery.thread_id="<reply_target>"。这是向用户通过通道发送定时/延迟消息的首选工具。',
  cron_list: '列出所有定时 cron 任务',
  cron_remove: '按 ID 或名称删除 cron 任务',
  cron_run: '立即强制运行 cron 任务并记录运行历史',
  cron_runs: '列出 cron 任务的最近运行历史',
  cron_update: '修补现有 cron 任务（计划、命令、提示、启用状态、投递、模型等）。接受任务名或 ID — 无需先调用 cron_list。',
  noop: '将子任务委托给专门的智能体。使用场景：任务受益于不同模型（如快速摘要、深度推理、代码生成）。子智能体默认运行单个提示；agentic=true 时可迭代带过滤的工具调用循环。支持后台执行（立即返回 task_id）、批量后台等待（await_sessions）和并行执行（并发运行多个智能体）。',
  file_read: '读取文件内容并带行号。支持通过 offset 和 limit 部分读取。拒绝二进制和图片文件（图片请用 image_info 工具）。设置 encoding="base64" 可返回 base64 编码的原始字节（适用于 .pdf/.xlsx/.docx 等二进制文件）；该模式下 offset/limit 被忽略。',
  read_skill: '按名称读取可用技能的完整源文件。在紧凑技能模式下需要完整技能指令而不想记文件路径时使用。',
  schedule: '管理仅 shell 的定时任务。操作：create/add/once/list/get/cancel/remove/pause/resume。警告：此工具创建的 shell 任务输出仅记录日志，不投递到任何通道。要向 Discord/Telegram/Slack/Matrix 发送定时消息，请使用 cron_add 工具，设 job_type=\'agent\' 和投递配置如 {"mode":"announce","channel":"discord","to":"<channel_id>"}。',
  security_ops: '托管网络安全服务的安全运营工具。操作：triage_alert（分类/优先级排序告警）、run_playbook（执行事件响应步骤）、parse_vulnerability（解析扫描结果）、generate_report（生成安全态势报告）、list_playbooks（列出可用剧本）、alert_stats（汇总告警指标）。',
  shell: '在工作区目录中执行 shell 命令',
  skills_list: '列出已安装的技能及其名称、版本和一行描述。只读。在使用 `skill_view` 或 `skill_manage` 前使用以查找候选 slug。',
  sop_advance: '报告当前 SOP 步骤的结果并前进到下一步。提供 run_id、步骤是否成功或失败，以及简要输出摘要。',
  sop_approve: '批准等待操作员审批的 SOP 步骤。返回要执行的步骤指令。使用 sop_status 查看哪些运行在等待。',
  sop_execute: '按名称手动触发标准操作流程（SOP）。返回运行 ID 和第一步指令。使用 sop_list 查看可用 SOP。',
  sop_list: '列出所有已加载的标准操作流程（SOP）及其触发器、优先级、步骤数和活跃运行数。可按名称或优先级筛选。',
  sop_status: '查询 SOP 执行状态。提供 run_id 查看特定运行，或 sop_name 列出该 SOP 的运行。不带参数时显示所有活跃运行。',
  sop_workshop: '管理 SOP 程序性记忆提案：propose、capture_run、list、inspect、apply、reject 或 quarantine。仅在显式操作后才写入 SOP.toml/SOP.md。',
  TodoWrite: '为当前工作渲染实时任务跟踪器。每次调用时传入完整的当前 todo 列表 — 新列表完全替换前一个。每个 todo 有 `content`（祈使句描述）、`status`（pending、in_progress 或 completed），以及可选的 `priority`（high、medium、low）和 `activeForm`（in_progress 时显示的进行时标签）。同时只保持一项 in_progress。传入空列表可清除跟踪器。',
  vi_verify: '验证可验证意图凭证链。支持两种操作：\'verify_binding\' 检查凭证层之间的 sd_hash 绑定；\'evaluate_constraints\' 根据履行数据验证约束。',
};

// ---------------------------------------------------------------------------
// 2. 配置字段 description 翻译映射表
//    key = 英文原文（Rust /// doc comment），value = 中文翻译
//    注意：配置字段数量庞大（300-500+），此处提供框架和示例。
//    完整映射可通过脚本从 schema.rs 的 /// 注释批量提取后翻译填充。
// ---------------------------------------------------------------------------

const configDescriptionMap: Record<string, string> = {
  // 示例条目 — 扩展时按同样格式添加
  'Secret API token for this model_provider. Grab it from the model_provider\'s dashboard (OpenAI platform, Anthropic console, OpenRouter keys page, etc.). Stored via the OS keyring when possible; never commit it to config.toml directly.':
    '此 model_provider 的密钥 API 令牌。从 model_provider 的控制面板获取（OpenAI 平台、Anthropic 控制台、OpenRouter 密钥页面等）。尽可能通过 OS 密钥环存储；切勿直接提交到 config.toml。',
  // 添加更多配置字段翻译...
};

// ---------------------------------------------------------------------------
// 3. Section label/help 翻译映射表
//    key = 英文原文，value = 中文翻译
// ---------------------------------------------------------------------------

const groupMap: Record<string, string> = {
  'Foundation': '基础',
  'Agent': '智能体',
  'Multi-agent': '多智能体',
  'Tools': '工具',
  'Integrations': '集成',
  'Network': '网络',
  'Storage': '存储',
  'Operations': '运维',
  'Other': '其他',
};

const sectionLabelMap: Record<string, string> = {
  // 示例 — 根据 /api/config/sections 返回的实际 label 填充
  // 'Channels': '通道',
  // 'Model Providers': '模型提供商',
  // 'Agents': '智能体',
};

const sectionHelpMap: Record<string, string> = {
  // 示例 — 根据 /api/config/sections 返回的实际 help 填充
};

// ---------------------------------------------------------------------------
// 翻译函数
// ---------------------------------------------------------------------------

/**
 * 翻译单个工具规格 — 替换 description 为中文（name 保留英文）
 */
export function translateToolSpec<T extends ToolSpec>(tool: T): T {
  const zh = toolDescriptionMap[tool.name];
  return zh ? { ...tool, description: zh } : tool;
}

/**
 * 批量翻译工具列表
 */
export function translateToolSpecs<T extends ToolSpec>(tools: T[]): T[] {
  return tools.map(translateToolSpec);
}

/**
 * 递归翻译 JSON Schema 中的所有 description 字段
 * 遍历 properties / items / additionalProperties / definitions / $defs
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function translateConfigSchema(schema: any): any {
  if (!schema || typeof schema !== 'object') return schema;

  const result = Array.isArray(schema)
    ? schema.map(translateConfigSchema)
    : { ...schema };

  // 翻译当前层级的 description
  if (typeof result.description === 'string') {
    const zh = configDescriptionMap[result.description];
    if (zh) result.description = zh;
  }

  // 递归 properties
  if (result.properties && typeof result.properties === 'object') {
    result.properties = {};
    for (const [key, value] of Object.entries(schema.properties)) {
      result.properties[key] = translateConfigSchema(value);
    }
  }

  // 递归 items（数组类型）
  if (result.items) {
    result.items = translateConfigSchema(schema.items);
  }

  // 递归 additionalProperties（map 类型）
  if (result.additionalProperties && typeof result.additionalProperties === 'object') {
    result.additionalProperties = translateConfigSchema(schema.additionalProperties);
  }

  // 递归 definitions / $defs（引用定义）
  for (const defKey of ['definitions', '$defs']) {
    if (result[defKey] && typeof result[defKey] === 'object') {
      result[defKey] = {};
      for (const [key, value] of Object.entries(schema[defKey])) {
        result[defKey][key] = translateConfigSchema(value);
      }
    }
  }

  // 递归 oneOf / anyOf / allOf
  for (const combKey of ['oneOf', 'anyOf', 'allOf']) {
    if (Array.isArray(result[combKey])) {
      result[combKey] = schema[combKey].map(translateConfigSchema);
    }
  }

  return result;
}

/**
 * 翻译 section 列表 — 替换 label、help 和 group
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function translateSections<T extends { label?: string; help?: string; group?: string }>(sections: T[]): T[] {
  return sections.map((s) => {
    const result = { ...s } as any;
    if (s.label && sectionLabelMap[s.label]) {
      result.label = sectionLabelMap[s.label];
    }
    if (s.help && sectionHelpMap[s.help]) {
      result.help = sectionHelpMap[s.help];
    }
    if (s.group) {
      result.group = groupMap[s.group] || s.group;
    }
    }
    return result;
  });
}

/**
 * 通用文本翻译 — 用于零散的硬编码英文文本
 * 如果映射表中没有匹配项，返回原文（降级处理）
 */
export function translateText(en: string): string {
  return configDescriptionMap[en]
    || sectionLabelMap[en]
    || sectionHelpMap[en]
    || en;
}
