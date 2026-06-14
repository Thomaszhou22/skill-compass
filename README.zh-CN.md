# 🧭 Skill Compass

**[English](README.md)** | **中文**

> 审计、修复并优化 Agent Skill 描述，让技能可靠触发。支持 OpenClaw、Claude Code、Cursor 及所有 agentskills.io 兼容平台。

**问题所在：** 65% 的 Skill 永远不会触发，因为它们的 description 没有告诉 Agent *什么时候*该启动。Skill Compass 能发现这些问题并修复——能自动修的就自动修，需要 AI 介入的生成功 prompt。

## 安装

```bash
# ClawHub
clawhub install skill-compass-guardian

# 或从源码安装
git clone https://github.com/Thomaszhou22/skill-compass.git
cp -r skill-compass ~/.openclaw/skills/
```

要求 Python 3.8+，无其他依赖。

## 命令一览

```bash
# ── 核心工作流 ──

# 一键全流程：审计 + 自动修复 + 生成 AI prompt（首次使用推荐）
python3 scripts/audit_skills.py --init

# 仅审计——扫描并给所有 Skill 打分
python3 scripts/audit_skills.py

# 自动修复 YAML 语法错误（自动创建备份）
python3 scripts/audit_skills.py --fix

# 生成 AI prompt，让 Agent 重写不合格的描述
python3 scripts/audit_skills.py --suggest

# JSON 输出（供 CI/CD 流水线使用）
python3 scripts/audit_skills.py --json

# ── 备份与回滚 ──

# 给所有 SKILL.md 文件拍照存档
python3 scripts/audit_skills.py --backup

# 查看所有备份
python3 scripts/audit_skills.py --list-backups

# 回滚到最近一次备份
python3 scripts/audit_skills.py --rollback

# 回滚到指定备份
python3 scripts/audit_skills.py --rollback --backup-id 20260614-151204

# ── 回流社区反馈 ──

# 生成 GitHub Issue 草稿，把修复方案分享给 Skill 原作者
python3 scripts/audit_skills.py --feedback
```

## 自愈闭环

`--init` 一步完成全流程——审计、自动修复、生成 AI prompt：

```
  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │  1. 审计     │────▶│  2. 修 YAML  │────▶│  3. 生成 AI prompt │
  │  (找问题)    │     │  (自动补丁)  │     │  (Agent 重写)      │
  └──────────────┘     └──────────────┘     └──────────────────┘
         ▲                                         │
         │          Agent 应用重写结果              │
         └─────────────────────────────────────────┘
                      重新审计验证
```

| 步骤 | 命令 | 发生什么 | 需要人工吗？ |
|------|------|---------|------------|
| **审计** | `--init` 或 不带参数 | 扫描所有 SKILL.md，逐个打分 0–100 | 否 |
| **自动修复** | `--fix` 或 `--init` | 修复 YAML 语法错误，先创建备份 | 否 |
| **生成 prompt** | `--suggest` 或 `--init` | 输出包含规则和上下文的 prompt | 否 |
| **重写** | Agent 读取 prompt | 按规则重写 description | 否——Agent 自己完成 |
| **验证** | 不带参数 | 重新审计确认分数提升 | 否 |

### 在 Agent 环境中（推荐）

如果你有 AI Agent（OpenClaw / Claude Code / Cursor），跟 Agent 说一句"检查一下我的 skills"就行了：

1. Agent 自动运行审计 → 发现哪些不及格
2. Agent 自己读 prompt → 自己改 description
3. Agent 自己重新验证分数

**全程不需要手动粘贴任何东西。**

### 在纯终端环境中

没有 Agent 也能用。运行 `--init`，把生成的 prompt 粘贴给 ChatGPT / Claude 网页版，一样能修复。

## 备份与回滚

每次 `--fix` 和 `--init` 都会在修改文件前自动创建备份。也可以手动管理：

| 命令 | 作用 |
|------|------|
| `--backup` | 给所有 SKILL.md 拍快照，存到 `~/.skill-compass-backups/` |
| `--list-backups` | 列出所有备份，含时间戳和文件数 |
| `--rollback` | 从最近一次备份恢复全部 |
| `--rollback --backup-id <ID>` | 从指定备份恢复 |

```
📦 可用备份（最新在前）：

  ID: 20260614-151204  |  文件数: 18  |  目录: ~/.openclaw/skills

恢复命令: python3 audit_skills.py --rollback [--backup-id <ID>]
```

如果 AI 重写后出了问题——一行命令全部恢复。

## 回流社区反馈

`--feedback` 会对比当前版本和上次备份，生成 **GitHub Issue 草稿**，分享给 Skill 原作者。你决定提交哪些。

生成的 Issue 是标准 bug report 风格，不会推销工具，只在末尾附一行链接：

```
标题: Improve `multi-search-engine` description for reliable agent triggering

## 问题
当前 description 没有触发条件，Agent 无法判断何时启用该技能：
  description: Multi search engine integration with 16 engines...

## 建议修复
  description: Use when the user asks to search the web...

## 为什么这很重要
- 约 65% 的 Agent Skill 因缺少触发词而永不激活
- 指令式描述触发率约 100%
- 被动式描述仅约 37%

_Found via [Skill Compass](https://github.com/Thomaszhou22/skill-compass)_
```

这就形成了一个社区改进闭环：本地修复 → 回流上游 → 所有用户受益。

## 评分机制

每个 Skill 按五个维度打分，总分 0–100：

| 维度 | 权重 | 检查内容 |
|------|------|---------|
| **触发条件** | ±35 | description 是否说明了*何时*启动？（`"Use when..."`） |
| **语言强度** | ±15 | 指令式（`"ALWAYS invoke"`）vs 被动式（`"Helps with"`） |
| **YAML 合法性** | 通过/不通过 | frontmatter 能否正确解析 |
| **描述长度** | ±15–30 | 不超过 350 字符，不少于 30 字符，关键词 ≥10 个词 |
| **冲突检测** | 建议 | 与其他 Skill 的描述是否重叠？（Jaccard > 0.4） |

**实测数据：** 指令式描述（`"Use when..."`）触发率约 100%。被动式描述（`"Helps with..."`）仅约 37%。*(数据来源：650-skill activation experiment, Ivan Seleznov, Medium)*

## 自动修复 vs Agent 修复

| 问题 | 占比 | 谁来修 | 怎么修 |
|------|------|--------|-------|
| 缺少触发条件 | 65% | Agent（通过 `--suggest`） | 用 `"Use when..."` 重写描述 |
| 语言太被动 | 常见 | Agent（通过 `--suggest`） | 改写为指令式 |
| YAML 语法错误 | 15% | 脚本（`--fix`） | 自动给冒号加引号 |
| 描述过长 | 10% | 脚本（建议） | 标记需要精简 |
| 描述冲突 | 5% | Agent（判断） | 添加 `"Do NOT use for..."` 约束 |
| Token 预算超限 | 少见 | 脚本（建议） | 统计所有 Skill 总字符数 |

## 文件结构

```
skill-compass/
├── SKILL.md                        # 诊断工作流 + Agent 修复指南
├── scripts/
│   └── audit_skills.py             # 自动扫描脚本（Python 3，零依赖）
├── references/
│   └── failure-patterns.md         # 6 种失败模式 + 真实案例
└── README.md
```

## 兼容性

- ✅ OpenClaw
- ✅ Claude Code
- ✅ Cursor、Codex CLI、Gemini CLI（所有使用 SKILL.md 的平台）
- ✅ 任何遵循 [agentskills.io](https://agentskills.io) 标准的平台

## 许可证

MIT-0 — 自由使用、修改、分发。无需署名。
