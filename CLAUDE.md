# PPTX Figure Style Generator

本项目包含一个完整的PPTX绘图风格分析与复现系统（v2，基于41页逐页视觉分析+OOXML提取重建）。

## Skills 可用

- `pptx-figure` — 根据MD文件生成源PPTX风格的学术图表（四种版式原型，输出SVG矢量/PNG/Mermaid）

## 目录结构

```
.claude/skills/pptx-figure/
├── skill.md                                     # 技能主定义
├── generate-figure.py                           # 生成脚本（route/panel/architecture/overview）
├── style-reference/complete-style-guide.md      # 完整风格指南v2（配色/组件词汇/9种布局原型/反面清单）
├── templates/mermaid/                           # Mermaid模板与主题
├── templates/python/pptx_style_base.py          # 双后端组件库（SVG矢量+matplotlib栅格；卡片/骑缝标签/燕尾页签/块箭头…）
└── examples/                                    # 示例输入与四种版式示例输出
```

## 使用方式

```bash
# 生成 PowerPoint 可导入的矢量 SVG（推荐；无需 matplotlib）
python .claude/skills/pptx-figure/generate-figure.py research.md -o figure.svg

# 自动选型生成 PNG（需 matplotlib）
python .claude/skills/pptx-figure/generate-figure.py research.md -o figure.png

# 指定版式原型: route(燕尾泳道) / panel(多栏板) / architecture(分层) / overview(总-分)
python .claude/skills/pptx-figure/generate-figure.py research.md -o figure.svg --type route

# 生成Mermaid代码
python .claude/skills/pptx-figure/generate-figure.py research.md -o diagram.mermaid
```

输出格式由 `-o` 扩展名决定：`.svg` 矢量（PPT 可"插入>图片"导入并"转换为形状"编辑，
零第三方依赖）、`.png` 栅格（需 matplotlib）、`.mermaid` 源码。

## 风格签名

分析自某41页学术项目申报PPT图集（41页，16:9，均值≈50形状/页）：
**浅色tint填充+黑1.5pt实线边框+黑字**为主导；深饱和色仅用于标题条/页签/结论条（白粗体）；
sysDash虚线分组框配骑缝标签；金黄FFC000块箭头做支撑主线；一区一色、三档同色相递进。
