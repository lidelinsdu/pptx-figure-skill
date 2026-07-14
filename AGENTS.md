# AGENTS.md

本仓库提供 **pptx-figure** 技能：把 Markdown 转成学术申报书风格的结构图，
输出 PowerPoint 可导入的矢量 SVG（可"转换为形状"编辑）、PNG 或 Mermaid。
对 OpenAI Codex、Claude Code 及任何读取 `AGENTS.md` 的智能体通用。

完整说明见 **`.claude/skills/pptx-figure/AGENTS.md`**（风格规则见其中链接的 `style-reference/complete-style-guide.md`）。

快速调用（SVG 输出零第三方依赖）：

```bash
python .claude/skills/pptx-figure/generate-figure.py <in.md> -o <out.svg> [--type route|panel|architecture|overview]
```

- `.svg` = 矢量（PPT 可导入/转形状）；`.png` = 栅格（需 matplotlib）；`.mermaid` = 源码
- 不给 `--type` 时按 `# 标题` 关键词自动选型

Claude Code 用户：`.claude/skills/pptx-figure/` 已是原生 Skill（`skill.md`），直接 `/pptx-figure` 或自然语言触发。
Codex 用户：本文件即入口；可选把 `.claude/skills/pptx-figure/prompts/pptx-figure.md` 复制到 `~/.codex/prompts/` 得到 `/pptx-figure` 命令。
