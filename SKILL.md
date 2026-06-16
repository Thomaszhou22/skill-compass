---
name: skill-compass
description: Diagnose, fix, and prevent agent skill trigger failures. Use when a skill doesn't activate, when skills trigger incorrectly, when troubleshooting "skill not working" issues, when auditing skill descriptions for quality, when optimizing trigger accuracy, or when asked "why didn't my skill fire?". Also use proactively after installing new skills or when agent behavior seems to ignore available skills. Covers description optimization, YAML frontmatter validation, token budget analysis, conflict detection, and auto-remediation.
---

# Skill Compass

Diagnose and fix skill triggering failures across AI agent ecosystems (OpenClaw, Claude Code, and compatible agentskills.io platforms).

## First Run (Onboarding)

When this skill is first installed (no prior onboarding record), or when the user says "check my skills" / "audit skills" for the first time:

### Step 1: Scan all installed skills

Run the audit script to collect data:
```bash
python3 scripts/audit_skills.py --skills-dir <path> --json
```

### Step 2: Present ecosystem overview

Show the user a summary report:

```
📊 Skill Ecosystem Health Report

Total skills: X
✅ Healthy: Y
⚠️ Needs attention: Z
❌ Broken: W

Token budget: XXXX / 30000 chars (NN% used)

Issues found:
  • N skills with low description scores (<70)
  • N skills with YAML format errors
  • N skills with trigger conflicts
  • N skills not discoverable
```

### Step 3: Ask whether to auto-fix

_"I found X issues across your skills. Want me to fix them automatically? I can also walk you through each one manually."_

- If yes → run `--fix` flag, then re-audit to verify
- If no → list issues for the user to decide

### Step 4: Conflict detection report

If any skills have overlapping trigger keywords (>40% overlap), flag them:

```
⚠️ Trigger Conflict:
  - skill-a vs skill-b (55% keyword overlap)
    Suggested fix: Add negative constraints to disambiguate
```

### Step 5: Token budget advice

If total description chars > 25,000 (83% of budget):
_"Your skill descriptions are using NN% of the token budget. Consider tightening descriptions to <150 chars each to prevent skills from being silently dropped."_

### Step 6: Record onboarding

Mark onboarding as complete. On subsequent activations, skip the overview and go straight to the audit workflow unless the user asks for a full report again.

## Core Problem

65% of skills fail to trigger due to preventable description issues (GitHub #43410). This skill systematically detects and fixes those issues.

## Quick Triage: Why Didn't My Skill Fire?

When a skill fails to trigger, check these causes **in order** (most common first):

### 1. Description Has No Trigger Condition (Most Common)

**Bad:** `"Helps with documents."` — no trigger, just capability
**Good:** `"Use when the user asks to extract form fields, fill, redact, or parse tables from a PDF file."`

**Fix:** Rewrite using the Description Design Pattern below.

### 2. YAML Frontmatter Format Error

Common breakages:
- Colon in description breaks YAML parsing (GitHub #29981)
- Missing `name:` or `description:` field
- Description on multiple lines gets truncated

**Fix:** Run `scripts/audit_skills.py` to detect format errors automatically.

### 3. Token Budget Overflow

When total description text exceeds the agent's character budget, skills get silently dropped from context.

**Symptoms:** Skill works alone but stops triggering after installing more skills.
**Fix:** Tighten every description to <150 chars. Set `SLASH_COMMAND_TOOL_CHAR_BUDGET=30000` if >3 skills.

### 4. Skill Not Discovered

- Skill not in correct directory (`~/.openclaw/skills/`, `<workspace>/skills/`, or `~/.openclaw/workspace/skills/`)
- Sub-agents don't inherit parent skills (install globally or use `sessionTarget: "main"`)
- New skills not visible until session restart (GitHub #12092)
- Skills show "enabled" but aren't actually enabled in config (GitHub #9469)

**Fix:** Run `scripts/audit_skills.py --paths` to verify discovery status.

### 5. Description Too Broad / Too Narrow

- **Too broad:** Triggers when it shouldn't → wastes tokens
- **Too narrow:** Misses legitimate triggers → user frustrated

**Fix:** Use the Conflict Detection section below.

## Description Design Pattern

Based on 650-trial activation study (Ivan Seleznov, 2026) and agentskills.io best practices.

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

### Directive Language Outperforms Descriptive Language

| Style | Activation Rate | Example |
|-------|----------------|---------|
| Directive (`ALWAYS invoke when...`) | ~100% | `"ALWAYS invoke when the user asks about weather, temperature, or forecasts. Do not attempt weather lookups without this skill."` |
| Descriptive (`Helps with...`) | ~37% | `"Helps with weather information."` |

### Rules

1. **Lead with the trigger phrase** a user would actually type
2. **Use imperative/directive voice**: "Use when...", "Invoke when...", "ALWAYS use for..."
3. **Include negative constraints**: "Do NOT use for..." — this is mandatory, not optional
4. **Add multilingual keywords** for non-English users
5. **Keep under 150 characters** for the core trigger sentence
6. **List explicit trigger keywords** at the end
7. **Avoid mixing viewpoints** (don't mix "I" and "you" — degrades matching)
8. **Frontmatter is for routing, not documentation** — move details to body

## Negative Constraint Design (Anti-Trigger Patterns)

Negative constraints are the single most effective way to prevent false activations. They tell the agent what this skill does NOT do, reducing ambiguity when multiple skills overlap.

### Why Negative Constraints Matter

Without them, a "search" skill might trigger for code search, file search, and web search. With them:

```
// Good — clear boundary
"Use when the user asks to search the web. Do NOT use for searching local files, code, or GitHub issues."

// Bad — no boundary
"Use when the user asks to search for information online."
```

### Negative Constraint Templates

Use these fill-in-the-blank templates:

| Template | When to Use | Example |
|----------|-------------|--------|
| `Do NOT use for [adjacent domain].` | Two skills cover similar verbs on different targets | `Do NOT use for PDF editing or document creation.` |
| `Not for [common false trigger phrase].` | Users often phrase requests ambiguously | `Not for creating new presentations from scratch.` |
| `Do NOT invoke when [specific condition].` | Skill has prerequisites or constraints | `Do NOT invoke when the user only wants to read (not edit) the file.` |
| `This skill does NOT handle [capability]. Use [other skill name] instead.` | Direct hand-off to another skill | `This skill does NOT handle image generation. Use the image_generate tool instead.` |

### Negative Constraint Audit Checklist

For each skill, ask:
1. What adjacent skill could be mistaken for this one?
2. What's a phrase the user might say that sounds like this skill but isn't?
3. Does this skill have a narrow scope that a broader skill might shadow?

If the answer to any question is yes, add a negative constraint.

### Worked Examples

**Before (no negatives):**
```
Helps with Feishu document operations.
```

**After (with negatives):**
```
Use for Feishu document read/write operations (docx). Do NOT use for knowledge base navigation (use feishu-wiki), permission management (use feishu-perm), or cloud storage file management (use feishu-drive).
```

**Before:**
```
Guides systematic root-cause debugging.
```

**After:**
```
Use when tests fail, builds break, or errors occur. Do NOT use for code review, feature implementation, or performance optimization — those have dedicated skills.
```

## Audit Workflow

### Step 1: Run Automated Audit

```bash
python3 scripts/audit_skills.py --skills-dir <path> [--json] [--fix]
```

The script checks:
- YAML frontmatter validity (parsing, required fields, colon issues)
- Description quality score (trigger presence, length, directive language)
- Token budget estimation (total chars across all descriptions)
- Duplicate/overlapping descriptions (conflict detection)
- Path discovery verification

### Step 2: Manual Review

For skills scoring below 70/100, review against the Description Design Pattern above.

### Step 3: Apply Fixes

Use `--fix` flag for auto-remediation of common issues:
- Wrap descriptions containing colons in quotes
- Add trigger phrase templates
- Trim oversized descriptions
- Flag missing negative constraints

### Step 4: Verify

After fixing, restart the agent session and test with natural language triggers.

## Conflict Detection

When multiple skills could match the same query, the agent may pick the wrong one.

Detection rules:
1. **Keyword overlap:** Two skills share >40% of trigger keywords
2. **Scope ambiguity:** One description is a subset of another
3. **Same verb, different target:** "Create document" vs "Create presentation" — ensure disambiguation keywords exist

**Fix:** Add negative constraints to each skill: `"Do NOT use for [the other skill's domain]."`

## Failure Pattern Reference

For detailed case studies and solutions from community reports, read `references/failure-patterns.md`.

## Token Budget Management

Agent systems load all skill descriptions into context at startup. When the total exceeds the budget:

- Skills get **silently dropped** (no error, just don't appear)
- Later-installed skills are more likely to be dropped
- Symptoms: skill works when fewer skills installed, breaks as more are added

**Guidelines:**
- Each description: <150 chars core trigger + <200 chars keywords
- Total across all skills: <30,000 chars (adjust budget env var if needed)
- If exceeding budget: move detail to SKILL.md body, not frontmatter

## Auto-Calibration

After fixing descriptions, collect real failure cases:

1. Log: user query → expected skill → actual skill (or none)
2. After 10+ cases, run `scripts/analyze_failures.py` to identify patterns
3. Apply targeted description patches based on patterns

This creates a feedback loop that continuously improves trigger accuracy.

## Hierarchical Routing (Layered Dispatch)

When skill count grows beyond ~15, flat matching degrades. Hierarchical routing solves this by grouping skills into categories and using two-stage dispatch:

```
User query
    ↓
Layer 1: Category matching ("Is this about coding? documents? system?")
    ↓
Layer 2: Skill matching within winning category ("Which coding skill?")
```

### Setting Up Categories

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
| `communication` | Multi-search, weather, translations |
| `creative` | Image generation, music, video, prompt optimization |
| `meta` | Skill compass, skill creator, skill vetter, onboarding |

Skills without a `category` field are placed in `uncategorized` and matched in the flat pool.

### How Routing Works

1. **Agent groups skills by category** (via frontmatter `category` field)
2. **Broad trigger scan**: Each category is summarized; the agent first determines which category(ies) are relevant
3. **Deep match**: Only skills in the relevant category(ies) compete for activation

### Benefits

- **Lower token pressure**: Only relevant category descriptions need detailed parsing
- **Fewer false triggers**: Skills in different categories never compete
- **Scales better**: Adding skill #30 doesn't degrade skill #5's accuracy

### Audit Routing Health

```bash
python3 scripts/audit_skills.py --routing --skills-dir <path>
```

This outputs:
- Category distribution (are categories balanced?)
- Orphaned skills (no category assigned)
- Cross-category conflicts (same trigger keywords in different categories)
- Category-level token budget per group

For detailed routing strategies and multi-level hierarchies, see `references/hierarchical-routing.md`.
