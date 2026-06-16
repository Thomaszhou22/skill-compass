# Hierarchical Routing — Detailed Guide

How to organize skills into layers for scalable, accurate triggering.

## The Problem with Flat Routing

When all skills sit in a single flat list, the agent must compare every query against every skill description simultaneously. This works for ≤10 skills but degrades rapidly:

| Skills | Avg. descriptions to compare | Token budget used | False trigger rate |
|--------|------------------------------|-------------------|-------------------|
| 5      | 5                            | ~1,500 chars      | ~3%               |
| 15     | 15                           | ~4,500 chars      | ~8%               |
| 30     | 30                           | ~9,000 chars      | ~15%              |
| 50     | 50                           | ~15,000 chars     | ~25%+             |

## Two-Stage Dispatch

### Stage 1: Category Resolution

The agent first determines which **category** of skill is relevant. Categories are broad buckets defined by the `category` field in frontmatter:

```yaml
# In each skill's SKILL.md frontmatter:
---
name: github
category: coding
description: Use when the user asks to interact with GitHub...
---
```

The category scan is implicit — the agent sees category labels as part of its skill list and naturally narrows down. No extra configuration needed beyond adding the field.

### Stage 2: Intra-Category Skill Matching

Once the category is determined, only skills within that category compete for activation. This means:

- A `coding` skill never competes with a `documents` skill
- Negative constraints primarily disambiguate **within** the same category
- Cross-category false triggers are eliminated by structure, not by description length

## Standard Category Taxonomy

| Category | Description | Example Skills |
|----------|-------------|----------------|
| `coding` | Code writing, review, VCS, debugging | github, code-review, git-workflow, debugging, incremental-implementation |
| `documents` | Document creation and editing | feishu-doc, feishu-wiki, powerpoint-pptx, pdf, better-readme |
| `system` | System administration and health | healthcheck, node-connect, auto-updater |
| `communication` | Search, weather, translations | multi-search-engine, weather, prompt-optimizer |
| `creative` | Generative AI output | image generation, music, video, skill-creator |
| `meta` | Skill management itself | skill-compass, skill-vetter, skill-creator, onboarding |
| `reasoning` | Cognitive frameworks | self-discover, self-refine |

## Category-Level Negative Constraints

In addition to per-skill negatives, you can define category-level boundaries:

```
# Implicit in category structure
coding skills: Do NOT trigger for document formatting or system admin
documents skills: Do NOT trigger for code editing or deployment
system skills: Do NOT trigger for content creation
```

This means even without explicit "Do NOT use for..." in each description, the category separation provides a baseline of disambiguation.

## Multi-Level Hierarchies (Advanced)

For very large skill collections (50+), consider sub-categories:

```yaml
---
name: git-workflow
category: coding
subcategory: version-control
description: Use when making commits, branches, resolving merge conflicts...
---
```

Three-stage dispatch: Domain → Sub-domain → Specific skill.

## Routing Health Audit

Run `python3 scripts/audit_skills.py --routing` to check:

### 1. Category Distribution
```
Category   Skills   Token Budget
────────   ──────   ────────────
coding        5       1,200 chars
documents     4         980 chars
system        3         720 chars
meta          3         690 chars
uncategorized 2         510 chars  ⚠️  Assign categories
```

### 2. Cross-Category Keyword Leaks
Flags when two skills in different categories share >30% trigger keywords — this can cause the agent to scan both categories when only one is relevant.

### 3. Category Token Budget
Per-category budget helps identify groups that are too heavy:

```
⚠️  Category "coding" uses 4,200 chars (28% of total budget)
    Consider splitting into "coding/frontend" and "coding/backend"
```

## Best Practices

1. **Assign categories early** — retrofitting is painful with 30+ skills
2. **Keep categories ≤8 skills each** — if a category grows beyond 8, consider sub-categories
3. **Use negative constraints within categories** — that's where the real competition is
4. **Don't over-engineer** — if you have <15 skills, flat routing is fine
5. **Review quarterly** — as you add skills, categories may need rebalancing
