Generate a PPTX-style academic vector figure from Markdown using the pptx-figure skill.

用户请求 / 输入：$ARGUMENTS

执行步骤：
1. 确定输入 Markdown。若用户给的是文件路径，直接用；若只给了内容或主题，先写入一个临时 `.md`
   （约定：`# 总标题`；`## 分组标题`；`- 列表项`。route/panel 版式下每组首个列表项会成为深色骑缝标签，
   route ≥3 项时末项成为底部结论条）。
2. 选版式 `--type`：技术路线/阶段流程=route，模块并列=panel，分层架构/平台=architecture，总-分关系/总览=overview。
   拿不准就省略 `--type`，让脚本按标题关键词自动选。
3. 运行生成器（默认输出可编辑矢量 SVG；只要预览图时用 `.png`）：

   ```bash
   python .claude/skills/pptx-figure/generate-figure.py <input.md> -o <output.svg> [--type TYPE]
   ```

   路径按本仓库/安装位置调整。SVG 输出无需第三方库；PNG 输出需 matplotlib + 中文字体。
4. 向用户报告输出文件路径，并说明：SVG 可在 PowerPoint「插入 > 图片」导入，再「图形工具 > 转换为形状」
   拆成原生可编辑图形。
5. 如需超出四种版式的复杂构图，参考 `.claude/skills/pptx-figure/style-reference/complete-style-guide.md`，
   用组件库 `pptx_style_base`（`S.set_backend('svg')` + card/deep_card/dashed_group/chevron_row/block_arrow…）手写。
