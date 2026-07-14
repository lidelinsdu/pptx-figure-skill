# PPTX Figure Style Generator v2

根据 .md 文件生成复刻源PPTX绘图风格的学术图表。

> v2 基于对源PPTX全部41页的逐页渲染视觉分析 + OOXML形状级提取重建（41个并行视觉
> 分析agent + 3路综合归纳）。核心修正：源PPT的主导模式是"浅色tint填充+黑1.5pt
> 边框+黑字"，深饱和色只出现在标题条/页签/结论条等窄条元素上。

## 文件结构

```
.claude/skills/pptx-figure/
├── skill.md                                    # 主技能定义（Claude入口）
├── README.md                                   # 本文件
├── generate-figure.py                          # 生成脚本（4种版式原型）
├── style-reference/
│   └── complete-style-guide.md                 # 完整风格指南v2（配色/组件/原型/反面清单）
├── templates/
│   ├── mermaid/
│   │   ├── flowchart-template.mmd              # 流程图Mermaid模板
│   │   ├── architecture-template.mmd           # 分层架构Mermaid模板
│   │   ├── concept-map-template.mmd            # 总-分关系Mermaid模板
│   │   └── pptx-mermaid-theme.json             # Mermaid主题配置
│   └── python/
│       └── pptx_style_base.py                  # 组件库（卡片/骑缝标签/燕尾页签/块箭头…）
└── examples/
    ├── research-content.md                     # 示例输入
    ├── sample_route.{svg,png}                   # 原型A: 燕尾页签+泳道
    ├── sample_panel.{svg,png}                   # 原型B: 多栏技术板
    ├── sample_architecture.{svg,png}           # 原型C: 分层架构
    ├── sample_overview.{svg,png}               # 原型D: 总-分关系
    └── sample_diagram.mermaid                  # Mermaid输出示例
```

## 使用方法

```bash
# 生成 PPTX 可导入的矢量 SVG（推荐；无需 matplotlib）
python .claude/skills/pptx-figure/generate-figure.py examples/research-content.md -o out.svg

# 自动选型生成 PNG（需 matplotlib）
python .claude/skills/pptx-figure/generate-figure.py examples/research-content.md -o out.png

# 指定版式: route / panel / architecture / overview
python .claude/skills/pptx-figure/generate-figure.py examples/research-content.md -o out.svg --type route

# Mermaid代码
python .claude/skills/pptx-figure/generate-figure.py examples/research-content.md -o out.mermaid
```

输出格式由 `-o` 扩展名决定：`.svg`（矢量，PowerPoint 可导入并"转换为形状"）、`.png`（栅格）、`.mermaid`（源码）。

## 风格体系（速览）

- **配对律**：浅底+黑1.5pt边+黑字（≈70%）；深饱和底+白粗体（≈20%，仅标题/导航/结论层）
- **色系**：蓝/橙/金/绿/紫/灰六系，每系"近白panel→浅band→中浅card→饱和accent"四档
- **连接**：金黄块箭头=支撑主线，蓝块箭头=数据流，白空心=轻量流，细线=微观汇聚，虚线=只表分组
- **标志手法**：骑缝标签（饱和标题条骑压虚线分组框上边线）、燕尾页签行（homePlate+chevron）、
  竖排侧标签、全宽层带+左侧标签、一区一色

详见 `style-reference/complete-style-guide.md`。
