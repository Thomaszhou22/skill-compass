# 🧭 Skill Compass

**English** | **[中文](README.zh-CN.md)**

Audit, fix, and optimize agent skill descriptions so they trigger reliably. Works with OpenClaw, Claude Code, Cursor, and any agentskills.io-compatible platform.

**The problem:** 65% of skills never trigger because their descriptions don't tell the agent *when* to fire. Skill Compass finds these and fixes them — automatically where possible, AI-assisted where not.

---

## Onboarding

When first installed (or when you say "audit my skills"), Skill Compass runs a comprehensive ecosystem health check:

1. **Scan all installed skills** — audit every SKILL.md for YAML validity, description quality, and discoverability
2. **Present a health report** — total skills, healthy vs broken, token budget usage, issues found
3. **Ask: auto-fix or manual?** — _"I found X issues. Want me to fix them automatically?"_
4. **Conflict detection** — flag any skills with overlapping trigger keywords
5. **Token budget advice** — warn if total description chars are approaching the limit
6. **Record onboarding** — subsequent runs skip the overview and go straight to audit workflow

```
📊 Skill Ecosystem Health Report

Total skills: 18
✅ Healthy: 15
⚠️ Needs attention: 3
❌ Broken: 0

Token budget: 8,420 / 30,000 chars (28% used)

Issues found:
  • 3 skills with low description scores (<70)
  • 10 skills missing negative constraints
  • 18 skills missing category assignment
  • 1 trigger conflict detected

Fix all automatically? (y/n)
```

Onboarding runs only once. Say "full report" anytime to see it again.

---

## Negative Constraints (When NOT to Fire)

The single most effective way to prevent false activations. Every skill description must specify both **when to trigger** and **when NOT to trigger**.

### The Four-Part Formula

```
[Trigger condition] + [Negative constraint] + [Capability declaration] + [Search vocabulary]
```

**Example:**
```
Use when creating, editing, or auditing PowerPoint presentations (.pptx).
Do NOT use for Google Slides, Keynote, or general document editing.
Covers layouts, placeholders, charts, notes, and visual QA.
Triggers on: PPT, PPTX, slides, deck, presentation, 幻灯片, 演示文稿.
```

### Why It Matters

Without negative constraints, a "search" skill might trigger for code search, file search, and web search. With them:

```
// Good — clear boundary
"Use when the user asks to search the web.
 Do NOT use for searching local files, code, or GitHub issues."

// Bad — no boundary
"Use when the user asks to search for information online."
```

### Negative Constraint Templates

| Template | When to Use | Example |
|----------|-------------|--------|
| `Do NOT use for [adjacent domain].` | Two skills cover similar verbs on different targets | `Do NOT use for PDF editing or document creation.` |
| `Not for [common false trigger phrase].` | Users often phrase requests ambiguously | `Not for creating new presentations from scratch.` |
| `Do NOT invoke when [specific condition].` | Skill has prerequisites or constraints | `Do NOT invoke when the user only wants to read (not edit) the file.` |
| `This skill does NOT handle [capability]. Use [other skill] instead.` | Direct hand-off to another skill | `This skill does NOT handle image generation. Use the image_generate tool instead.` |

### Audit & Auto-Generate

```bash
# Check which skills are missing negative constraints
python3 scripts/audit_skills.py --routing

# Generate suggested negative constraints for skills missing them
python3 scripts/audit_skills.py --negative-samples
```

Output:
```
📌 github (uncategorized)
   Current: Use when the user asks to interact with GitHub...

   Suggested negative constraint:
   "Do NOT use for code-review-and-quality, git-workflow-and-versioning.
    Those have dedicated skills."
```

**Scoring impact:** Missing negative constraints now costs **−15 points** (was −5). Skills with explicit negatives get a +5 bonus.

---

## Hierarchical Routing (Layered Dispatch)

When skill count grows beyond ~15, flat matching degrades — skills compete with each other, token budget inflates, and false triggers multiply. Hierarchical routing solves this with **two-stage dispatch**.

### How It Works

```
User query
    ↓
Layer 1: Category matching ("Is this about coding? documents? system?")
    ↓
Layer 2: Skill matching within winning category ("Which coding skill?")
```

Skills in different categories **never compete** with each other.

### Setup: Assign Categories

Add an optional `category` field to each skill's YAML frontmatter:

```yaml
---
name: github
category: coding
description: Use when the user asks to interact with GitHub...
---
```

### Standard Categories

| Category | Covers |
|----------|--------|
| `coding` | GitHub, code review, git workflow, debugging, implementation |
| `documents` | Feishu docs, PPTX, PDF, README, writing |
| `system` | Healthcheck, node-connect, auto-updater, security |
| `communication` | Search, weather, translations |
| `creative` | Image generation, music, video, prompt optimization |
| `meta` | Skill compass, skill creator, skill vetter, onboarding |
| `reasoning` | Self-discover, self-refine, cognitive frameworks |

### Audit Routing Health

```bash
python3 scripts/audit_skills.py --routing
```

Output:
```
Category            Skills    Chars   % Budget
──────────────────────────────────────────────────
coding                  5      1200      23.0%
documents               4       980      18.7%
system                  3       720      13.7%
uncategorized           2       510       9.7%  ⚠️

📋 Negative Constraints: 9/14 have "Do NOT use for..."
   ⚠️  5 skill(s) missing negative constraints

⚡ Cross-Category Keyword Leaks (1):
   coding ↔ documents (32% overlap)
      Shared: file, create, edit, write
```

### Benefits

- **Lower token pressure** — only relevant category descriptions need detailed parsing
- **Fewer false triggers** — skills in different categories never compete
- **Scales better** — adding skill #30 doesn't degrade skill #5's accuracy
- **Built-in disambiguation** — category separation provides baseline boundary even without per-skill negatives

For advanced strategies (sub-categories, multi-level hierarchies), see [`references/hierarchical-routing.md`](references/hierarchical-routing.md).

---

## Commands

```bash
# ── Core Workflow ──

# One-command setup: audit + auto-fix + AI prompt (also triggers onboarding)
python3 scripts/audit_skills.py --init

# Audit only — scan and score all skills
python3 scripts/audit_skills.py

# Auto-fix YAML syntax errors (creates backup automatically)
python3 scripts/audit_skills.py --fix

# Generate AI prompt to rewrite bad descriptions
python3 scripts/audit_skills.py --suggest

# JSON output for CI/CD pipelines
python3 scripts/audit_skills.py --json

# ── Routing & Negative Constraints ──

# Analyze hierarchical routing health
python3 scripts/audit_skills.py --routing

# Generate negative constraint suggestions for skills missing them
python3 scripts/audit_skills.py --negative-samples

# ── Backup & Rollback ──

# Snapshot all SKILL.md files
python3 scripts/audit_skills.py --backup

# List available backups
python3 scripts/audit_skills.py --list-backups

# Rollback to latest backup
python3 scripts/audit_skills.py --rollback

# Rollback to a specific backup
python3 scripts/audit_skills.py --rollback --backup-id 20260614-151204

# ── Upstream Feedback ──

# Generate GitHub issue drafts to share fixes with skill authors
python3 scripts/audit_skills.py --feedback
```

---

## The Self-Healing Loop

`--init` runs the full setup in one pass — audit, auto-fix, and AI prompt generation:

```
  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │  1. Audit    │────▶│  2. Fix YAML │────▶│  3. Suggest prompt│
  │  (find bugs) │     │  (auto patch)│     │  (AI rewrites)    │
  └──────────────┘     └──────────────┘     └──────────────────┘
         ▲                                         │
         │         Agent applies rewrites          │
         └─────────────────────────────────────────┘
                     Re-audit to verify
```

| Step | Command | What happens | Needs human? |
|------|---------|-------------|--------------|
| **Audit** | `--init` or bare | Scans all SKILL.md files, scores each 0–100 | No |
| **Auto-fix** | `--fix` or `--init` | Fixes YAML syntax errors, creates backup first | No |
| **Suggest** | `--suggest` or `--init` | Outputs a prompt with rules + context for each failing skill | No |
| **Rewrite** | Agent reads the prompt | Rewrites descriptions following the rules | No — agent does it |
| **Verify** | bare | Re-run audit to confirm scores improved | No |

---

## How Scoring Works

Each skill gets a score 0–100 based on six factors:

| Factor | Weight | What it checks |
|--------|--------|---------------|
| **Trigger condition** | ±35 | Does the description say *when* to fire? (`"Use when..."`) |
| **Negative constraint** | ±15 | Does it say what NOT to fire on? (`"Do NOT use for..."`) |
| **Language strength** | ±15 | Directive (`"ALWAYS invoke"`) vs passive (`"Helps with"`) |
| **YAML validity** | Pass/fail | Does frontmatter parse without errors? |
| **Description length** | ±15–30 | Under 350 chars, over 30 chars, enough keywords (≥10 words) |
| **Conflict detection** | Advisory | Do descriptions overlap with other skills? (Jaccard > 0.4) |

**Real data:** Directive descriptions (`"Use when..."`) achieve ~100% activation rate. Passive descriptions (`"Helps with..."`) only ~37%. *(Source: 650-skill activation experiment, Ivan Seleznov, Medium)*

---

## What Gets Fixed Automatically vs. What Needs the Agent

| Problem | Prevalence | Who fixes it | How |
|---------|-----------|-------------|-----|
| Missing trigger condition | 65% | Agent (via `--suggest`) | Rewrites with `"Use when..."` |
| Missing negative constraint | common | Script + Agent | `--negative-samples` suggests, agent applies |
| No category assigned | common | Script (advisory) | `--routing` flags uncategorized skills |
| Weak/passive language | common | Agent (via `--suggest`) | Rewrites to directive form |
| YAML syntax errors | 15% | Script (`--fix`) | Quotes unquoted colons automatically |
| Description too long | 10% | Script (advisory) | Flags for trimming |
| Description overlap | 5% | Agent (judgment call) | Add `"Do NOT use for..."` constraints |
| Cross-category keyword leak | rare | Script (advisory) | `--routing` flags shared keywords |
| Token budget exceeded | rare | Script (advisory) | Reports total chars across all skills |

---

## Backup & Rollback

Every `--fix` and `--init` automatically creates a backup before modifying files:

| Command | What it does |
|---------|-------------|
| `--backup` | Snapshot all SKILL.md files to `~/.skill-compass-backups/` |
| `--list-backups` | Show all snapshots with timestamps and file counts |
| `--rollback` | Restore everything from the latest backup |
| `--rollback --backup-id <ID>` | Restore from a specific backup |

---

## Upstream Feedback

`--feedback` compares your improved descriptions against the last backup and generates **GitHub issue drafts** to share with the original skill authors:

```
📧  UPSTREAM FEEDBACK

Found 1 improved description(s).

──────────────────────────────────────
1. multi-search-engine
──────────────────────────────────────

Repo: https://github.com/Thomaszhou22/multi-search-engine

Submit with:
  gh issue create -R Thomaszhou22/multi-search-engine \
    --title "Improve description for reliable agent triggering" \
    --body "..."
```

This creates a community improvement loop: fix locally → share upstream → all users benefit.

---

## Install

```bash
# ClawHub
clawhub install skill-compass-guardian

# Or from source
git clone https://github.com/Thomaszhou22/skill-compass.git
cp -r skill-compass ~/.openclaw/skills/
```

Requires Python 3.8+. No other dependencies.

---

## Files

```
skill-compass/
├── SKILL.md                        # Diagnostic workflow + fix guide for agents
├── scripts/
│   └── audit_skills.py             # Automated scanner (Python 3, no deps)
├── references/
│   ├── failure-patterns.md         # 6 failure patterns with real examples
│   └── hierarchical-routing.md     # Layered dispatch guide & best practices
└── README.md
```

## Compatibility

- ✅ OpenClaw
- ✅ Claude Code
- ✅ Cursor, Codex CLI, Gemini CLI (anything using SKILL.md)
- ✅ Any platform following the [agentskills.io](https://agentskills.io) standard

## License

MIT-0 — Free to use, modify, and distribute. No attribution required.
