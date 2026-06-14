## 你的 AI Skill 为什么总是不触发？

用 Claude Code / Cursor / OpenClaw 的小伙伴注意了⚠️

你有没有遇到过这种情况：明明装了某个 Skill，但 AI 就是不用它？你说的话它接不住，非要手动提醒？

**不是 AI 笨，是 Skill 的"自我介绍"写得有问题。**

我调研了社区里 650 个 Skill 的触发数据，发现一个离谱的事实：
👉 **65% 的 Skill 因为 description 里没有写触发条件，永远不会被 AI 主动调用。**

举个🌰：
- ❌ "多搜索引擎整合工具" → AI 不知道什么时候该用它
- ✅ "Use when the user asks to search the web..." → 触发率直接拉满

本质上，Agent 每次对话前会读一遍所有 Skill 的 description，然后做语义匹配。description 没写"我什么时候该被触发"，AI 就匹配不上。

所以我做了一个工具：**Skill Compass** 🧭

一行命令扫描你所有 Skill，给每个打分 0-100，告诉你哪个有问题、问题是什么、怎么修。还能自动生成一段 prompt，丢给你的 AI Agent 让它自己改。

改完之后再跑一次，分数从 50 飙到 100，全程不用手动编辑。

更贴心的是：
- 📦 改之前自动备份，改坏了 `--rollback` 一键回滚
- 📬 改好了能生成 GitHub Issue，发给 Skill 原作者，让所有人都受益

**三步搞定：**
```
python3 audit_skills.py --init      # 体检 + 修复
# 把生成的 prompt 粘贴给 AI
python3 audit_skills.py             # 验证分数
```

支持所有用 SKILL.md 格式的平台：OpenClaw / Claude Code / Cursor / Codex CLI / Gemini CLI

🔗 工具地址放评论区了，自取～
