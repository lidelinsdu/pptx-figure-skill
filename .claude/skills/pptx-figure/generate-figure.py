#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPTX Figure Style Generator v2
==============================
根据 .md 文件生成源PPTX风格的学术图表。

版式原型（源自41页逐页分析，见 style-reference/complete-style-guide.md）:
    route         原型A: 燕尾页签 + 等宽泳道面板（技术路线/阶段流程）
    panel         原型B: 多栏并列技术板 + 栏间块箭头（模块并列）
    architecture  原型C: 全宽横带层叠平台 + 层间金黄支撑箭头（分层架构）
    overview      原型D: 外框+总标题条+骑缝标签虚线分组（总-分关系）

用法:
    python generate-figure.py input.md -o figure.png --type route
    python generate-figure.py input.md -o figure.png            (自动选型)
    python generate-figure.py input.md -o diagram.mermaid       (Mermaid代码)

依赖: pip install matplotlib
"""

import os
import sys
import re
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
    sys.stderr.reconfigure(errors='replace')

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
sys.path.insert(0, os.path.join(TEMPLATE_DIR, 'python'))

# ============================================================
# 1. Markdown解析
# ============================================================

def parse_markdown_structure(filepath):
    """# 一级标题=图题；##/###=章节；列表项=子模块；正文首行=章节描述"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    structure = {'title': '', 'sections': []}
    current = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('<!--'):
            continue
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1:
                structure['title'] = text
                current = None
            else:
                if current:
                    structure['sections'].append(current)
                current = {'title': text, 'level': level, 'items': [], 'desc': ''}
            continue
        m = re.match(r'^[-*+]\s+(.+)$', line) or re.match(r'^\d+[\.\)]\s+(.+)$', line)
        if m and current:
            current['items'].append(m.group(1).strip())
            continue
        if line and current and not line.startswith('#'):
            b = re.match(r'^\*\*(.+)\*\*$', line)
            if b:
                current['items'].append(b.group(1))
            elif not current['desc']:
                current['desc'] = line
    if current:
        structure['sections'].append(current)
    return structure


def content_sections(structure):
    return [s for s in structure['sections'] if s.get('items')]


def find_center(structure):
    for s in structure['sections']:
        if any(kw in s['title'] for kw in ['核心', '主题', '总览', '中心', '目标']):
            return s.get('desc') or s['title']
    return structure['title'] or '核心主题'


# ============================================================
# 2. 版式生成器
# ============================================================

def _families(n):
    from pptx_style_base import FAMILY_CYCLE
    return [FAMILY_CYCLE[i % len(FAMILY_CYCLE)] for i in range(n)]


def gen_route(md, out):
    """原型A: 燕尾页签+等宽泳道面板。
    章节=阶段(页签+泳道)；items[0]=骑缝标签(深色)；其余=组内浅色卡"""
    import pptx_style_base as S

    secs = content_sections(md) or md['sections']
    secs = secs[:4]
    n = len(secs)
    fams = _families(n)

    fig, ax = S.init_figure()
    S.page_header(ax, md['title'])

    ML, MR, GAP = 60, 60, 24
    total_w = 1280 - ML - MR
    seg_w = (total_w + (n - 1) * 5) / n          # 页签重叠5px咬合

    # 页签行
    chev_y, chev_h = 585, 52
    spans = S.chevron_row(ax, ML, chev_y, [seg_w] * n, chev_h,
                          [s['title'] for s in secs], colors=fams)

    # 按最大内容量决定统一泳道高度（同级面板严格等高）
    def _counts(sec):
        items = sec['items']
        if not items:
            return 0, False
        if len(items) >= 3:
            return len(items) - 2, True
        return max(len(items) - 1, 0), bool(sec.get('desc'))

    ch, gap = 42, 12
    max_rest = max((_counts(s)[0] for s in secs), default=1)
    has_concl = any(_counts(s)[1] for s in secs)
    g_h_uni = 46 + max(max_rest, 1) * (ch + gap) + 10
    pan_h = 44 + g_h_uni + (36 + 40 + 18 if has_concl else 0) + 24
    pan_top = 575
    pan_bot = max(pan_top - pan_h, 60)
    pan_h = pan_top - pan_bot
    for i, (sec, fam) in enumerate(zip(secs, fams)):
        px = ML + i * (total_w + GAP * (n - 1)) / n - (0 if n == 1 else i * GAP * 0)
        # 与页签严格等宽对齐（页签有重叠，面板取不重叠均分）
        pw = (total_w - (n - 1) * GAP) / n
        px = ML + i * (pw + GAP)
        S.card(ax, px, pan_bot, pw, pan_h, family=fam, tier='panel', radius=0,
               lw=1.5)

        items = sec['items']
        inner_x = px + 12
        inner_w = pw - 24
        if items:
            head = items[0]
            # ≥3项时末项作底部结论条（原型A：标题→分组→结论）
            if len(items) >= 3:
                rest, concl = items[1:-1][:4], items[-1]
            else:
                rest, concl = items[1:5], (sec.get('desc') or None)
            # 虚线分组框统一高度，贴泳道上部
            g_h = min(g_h_uni, pan_h - 120 if concl else pan_h - 70)
            g_y = pan_top - 44 - g_h
            S.dashed_group(ax, inner_x, g_y, inner_w, g_h,
                           fill=(fam, 'panel'), label=head, label_family=fam,
                           label_fs=13)
            cy = g_y + g_h - 40
            for it in rest:
                cy -= (ch + gap)
                if cy < g_y + 8:
                    break
                S.card(ax, inner_x + 10, cy, inner_w - 20, ch, family=fam,
                       tier='card', text=it, fs=12)
            # 底部结论条
            if concl:
                S.deep_card(ax, inner_x, pan_bot + 14, inner_w, 40,
                            family=fam, text=concl, fs=12)
                # 分组→结论 的竖直块箭头
                S.block_arrow(ax, px + pw/2, (g_y + pan_bot + 54) / 2,
                              direction='down', length=30, width=26,
                              style='blue')
        # 栏间块箭头
        if i < n - 1:
            S.block_arrow(ax, px + pw + GAP/2, pan_bot + pan_h/2,
                          direction='right', length=30, width=24, style='blue')

    S.save(fig, out)


def gen_panel(md, out):
    """原型B: 多栏并列技术板+栏间块箭头（无页签）。
    章节=技术板；items[0]=深色标题条；其余=虚线分组内小卡"""
    import pptx_style_base as S

    secs = content_sections(md) or md['sections']
    secs = secs[:4]
    n = len(secs)
    fams = _families(n)

    fig, ax = S.init_figure()
    S.page_header(ax, md['title'])

    ML, GAP = 60, 40
    total_w = 1280 - 2 * ML
    pw = (total_w - (n - 1) * GAP) / n
    # 按最大条目数决定统一板高
    ch, gap = 36, 10
    max_rest = max((len(s['items'][1:5]) for s in secs), default=1)
    g_h_uni = 18 + max(max_rest, 1) * (ch + gap)
    p_top = 630
    p_bot = max(p_top - (46 + 36 + 18 + g_h_uni + 24), 90)
    ph = p_top - p_bot

    for i, (sec, fam) in enumerate(zip(secs, fams)):
        px = ML + i * (pw + GAP)
        S.card(ax, px, p_bot, pw, ph, family=fam, tier='panel', radius=0)
        # 板顶粗体标题（无框）
        S.note(ax, px + pw/2, p_top - 24, sec['title'], fs=15, bold=True)

        items = sec['items']
        if items:
            head, rest = items[0], items[1:5]
            S.deep_card(ax, px + 14, p_top - 86, pw - 28, 36, family=fam,
                        text=head, fs=13)
            g_y = p_bot + 16
            g_h = p_top - 104 - g_y
            S.dashed_group(ax, px + 14, g_y, pw - 28, g_h, fill='none',
                           edge=S.FAMILIES[fam]['accent'])
            cy = g_y + g_h - 12
            for it in rest:
                cy -= (ch + gap)
                if cy < g_y + 6:
                    break
                S.card(ax, px + 26, cy, pw - 52, ch, family=fam, tier='card',
                       text=it, fs=12)
        if i < n - 1:
            S.block_arrow(ax, px + pw + GAP/2, (p_top + p_bot)/2,
                          direction='right', length=34, width=28, style='gold')

    S.save(fig, out)


def gen_architecture(md, out):
    """原型C: 全宽横带层叠平台。章节=层（第一节在顶层），层间金黄上箭头+“支撑”"""
    import pptx_style_base as S

    secs = content_sections(md) or md['sections']
    secs = secs[:5]
    n = len(secs)
    fams = _families(n)

    fig, ax = S.init_figure()
    S.page_header(ax, md['title'])

    ML, MR = 100, 100
    total_w = 1280 - ML - MR
    top_y, bot_y = 630, 100
    arrow_gap = 44
    band_h = (top_y - bot_y - (n - 1) * arrow_gap) / n

    for i, (sec, fam) in enumerate(zip(secs, fams)):
        by = top_y - band_h - i * (band_h + arrow_gap)
        bx, _, bw, _ = S.layer_band(ax, ML, by, total_w, band_h, family=fam,
                                    label=sec['title'], label_w=150,
                                    label_fs=14)
        # 层内等宽卡片横排
        items = sec['items'][:5] or ['…']
        m = len(items)
        igap = 14
        cw = (bw - 24 - (m - 1) * igap) / m
        ch = min(band_h - 20, 52)
        for j, it in enumerate(items):
            S.card(ax, bx + 12 + j * (cw + igap), by + (band_h - ch)/2,
                   cw, ch, family=fam, tier='card', text=it, fs=12)
        # 层间金黄支撑箭头
        if i < n - 1:
            for frac, lab in ((0.30, '支撑'), (0.70, None)):
                axp = ML + 150 + (total_w - 150) * frac
                S.block_arrow(ax, axp, by - arrow_gap/2, direction='up',
                              length=34, width=30, style='gold',
                              note=lab, note_fs=12)

    S.save(fig, out)


def gen_overview(md, out):
    """原型D: 外框+骑缝总标题条+并列虚线分组（骑缝标签）总-分图"""
    import pptx_style_base as S

    secs = content_sections(md) or md['sections']
    secs = secs[:3]
    n = max(len(secs), 1)
    fams = _families(n)
    title = find_center(md)

    fig, ax = S.init_figure()
    S.page_header(ax, md['title'])

    # 按最大条目数决定分组框/外框高度，整体垂直居中
    ch, igap = 40, 12
    max_items = max((len(s['items'][:5]) for s in secs), default=1)
    g_h = 44 + max_items * (ch + igap) + 16
    FH = g_h + 128
    FW = 1100
    FX = (1280 - FW) / 2
    FY = max((640 - FH) / 2 + 30, 70)
    S.frame(ax, FX, FY, FW, FH, fill='#FFFFFF', radius=8)
    # 总标题条骑跨外框顶边
    S.title_bar(ax, FX + FW/2, FY + FH - 26, min(620, FW*0.55), 52, title,
                family='blue', fs=18)

    # 并列虚线分组
    GAP = 36
    gw = (FW - 60 - (n - 1) * GAP) / n
    g_y = FY + 40
    for i, (sec, fam) in enumerate(zip(secs, fams)):
        gx = FX + 30 + i * (gw + GAP)
        S.dashed_group(ax, gx, g_y, gw, g_h, fill=(fam, 'panel'),
                       label=sec['title'], label_family=fam, label_fs=14)
        items = sec['items'][:5]
        ch, igap = 40, 12
        cy = g_y + g_h - 40
        for it in items:
            cy -= (ch + igap)
            if cy < g_y + 10:
                break
            S.card(ax, gx + 16, cy, gw - 32, ch, family=fam, tier='card',
                   text=it, fs=12)
        # 组间加号（组合语义）
        if i < n - 1:
            S.plus_sign(ax, gx + gw + GAP/2, g_y + g_h/2, size=26,
                        color=S.FAMILIES[fams[i]]['accent'])

    S.save(fig, out)


# ============================================================
# 3. Mermaid输出（浅底黑边黑字风格）
# ============================================================

def gen_mermaid(md, out):
    secs = content_sections(md) or md['sections']
    fams = _families(len(secs))
    from pptx_style_base import FAMILIES
    lines = [
        '%%{init: {"theme": "base", "themeVariables": {',
        '  "primaryColor": "#DAE3F3", "primaryTextColor": "#000000",',
        '  "primaryBorderColor": "#000000", "lineColor": "#000000",',
        '  "fontFamily": "Microsoft YaHei"}}}%%',
        '',
        'flowchart LR',
    ]
    for f in set(fams):
        fam = FAMILIES[f]
        lines.append(f'  classDef {f} fill:{fam["card"]},stroke:#000000,'
                     f'stroke-width:1.5px,color:#000000,rx:4,ry:4')
        lines.append(f'  classDef {f}_head fill:{fam["accent"]},stroke:#000000,'
                     f'stroke-width:1.5px,color:#FFFFFF,rx:4,ry:4,font-weight:bold')
    lines.append('')
    for i, (sec, f) in enumerate(zip(secs, fams)):
        sid = f'S{i}'
        t = sec['title'].replace('"', "'")
        lines.append(f'  {sid}["{t}"]:::{f}_head')
        for j, it in enumerate(sec['items'][:4]):
            it = it.replace('"', "'")
            lines.append(f'  {sid}_{j}["{it}"]:::{f}')
            lines.append(f'  {sid} --> {sid}_{j}')
    for i in range(len(secs) - 1):
        lines.append(f'  S{i} ==> S{i+1}')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'[OK] Mermaid: {out}')


# ============================================================
# 4. 选型与入口
# ============================================================

GENERATORS = {
    'route': gen_route, 'flowchart': gen_route, 'roadmap': gen_route,
    'panel': gen_panel, 'board': gen_panel,
    'architecture': gen_architecture, 'layered': gen_architecture,
    'overview': gen_overview, 'concept': gen_overview,
}


def auto_type(md):
    t = md['title']
    n = len(content_sections(md))
    if any(k in t for k in ['路线', '流程', '阶段', '步骤', 'pipeline']):
        return 'route'
    if any(k in t for k in ['架构', '平台', '分层', '体系', 'architecture']):
        return 'architecture'
    if any(k in t for k in ['总览', '关系', '总体', '组成', '概念']):
        return 'overview'
    return 'panel' if n >= 3 else 'overview'


def main():
    p = argparse.ArgumentParser(description='PPTX风格图表生成器 v2')
    p.add_argument('input', help='输入 .md 文件')
    p.add_argument('--output', '-o', default=None)
    p.add_argument('--type', '-t', default='auto',
                   choices=['auto'] + sorted(GENERATORS.keys()) + ['mermaid'])
    p.add_argument('--title', default=None, help='覆盖标题')
    args = p.parse_args()

    if not os.path.exists(args.input):
        print(f'错误: 文件不存在: {args.input}')
        sys.exit(1)

    md = parse_markdown_structure(args.input)
    if args.title:
        md['title'] = args.title
    out = args.output or os.path.splitext(args.input)[0] + '.png'

    if args.type == 'mermaid' or out.lower().endswith('.mermaid'):
        gen_mermaid(md, out)
        return

    t = auto_type(md) if args.type == 'auto' else args.type
    GENERATORS[t](md, out)
    print(f'[OK] {out} (type: {t})')


if __name__ == '__main__':
    main()
