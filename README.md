# 🧭 Skill Compass

Audit, fix, and optimize agent skill descriptions so they trigger reliably. Works with OpenClaw, Claude Code, Cursor, and any agentskills.io-compatible platform.

**The problem:** 65% of skills never trigger because their descriptions don't tell the agent *when* to fire. Skill Compass finds these and fixes them — automatically where possible, AI-assisted where not.

## Install

```bash
# ClawHub
clawhub install skill-compass-guardian

# Or from source
git clone https://github.com/Thomaszhou22/skill-compass.git
cp -r skill-compass ~/.openclaw/skills/
```

Requires Python 3.8+. No other dependencies.

## Quick Start

```bash
# Step 1: Audit — find broken skills
python3 scripts/audit_skills.py

# Step 2: Auto-fix YAML syntax issues (auto-creates backup)
python3 scripts/audit_skills.py --fix

# Step 3: Generate AI prompt to rewrite bad descriptions
python3 scripts/audit_skills.py --suggest

# JSON output for CI/CD pipelines
python3 scripts/audit_skills.py --json

# Backup all SKILL.md files manually
python3 scripts/audit_skills.py --backup

# List available backups
python3 scripts/audit_skills.py --list-backups

# Rollback to latest backup (or specify --backup-id)
python3 scripts/audit_skills.py --rollback
python3 scripts/audit_skills.py --rollback --backup-id 20260614-151204
```

## The Self-Healing Loop

The three steps above form a closed loop that an agent can run by itself — no human editing required:

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
| **Audit** | `audit_skills.py` | Scans all SKILL.md files, scores each 0–100 | No |
| **Auto-fix** | `audit_skills.py --fix` | Fixes YAML syntax errors in-place | No |
| **Suggest** | `audit_skills.py --suggest` | Outputs a prompt with rules + context for each failing skill | No — paste it to any AI agent |
| **Rewrite** | Agent reads the suggest prompt | Rewrites descriptions following the rules | No — agent does it |
| **Verify** | `audit_skills.py` again | Confirm scores improved | No |
| **Backup** | `audit_skills.py --backup` | Snapshot all SKILL.md files | No |
| **Rollback** | `audit_skills.py --rollback` | Restore from backup if AI broke something | No |
| **List backups** | `audit_skills.py --list-backups` | Show all available snapshots | No |

### What a full run looks like

```
🧭  SKILL COMPASS — AUDIT REPORT

📂 Directory: ~/.openclaw/skills
📊 Total skills: 18
⚠️  Issues found: 11

📈 Score Summary:
   Average score: 81/100
   ✅ Passing (≥70): 12
   ⚠️  Needs work (<70): 6
   🔴 Critical (<30): 0

⚠️  multi-search-engine — Score: 50/100
   • NO_TRIGGER: Missing trigger condition
   • WEAK_LANG: Uses passive language instead of directive
   💡 Add trigger phrases: "Use when...", "Invoke when..."

✅ powerpoint-pptx — Score: 100/100
```

### What `--suggest` generates

```
You are a skill description optimizer. Your job is to rewrite SKILL.md
frontmatter descriptions so they trigger reliably in AI agents.

## Rules
1. Start with "Use when..." or "ALWAYS invoke when..."
2. Include specific trigger keywords the user might say
3. Add "Do NOT use for..." to prevent false triggers when relevant
4. Keep the description under 350 characters
5. Do NOT change the skill name — only the description

## Skills to Fix

### 1. multi-search-engine (Score: 50/100)
**File:** `~/.openclaw/skills/multi-search-engine/SKILL.md`
**Current description:** Multi search engine integration with 16 engines...
**Issues:** NO_TRIGGER; WEAK_LANG
**Hints:** Add trigger phrases; Replace passive language

...

After generating all rewrites, apply them to the respective SKILL.md files.
```

Paste this to any AI agent (Claude, GPT, Gemini, etc.) and it rewrites every bad description following the rules. Re-run the audit to verify improvements.

## How Scoring Works

Each skill gets a score 0–100 based on five factors:

| Factor | Weight | What it checks |
|--------|--------|---------------|
| **Trigger condition** | ±35 | Does the description say *when* to fire? (`"Use when..."`) |
| **Language strength** | ±15 | Directive (`"ALWAYS invoke"`) vs passive (`"Helps with"`) |
| **YAML validity** | Pass/fail | Does frontmatter parse without errors? |
| **Description length** | ±15–30 | Under 350 chars, over 30 chars, enough keywords (≥10 words) |
| **Conflict detection** | Advisory | Do descriptions overlap with other skills? (Jaccard > 0.4) |

**Real data:** Directive descriptions (`"Use when..."`) achieve ~100% activation rate. Passive descriptions (`"Helps with..."`) only ~37%. *(Source: 650-skill activation experiment, Ivan Seleznov, Medium)*

## What Gets Fixed Automatically vs. What Needs the Agent

| Problem | Prevalence | Who fixes it | How |
|---------|-----------|-------------|-----|
| Missing trigger condition | 65% | Agent (via `--suggest` prompt) | Rewrites description with `"Use when..."` |
| Weak/passive language | common | Agent (via `--suggest` prompt) | Rewrites to directive form |
| YAML syntax errors | 15% | Script (`--fix` flag) | Quotes unquoted colons automatically |
| Description too long | 10% | Script (`--fix` flag) | Flags for manual trimming |
| Description overlap | 5% | Agent (judgment call) | Add `"Do NOT use for..."` constraints |
| Token budget exceeded | rare | Script (advisory) | Reports total chars across all skills |

## Files

```
skill-compass/
├── SKILL.md                        # Diagnostic workflow + fix guide for agents
├── scripts/
│   └── audit_skills.py             # Automated scanner (Python 3, no deps)
├── references/
│   └── failure-patterns.md         # 6 failure patterns with real examples
└── README.md
```

## Compatibility

- ✅ OpenClaw
- ✅ Claude Code
- ✅ Cursor, Codex CLI, Gemini CLI (anything using SKILL.md)
- ✅ Any platform following the [agentskills.io](https://agentskills.io) standard

## License

MIT-0 — Free to use, modify, and distribute. No attribution required.
