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

## Commands

```bash
# ── Core Workflow ──

# One-command setup: audit + auto-fix + AI prompt (recommended for first run)
python3 scripts/audit_skills.py --init

# Audit only — scan and score all skills
python3 scripts/audit_skills.py

# Auto-fix YAML syntax errors (creates backup automatically)
python3 scripts/audit_skills.py --fix

# Generate AI prompt to rewrite bad descriptions
python3 scripts/audit_skills.py --suggest

# JSON output for CI/CD pipelines
python3 scripts/audit_skills.py --json

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

### What `--init` looks like

```
🧭  SKILL COMPASS — SETUP GUIDE

📊 Scanned 18 skills in: ~/.openclaw/skills
   ✅ 15 passing  |  ⚠️  3 need work  |  🔴 0 critical
   Average score: 82/100

3 STEPS TO FIX YOUR SKILLS

Step 1/3: Auto-fix YAML syntax issues
Step 2/3: Generate an AI prompt to rewrite bad descriptions
Step 3/3: Paste the output to your AI agent

SKILLS THAT NEED ATTENTION (3)
  ⚠️  multi-search-engine (20/100) — NO_TRIGGER; SHORT
  ⚠️  github (20/100) — NO_TRIGGER; SHORT
  ⚠️  onboarding (20/100) — NO_TRIGGER; SHORT

▶  Running Step 1 (auto-fix YAML)...
   💾 Backup saved: ~/.skill-compass-backups/20260614-151204

▶  Step 2 preview — here's your AI prompt:
   (full prompt with rules + per-skill context)

⏮️  If something goes wrong, rollback with:
   python3 scripts/audit_skills.py --rollback
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
**Current description:** Multi search engine integration with 16 engines...
**Issues:** NO_TRIGGER; WEAK_LANG
**Hints:** Add trigger phrases; Replace passive language

...

After generating all rewrites, apply them to the respective SKILL.md files.
```

Paste this to any AI agent (Claude, GPT, Gemini, etc.) and it rewrites every bad description. Re-run the audit to verify.

## Backup & Rollback

Every `--fix` and `--init` automatically creates a backup before modifying files. You can also manage backups manually:

| Command | What it does |
|---------|-------------|
| `--backup` | Snapshot all SKILL.md files to `~/.skill-compass-backups/` |
| `--list-backups` | Show all snapshots with timestamps and file counts |
| `--rollback` | Restore everything from the latest backup |
| `--rollback --backup-id <ID>` | Restore from a specific backup |

```
📦 Available Backups (newest first):

  ID: 20260614-151204  |  Files: 18  |  Dir: ~/.openclaw/skills

Restore with: python3 audit_skills.py --rollback [--backup-id <ID>]
```

If the AI rewrites a description and it breaks something — one command restores everything.

## Upstream Feedback

`--feedback` compares your improved descriptions against the last backup and generates **GitHub issue drafts** to share with the original skill authors. You decide which ones to submit.

```
📧  UPSTREAM FEEDBACK

Found 1 improved description(s). Review and submit the ones you want to share.

──────────────────────────────────────
1. multi-search-engine
──────────────────────────────────────

Repo: https://github.com/Thomaszhou22/multi-search-engine

Submit with:
  gh issue create -R Thomaszhou22/multi-search-engine \
    --title "Improve `multi-search-engine` description for reliable agent triggering" \
    --body "..."
```

The issue draft focuses on the skill's problem — not the tool that found it:

```
Title: Improve `multi-search-engine` description for reliable agent triggering

## Problem
The current description does not contain a trigger condition, so agents
often do not know when to activate this skill:
  description: Multi search engine integration with 16 engines...

## Suggested Fix
  description: Use when the user asks to search the web...

## Why This Matters
- ~65% of agent skills never fire due to missing trigger phrases
- Directive descriptions achieve ~100% activation rate
- Passive descriptions only ~37%

_Found via [Skill Compass](https://github.com/Thomaszhou22/skill-compass)_
```

This creates a community improvement loop: fix locally → share upstream → all users benefit.

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
| Missing trigger condition | 65% | Agent (via `--suggest`) | Rewrites description with `"Use when..."` |
| Weak/passive language | common | Agent (via `--suggest`) | Rewrites to directive form |
| YAML syntax errors | 15% | Script (`--fix`) | Quotes unquoted colons automatically |
| Description too long | 10% | Script (advisory) | Flags for trimming |
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
