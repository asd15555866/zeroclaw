// API 拦截层：在 Web 端将 Rust 产生的英文翻译为中文
// 不改 Rust 源码，在 api.ts 的 3 个返回点注入翻译后再传给 React 组件

import type { ToolSpec } from "../types/api";
import type { components } from "./api-generated";
import type { JsonSchema } from "./api";

type SectionInfo = {
  key: string;
  label: string;
  help?: string;
  group?: string;
  shape?: string;
};

type SectionsResponse = { sections: SectionInfo[] };

// ═══════════════════════════════════════════
// 工具描述翻译映射
// ═══════════════════════════════════════════
const TOOL_DESC_MAP: Record<string, string> = {
  'shell terminal': '执行 Shell 命令并返回输出。命令在智能体工作目录中运行',
  'file read': '读取文件内容，带行号。支持任意文本文件格式',
  'file write': '写入新的文件内容。如果文件已存在则覆盖',
  'file edit': '使用字符串替换编辑文件的指定行',
  'Glob Search': '使用 glob 模式在工作空间中查找文件',
  'Content Search': '使用正则表达式在文件内容中搜索',
  'cron list': '列出所有已配置的定时任务',
  'cron add': '添加一个新的定时任务',
  'cron remove': '删除指定的定时任务',
  'cron update': '更新现有定时任务的参数',
  'cron run': '立即手动运行一个定时任务',
  'cron runs': '查看定时任务的运行历史',
  'Memory Store': '将信息保存到持久记忆后端',
  'Memory Recall': '从记忆后端检索之前存储的信息',
  'Memory Forget': '从记忆后端删除特定的记忆条目',
  'Memory Export': '导出记忆到 JSON 文件',
  'Memory Purge': '清除所有记忆条目',
  'Todo Write': '创建和更新结构化任务列表，带状态追踪',
  'Web Fetch': '获取网页或 API 端点并返回内容',
  'Web Search': '通过搜索引擎搜索互联网',
  'SOP Execute': '执行一个标准操作流程',
  'SOP List': '列出所有可用的 SOP 模板和实例',
  'SOP Status': '检查指定 SOP 运行的状态',
  'SOP Advance': '推进正在运行的 SOP 到下一步',
  'SOP Approve': '批准需要人工确认的 SOP 步骤',
  'SOP Workshop': '交互式创建和编辑 SOP',
  'Spawn SubAgent': '创建临时子智能体',
  'Send Message to Peer': '向同伴组中的其他智能体发送消息',
  'Model Routing Config': '配置模型路由策略',
  'Ask User': '向用户询问问题并等待回复',
  'Escalate to Human': '将问题升级给人工操作员',
  'Browser': '打开浏览器并执行自动化操作',
  'Browser Open': '在浏览器中打开 URL 并返回页面内容',
  'Browser Delegate': '将复杂的浏览器操作委派给专用浏览器智能体',
  'Screenshot': '捕获当前浏览器页面的截图',
  'Calculator': '执行数学计算',
  'Date Time': '获取当前日期和时间',
  'Weather': '获取指定位置的天气预报',
  'Docker': '执行 Docker 容器管理命令',
  'PostgreSQL': '执行 PostgreSQL 数据库查询',
  'SQLite': '执行 SQLite 数据库查询',
  'Qdrant': '执行 Qdrant 向量数据库操作',
  'Prometheus': '查询 Prometheus 指标',
  'Git': '执行 Git 版本控制命令',
  'GitHub': '执行 GitHub API 操作',
  'Jira': '执行 Jira 问题追踪操作',
  'Notion': '执行 Notion API 操作',
  'Email': '发送邮件',
  'Email Read': '读取邮件',
  'Email Search': '搜索邮件',
  'Webhook': '发送 HTTP Webhook 请求',
  'Broadcast': '向多个频道广播消息',
  'Canvas': '在画布上推送可视内容',
  'Workspace': '管理文件系统操作',
  'GPIO Read': '从 GPIO 引脚读取数据',
  'GPIO Write': '向 GPIO 引脚写入数据',
  'I2C Read': '从 I2C 设备读取数据',
  'I2C Write': '向 I2C 设备写入数据',
  'SPI Transfer': '执行 SPI 总线传输',
  'Hardware Board Info': '获取单板计算机信息',
  'Read Device': '读取设备信息',
  'Set Device': '配置或设置设备参数',
  'Voice Call': '发起语音通话',
  'Voice Wake': '语音唤醒功能',
  'Speak': '将文本转换为语音朗读',
  'Listen': '监听语音输入',
  'Image Gen': '使用 AI 生成图片',
  'Image Info': '获取图片元信息',
  'Session Send': '向当前会话发送消息',
  'Session History': '查看会话历史',
  'Session Delete': '删除会话',
  'Session List': '列出所有会话',
  'Session Reset': '重置当前会话',
  'Discord': 'Discord 频道集成',
  'Telegram': 'Telegram 频道集成',
  'Slack': 'Slack 频道集成',
  'WeChat': '微信频道集成',
  'WhatsApp': 'WhatsApp 频道集成',
  'Signal': 'Signal 频道集成',
  'Line': 'Line 频道集成',
  'DingTalk': '钉钉频道集成',
  'Feishu': '飞书频道集成',
  'Voice': '语音频道集成',
  'Google': 'Google API 集成',
  'Google Workspace': 'Google Workspace 集成',
};

// ═══════════════════════════════════════════
// Section 标签翻译
// ═══════════════════════════════════════════
const SECTION_LABEL_MAP: Record<string, string> = {
  'Model providers': '模型提供商',
  'Model routes': '模型路由',
  'Embedding routes': '嵌入路由',
  'Risk profiles': '风险配置',
  'Runtime profiles': '运行时配置',
  'Memory': '记忆',
  'Skills': '技能',
  'Skill bundles': '技能集',
  'TTS providers': '语音合成',
  'Transcription providers': '语音识别',
  'Channels': '频道',
  'Hardware': '硬件',
  'Agents': '智能体',
  'Peer groups': '同伴组',
  'Tunnel': '隧道',
  'Cron': '定时任务',
  'MCP': 'MCP',
  'MCP servers': 'MCP 服务器',
  'MCP bundles': 'MCP 服务集',
  'Knowledge bundles': '知识库集',
};

// ═══════════════════════════════════════════
// 通用字段翻译
// ═══════════════════════════════════════════
const SECTION_GROUP_MAP: Record<string, string> = {
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

// ═══════════════════════════════════════════
// 配置字段翻译
// ═══════════════════════════════════════════
const FIELD_LABEL_MAP: Record<string, string> = {
  'Enabled': '已启用', 'Disabled': '已禁用',
  'Bind': '绑定', 'Port': '端口', 'Host': '主机',
  'URI': '地址', 'URL': 'URL', 'Path': '路径',
  'Key': '密钥', 'Secret': '密钥', 'Token': '令牌',
  'Name': '名称', 'Alias': '别名', 'Type': '类型',
  'Status': '状态', 'Mode': '模式', 'Format': '格式',
  'Target': '目标', 'Source': '来源',
  'Timeout': '超时', 'Interval': '间隔',
  'Limit': '限制', 'Threshold': '阈值',
  'Default': '默认', 'Optional': '可选', 'Required': '必填',
  'Public Base URL': '公共 URL', 'Base URL': '基础 URL',
  'API Key': 'API 密钥', 'Model ID': '模型 ID',
  'Provider': '提供商', 'Provider Alias': '提供商别名',
  'Endpoint': '端点', 'Endpoint URL': '端点地址',
  'Description': '描述', 'Version': '版本',
  'Channel': '频道', 'Agent': '智能体',
  'Server': '服务器', 'Client': '客户端',
  'Storage': '存储', 'Memory': '记忆',
  'Sandbox': '沙箱', 'Browser': '浏览器',
  'Gateway': '网关', 'Daemon': '守护进程',
  'Username': '用户名', 'Password': '密码',
};

// ═══════════════════════════════════════════
// API 拦截函数
// ═══════════════════════════════════════════

/** 翻译单个工具的 description（name 保留原文，LLM 需要） */
function translateToolDescription(name: string, desc: string): string {
  return TOOL_DESC_MAP[name] ?? TOOL_DESC_MAP[desc] ?? desc;
}

/** 拦截 getTools() 返回值，翻译工具描述 */
export function translateToolSpecs(tools: ToolSpec[]): ToolSpec[] {
  return tools.map((t) => {
    const key = t.name || t.description || '';
    const translated = TOOL_DESC_MAP[key];
    if (translated) {
      return { ...t, description: translated };
    }
    return t;
  });
}

/** 递归翻译 JSON Schema 中的 description */
export function translateConfigSchema(schema: JsonSchema): JsonSchema {
  if (!schema || typeof schema !== 'object') return schema;
  
  const result = { ...schema } as Record<string, unknown>;

  // 翻译 description
  if (typeof result.title === 'string' && FIELD_LABEL_MAP[result.title]) {
    result.title = FIELD_LABEL_MAP[result.title];
  }
  
  // 递归 properties
  if (result.properties && typeof result.properties === 'object') {
    const props = result.properties as Record<string, Record<string, unknown>>;
    for (const [key, value] of Object.entries(props)) {
      if (typeof value === 'object' && value !== null) {
        // 翻译字段标签：将 snake_case key 转为中文标签
        const labelKey = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        if (FIELD_LABEL_MAP[labelKey] && value.title === undefined) {
          value.title = FIELD_LABEL_MAP[labelKey];
        }
        result.properties[key] = translateConfigSchema(value as JsonSchema);
      }
    }
  }

  // 递归 definitions / $defs
  for (const defKey of ['definitions', '$defs']) {
    if (result[defKey] && typeof result[defKey] === 'object') {
      const defs = result[defKey] as Record<string, JsonSchema>;
      for (const [k, v] of Object.entries(defs)) {
        defs[k] = translateConfigSchema(v);
      }
    }
  }

  // 递归 items
  if (result.items && typeof result.items === 'object') {
    const items = result.items as JsonSchema;
    if (typeof items.title === 'string' && FIELD_LABEL_MAP[items.title]) {
      (items as Record<string, unknown>).title = FIELD_LABEL_MAP[items.title];
    }
    result.items = items;
  }

  // 递归 oneOf/anyOf/allOf
  for (const ofKey of ['oneOf', 'anyOf', 'allOf']) {
    if (Array.isArray(result[ofKey])) {
      result[ofKey] = (result[ofKey] as JsonSchema[]).map(translateConfigSchema);
    }
  }

  return result as JsonSchema;
}

/** 翻译 Section 列表 */
export function translateSections(sections: SectionInfo[]): SectionInfo[] {
  return sections.map((s) => {
    const label = SECTION_LABEL_MAP[s.label] || FIELD_LABEL_MAP[s.label] || s.label;
    const group = s.group ? SECTION_GROUP_MAP[s.group] || s.group : s.group;
    return { ...s, label, group };
  });
}
