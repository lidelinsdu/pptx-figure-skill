# pptx-figure — Agent Skill (AGENTS.md)

> 本文件让 **OpenAI Codex** 及任何读取 `AGENTS.md` 的智能体原生识别本技能。
> Claude Code 读取同目录的 `skill.md`（含 frontmatter）。两者共用下方同一个 Python 引擎。

## 能力

把 Markdown 转成**学术项目申报书风格**的结构图：技术路线图 / 分层架构图 / 总-分关系图 / 多栏模块图。
输出 **PowerPoint 可导入的矢量 SVG**（可"转换为形状"变原生可编辑图形）、PNG 或 Mermaid。

风格逆向自某 41 页学术申报 PPT 图集：浅色 tint 填充 + 黑 1.5pt 边框 + 黑字为主导；
深饱和色只用于标题条/页签/结论条；sysDash 虚线分组配骑缝标签；金黄块箭头做支撑主线；一区一色。

## 何时使用

用户要"画技术路线图 / 架构图 / 研究内容总览 / 总-分关系图"，或需要一张能放进 PPT 的矢量结构图时。

## 如何调用（命令行，工具无关）

核心是一个纯 Python 脚本，无需联网；SVG 输出零第三方依赖。
路径按安装位置调整（下例假设脚本在 `.claude/skills/pptx-figure/` 下）：

```bash
python .claude/skills/pptx-figure/generate-figure.py <input.md> -o <out.svg> [--type TYPE]
```

- **输出扩展名决定格式**：`.svg`（矢量，PPT"插入>图片"可导入并"转换为形状"；无需 matplotlib）、
  `.png`（栅格，需 matplotlib）、`.mermaid`（源码）。
- 不指定 `--type` 时按标题关键词自动选型。

版式 `--type`：

| 值 | 适用 | 结构 |
|---|---|---|
| `route` | 技术路线/阶段流程 | 燕尾页签行 + 等宽泳道 + 骑缝标签分组 + 结论条 |
| `panel` | 无阶段的模块并列 | 多栏浅底技术板 + 金黄块箭头串联 |
| `architecture` | 平台/系统分层、支撑关系 | 全宽横带层叠 + 左侧标签 + 层间支撑箭头 |
| `overview` | 研究内容总览、A+B+C | 外框 + 骑缝总标题条 + 并列虚线分组 + 加号 |

## 输入 MD 约定

```markdown
# 图表总标题            ← 含"路线/架构/总览"等词可触发自动选型
## 阶段/层/分组标题      ← 章节 = 页签/层/分组
- 条目1                ← route/panel：首条 = 深色骑缝标签
- 条目2                ← 其余 = 浅色内容卡
- 条目3                ← route ≥3 条时末条 = 底部结论条
```

## 自定义复杂图（组件库）

```python
import sys; sys.path.insert(0, '.claude/skills/pptx-figure/templates/python')
import pptx_style_base as S
S.set_backend('svg')                 # 'svg'矢量 / 'mpl'栅格
fig, ax = S.init_figure()            # 1280×720，原点左下
S.card(ax, x, y, w, h, family='blue', text='内容卡')      # 浅底黑边黑字
S.deep_card(ax, x, y, w, h, family='blue', text='标题卡')  # 饱和底白粗体
S.dashed_group(ax, x, y, w, h, label='骑缝标签')          # 虚线分组+骑缝标签
S.chevron_row(ax, x, y, [320]*3, 52, ['一','二','三'])     # 燕尾页签
S.block_arrow(ax, cx, cy, 'up', style='gold', note='支撑') # 块状支撑箭头
S.save(fig, 'out.svg')               # 扩展名决定格式
```

完整配色/组件词汇表/9 种布局原型/反面清单见 `style-reference/complete-style-guide.md`。

## 依赖

- SVG 输出：仅 Python 标准库。
- PNG 输出：`pip install matplotlib` + 中文字体（微软雅黑 / Noto Sans CJK / 文泉驿）。
