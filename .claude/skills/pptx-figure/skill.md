---
name: pptx-figure
description: 根据MD文件生成源PPTX风格的学术绘图（浅色tint填充+黑1.5pt边框+黑粗体字体系）。支持燕尾页签泳道图、多栏技术板、分层架构图、总-分关系图四种版式原型，输出PNG或Mermaid。
---

# PPTX Figure Style Generator v2

根据输入的 Markdown 文件，生成复刻源 PPTX（某41页学术项目申报PPT图集，41页）绘图风格的学术图表。

## 风格签名（生成任何图之前先记住）

- **浅色tint填充 + 黑色1.5pt实线边框 + 黑色文字**是主导模式（约70%）；标题粗体、正文常规
- **深饱和色只用于窄条**：总标题条、燕尾页签、一级节点、结论条（配白粗体字；金色FFC000上配黑字）
- **sysDash虚线框=逻辑分组**，几乎总配"骑缝标签"（饱和色标题条骑压框上边线）
- **块状实心箭头做宏观流程**（金黄FFC000+黑描边=支撑主线；蓝=数据流；白底蓝边空心=轻量流），细线连接器只做微观汇聚
- **一区一色**：每栏/层一个色系，同色相"近白底板→中浅卡片→饱和标题"三档递进；每页≤4色系
- 反面清单（不要做）：大面积饱和色+白字内容区、无边框浅色卡、细线做主干、虚线表流向、投影/发光/3D、胶囊大圆角

完整规则见 `style-reference/complete-style-guide.md`（配色系统/组件词汇表/9种布局原型/反面清单）。

## 调用方式

```bash
# 自动选型生成PNG
python .claude/skills/pptx-figure/generate-figure.py content.md -o figure.png

# 指定版式原型
python .claude/skills/pptx-figure/generate-figure.py content.md -o f.png --type route         # 原型A 燕尾页签+泳道
python .claude/skills/pptx-figure/generate-figure.py content.md -o f.png --type panel         # 原型B 多栏技术板
python .claude/skills/pptx-figure/generate-figure.py content.md -o f.png --type architecture  # 原型C 分层架构
python .claude/skills/pptx-figure/generate-figure.py content.md -o f.png --type overview      # 原型D 总-分关系

# Mermaid代码输出
python .claude/skills/pptx-figure/generate-figure.py content.md -o diagram.mermaid
```

类型别名：`flowchart`/`roadmap`→route，`concept`→overview，`layered`→architecture，`board`→panel。

## 输入MD约定

```markdown
# 图表总标题                ← 页眉标题；含"路线/架构/总览"等词可触发自动选型

## 阶段/层/分组标题          ← 章节=页签/层/分组
描述行                      ← route类型中作为该栏结论条(可选)
- 条目1                     ← route/panel中: 首条=深色标题卡(骑缝标签)
- 条目2                     ←   其余条目=浅色内容卡
- 条目3                     ← route中≥3条时: 末条=底部结论条
```

标题含"核心/主题/总览/目标"的章节，其描述行会被 overview 用作中心总标题。

## 版式选择速查

| 内容语义 | 版式 | 视觉结构 |
|---|---|---|
| 阶段性流程/技术路线 | route | 燕尾页签行+等宽泳道面板+骑缝标签分组+结论条 |
| 无阶段的模块并列 | panel | 多栏浅底技术板+金黄块箭头串联 |
| 分层支撑关系 | architecture | 全宽横带层叠+左侧标签+层间金黄支撑箭头 |
| 总-分从属关系 | overview | 外框+骑缝总标题条+并列虚线分组+加号 |

## 自定义绘图（组件库API）

复杂图表直接用组件库编写Python：

```python
import sys
sys.path.insert(0, '.claude/skills/pptx-figure/templates/python')
import pptx_style_base as S

fig, ax = S.init_figure()                 # 1280×720坐标系，原点左下
S.page_header(ax, '页面标题')              # 左上角蓝块装饰+黑粗体标题
S.card(ax, x, y, w, h, family='blue', tier='card', text='内容卡')   # 浅底黑边黑字
S.deep_card(ax, x, y, w, h, family='blue', text='标题卡')           # 饱和底白粗体
S.dashed_group(ax, x, y, w, h, fill=('blue','panel'),
               label='骑缝标签', label_family='blue')               # 虚线分组+骑缝标签
S.chevron_row(ax, x, y, [320,320,320], 52, ['阶段一','阶段二','阶段三'],
              colors=['blue','orange','green'])                     # 燕尾页签行
S.block_arrow(ax, cx, cy, 'up', style='gold', note='支撑')          # 块状箭头+旁注
S.layer_band(ax, x, y, w, h, family='blue', label='应用层')         # 全宽层带+侧标签
S.side_label(ax, x, y, 50, 300, '竖排标签文字', family='blue')       # 伪竖排侧标签
S.cylinder(ax, cx, y, 95, 90, '数据库', family='blue')              # 数据库圆柱
S.badge(ax, cx, cy, 1)                                              # 编号圆徽章
S.plus_sign(ax, cx, cy)                                             # A+B加号
S.connector(ax, x1, y1, x2, y2, color='#5B9BD5')                    # 细线汇聚(非主干!)
S.note(ax, x, y, '关系词', bold=True)                               # 透明标注文本
S.save(fig, 'out.png')
```

色系：`FAMILIES['blue'|'orange'|'gold'|'green'|'purple'|'gray']`，
每系四档 `panel`(近白底板) / `band`(浅色带) / `card`(卡片) / `accent`(饱和) / `deep`(深强调)。

## 生成流程

1. 读取MD提取结构 → 2. 选版式原型 → 3. 应用组件库绘制 → 4. 输出PNG/Mermaid
