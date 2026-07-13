# -*- coding: utf-8 -*-
"""
PPTX风格绘图组件库 v2
======================
基于对源PPTX全部41页的逐页视觉分析+OOXML提取重建。

风格签名：
  浅色tint填充 + 黑色1.5pt实线边框 + 黑色粗体标题/常规正文；
  sysDash虚线分组框配“骑缝标签”；块状实心箭头（金黄FFC000+黑描边）做宏观流程；
  细线连接器只做微观汇聚；一区一色、同色相三档深浅递进；
  白字只出现在饱和深色窄条上。

坐标系：1280×720，原点左下（y向上）。全出血画布，1pt字号=1.333坐标单位。
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Polygon, Circle

# ============================================================
# 1. 色彩系统：一色系四档（panel近白底板 / band浅色带 / card卡片 / accent饱和）
# ============================================================

FAMILIES = {
    'blue':   dict(panel='#F6F8FC', band='#D4EBFC', card='#DAE3F3', card2='#B4C7E7',
                   accent='#4472C4', deep='#0070C0'),
    'orange': dict(panel='#FFFDFB', band='#FFEDE4', card='#FBE5D6', card2='#F8CBAD',
                   accent='#ED7D31', deep='#C55A11'),
    'gold':   dict(panel='#FFFBE8', band='#FFF6DC', card='#FFF2CC', card2='#FFE699',
                   accent='#FFC000', deep='#BF9000'),
    'green':  dict(panel='#F8FCF6', band='#ECF9E7', card='#E2EFDA', card2='#C9E7A7',
                   accent='#70AD47', deep='#15803D'),
    'purple': dict(panel='#F2EEFC', band='#F5EBFF', card='#EEEDFD', card2='#D8DBFC',
                   accent='#7030A0', deep='#4F2EA2'),
    'gray':   dict(panel='#F9FAFB', band='#EDEDED', card='#E7E6E6', card2='#D6DCE5',
                   accent='#A5A5A5', deep='#44546A'),
}
# 一区一色的默认轮换顺序（蓝为主，橙绿次之——与源PPT一致）
FAMILY_CYCLE = ['blue', 'orange', 'green', 'purple', 'gold', 'gray']

BLACK = '#000000'
WHITE = '#FFFFFF'
GOLD = '#FFC000'          # 签名箭头色
RED = '#FF0000'           # 竖排侧柱红色关键词/告警
LW = 1.5                  # 签名线宽
DASH = (0, (3.2, 1.8))    # 近似 sysDash

PX_PER_PT = 96 / 72


# ============================================================
# 2. 文字工具（CJK折行+自动缩字）
# ============================================================

def _char_w_px(ch, fontsize):
    return fontsize * PX_PER_PT * (1.0 if ord(ch) > 0x2E80 else 0.55)


def wrap_text(text, max_w_px, fontsize):
    lines = []
    for seg in text.split('\n'):
        cur, cur_w = '', 0.0
        for ch in seg:
            w = _char_w_px(ch, fontsize)
            if cur and cur_w + w > max_w_px:
                lines.append(cur)
                cur, cur_w = ch, w
            else:
                cur += ch
                cur_w += w
        lines.append(cur)
    return lines


def fit_text(text, box_w, box_h, fontsize, min_size=7, pad_x=10, pad_y=5):
    fs = fontsize
    while fs >= min_size:
        lines = wrap_text(text, box_w - 2 * pad_x, fs)
        line_h = fs * PX_PER_PT * 1.32
        if len(lines) * line_h <= box_h - 2 * pad_y:
            return '\n'.join(lines), fs
        fs -= 1
    return '\n'.join(wrap_text(text, box_w - 2 * pad_x, min_size)), min_size


def init_figure(figsize=(13.33, 7.5), dpi=150):
    """全出血16:9画布，1280×720坐标，白底"""
    plt.rcParams.update({
        'font.family': ['Microsoft YaHei', 'SimHei', 'sans-serif'],
        'font.size': 12,
        'axes.unicode_minus': False,
    })
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1280)
    ax.set_ylim(0, 720)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor(WHITE)
    return fig, ax


def _text(ax, cx, cy, s, fs, bold=False, color=BLACK, ha='center', va='center'):
    ax.text(cx, cy, s, fontsize=fs, ha=ha, va=va,
            fontweight='bold' if bold else 'normal', color=color)


# ============================================================
# 3. 原子组件
# ============================================================

def card(ax, x, y, w, h, family='blue', text='', fs=12, bold=False,
         tier='card', radius=5, lw=LW, edge=BLACK, text_color=BLACK):
    """浅填充+黑1.5pt边+黑字 圆角内容卡（全库最高频组件）。
    tier: panel/band/card/card2 选择同色系浅色档位。"""
    fam = FAMILIES[family] if isinstance(family, str) else None
    fill = fam[tier] if fam else family
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=fill, edgecolor=edge, linewidth=lw)
    ax.add_patch(p)
    if text:
        t, fs2 = fit_text(text, w, h, fs)
        _text(ax, x + w/2, y + h/2, t, fs2, bold=bold, color=text_color)


def deep_card(ax, x, y, w, h, family='blue', text='', fs=14, radius=5,
              use='accent', edge=BLACK, lw=LW):
    """饱和深色底+白粗体字：一级节点/结论条/标题卡。use: accent或deep"""
    fill = FAMILIES[family][use] if isinstance(family, str) else family
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=fill, edgecolor=edge, linewidth=lw)
    ax.add_patch(p)
    if text:
        # 金色FFC000上惯用黑字，其余饱和色用白字
        tc = BLACK if str(fill).upper() in ('#FFC000',) else WHITE
        t, fs2 = fit_text(text, w, h, fs)
        _text(ax, x + w/2, y + h/2, t, fs2, bold=True, color=tc)


def title_bar(ax, cx, y, w, h, text, family='blue', fs=18, use='deep'):
    """深蓝总标题条（白粗体20pt级，水平居中），cx为中心x"""
    deep_card(ax, cx - w/2, y, w, h, family=family, text=text, fs=fs,
              use=use, edge='none', lw=0)


def frame(ax, x, y, w, h, fill='none', edge=BLACK, lw=LW, radius=0):
    """外层容器框：白底/无填充+黑实线。radius>0用圆角"""
    if radius > 0:
        p = FancyBboxPatch((x, y), w, h,
                           boxstyle=f"round,pad=0,rounding_size={radius}",
                           facecolor=fill if fill != 'none' else 'none',
                           edgecolor=edge, linewidth=lw)
    else:
        p = plt.Rectangle((x, y), w, h,
                          facecolor=fill if fill != 'none' else 'none',
                          edgecolor=edge, linewidth=lw)
    ax.add_patch(p)


def dashed_group(ax, x, y, w, h, fill='none', edge=BLACK, lw=LW, radius=6,
                 label=None, label_family='blue', label_w=None, label_h=36,
                 label_fs=14):
    """sysDash虚线分组框；label给出时绘制“骑缝标签”压在上边线（重叠约50%）。
    fill 可传 'none'/具体hex/(family,tier)元组"""
    if isinstance(fill, tuple):
        fill = FAMILIES[fill[0]][fill[1]]
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=fill if fill != 'none' else 'none',
                       edgecolor=edge, linewidth=lw, linestyle=DASH)
    ax.add_patch(p)
    if label:
        lw_ = label_w or min(w * 0.72, max(150, len(label) * label_fs * 1.4 + 30))
        lx = x + (w - lw_) / 2
        ly = y + h - label_h * 0.5           # 骑缝：一半在框内一半在框外
        deep_card(ax, lx, ly, lw_, label_h, family=label_family,
                  text=label, fs=label_fs, edge='none', lw=0)


def chevron_row(ax, x, y, seg_ws, h, labels, colors=None, fs=17, overlap=5,
                tip=None):
    """燕尾页签行：首段homePlate(单尖五边形)+后续chevron，白粗体字。
    seg_ws: 每段宽度列表; colors: 每段饱和色(hex或family名)。
    返回每段的(x, w)供下方泳道对齐。"""
    if colors is None:
        colors = [FAMILIES[FAMILY_CYCLE[i % 6]]['accent'] for i in range(len(labels))]
    colors = [FAMILIES[c]['accent'] if isinstance(c, str) and c in FAMILIES else c
              for c in colors]
    tip = tip or h * 0.55
    spans = []
    cx = x
    for i, (w, lab, col) in enumerate(zip(seg_ws, labels, colors)):
        if i == 0:
            verts = [(cx, y), (cx + w - tip, y), (cx + w, y + h/2),
                     (cx + w - tip, y + h), (cx, y + h)]
        else:
            verts = [(cx, y), (cx + w - tip, y), (cx + w, y + h/2),
                     (cx + w - tip, y + h), (cx, y + h), (cx + tip, y + h/2)]
        ax.add_patch(Polygon(verts, facecolor=col, edgecolor='none'))
        tx = cx + (w - tip) / 2 + (tip / 2 if i else 0)
        t, fs2 = fit_text(lab, w - tip - 16, h, fs)
        _text(ax, tx, y + h/2, t, fs2, bold=True, color=WHITE)
        spans.append((cx, w))
        cx += w - overlap
    return spans


ARROW_STYLES = {
    'gold':   dict(fill=GOLD, edge=BLACK, lw=1.2),
    'blue':   dict(fill='#4472C4', edge=BLACK, lw=1.0),
    'deep':   dict(fill='#0070C0', edge=BLACK, lw=1.0),
    'hollow': dict(fill=WHITE, edge='#4472C4', lw=1.5),
    'gray':   dict(fill='#A5A5A5', edge='#333333', lw=0.8),
    'green':  dict(fill='#70AD47', edge=BLACK, lw=1.0),
    'red':    dict(fill='#C00000', edge=BLACK, lw=1.0),
}


def block_arrow(ax, cx, cy, direction='up', length=42, width=30, style='gold',
                note=None, note_fs=12, note_dx=None, note_dy=0):
    """块状实心箭头（宏观流程/支撑专用）。
    direction: up/down/left/right; style见ARROW_STYLES。
    note: 旁注关系词（独立透明文本，黑粗体）"""
    st = ARROW_STYLES[style]
    L, W = length, width
    hd = L * 0.45            # 箭头头部长
    sw = W * 0.58            # 箭杆宽
    # 以right为基准的多边形（原点在尾部中点）
    pts = [(0, -sw/2), (L - hd, -sw/2), (L - hd, -W/2), (L, 0),
           (L - hd, W/2), (L - hd, sw/2), (0, sw/2)]
    import math
    ang = {'right': 0, 'up': 90, 'left': 180, 'down': 270}[direction]
    rad = math.radians(ang)
    cosr, sinr = math.cos(rad), math.sin(rad)
    # 平移使箭头中心在(cx,cy)
    ox, oy = -L/2, 0
    rot = [(cx + (px + ox) * cosr - py * sinr, cy + (px + ox) * sinr + py * cosr)
           for px, py in pts]
    ax.add_patch(Polygon(rot, facecolor=st['fill'], edgecolor=st['edge'],
                         linewidth=st['lw']))
    if note:
        if note_dx is None:
            note_dx = (W/2 + 8 + len(note) * note_fs * 0.67) if direction in ('up', 'down') else 0
        ny = cy + note_dy if direction in ('up', 'down') else cy + W/2 + 12
        _text(ax, cx + note_dx, ny, note, note_fs, bold=True)


def side_label(ax, x, y, w, h, text, family='blue', tier='card', fs=14,
               bold=True, edge=BLACK, lw=1.0, red_head=None, radius=5):
    """竖排侧标签（伪竖排：逐字换行）。red_head: 顶部红色关键词（也竖排）"""
    fam_fill = FAMILIES[family][tier] if isinstance(family, str) else family
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=fam_fill, edgecolor=edge, linewidth=lw)
    ax.add_patch(p)
    body = '\n'.join(text)
    if red_head:
        head = '\n'.join(red_head)
        # 红色关键词在上，黑色正文在下
        _text(ax, x + w/2, y + h * 0.82, head, fs + 1, bold=True, color=RED)
        _text(ax, x + w/2, y + h * 0.40, body, fs, bold=bold)
    else:
        _text(ax, x + w/2, y + h/2, body, fs, bold=bold)


def layer_band(ax, x, y, w, h, family='blue', label=None, label_w=130,
               tier='band', label_fs=14, radius=4):
    """全宽层带 = 左侧饱和侧标签块 + 浅色内容带。返回内容区(x,y,w,h)"""
    if label:
        deep_card(ax, x, y, label_w, h, family=family, text=label, fs=label_fs,
                  radius=radius)
        bx = x + label_w + 8
        bw = w - label_w - 8
    else:
        bx, bw = x, w
    card(ax, bx, y, bw, h, family=family, tier=tier, radius=radius)
    return bx, y, bw, h


def cylinder(ax, cx, y, w, h, text='', family='blue', fs=11):
    """数据库圆柱（浅蓝底黑边黑字）"""
    fill = FAMILIES[family]['band']
    ry = h * 0.14
    body = plt.Rectangle((cx - w/2, y + ry), w, h - 2*ry,
                         facecolor=fill, edgecolor='none')
    ax.add_patch(body)
    ax.add_patch(Ellipse((cx, y + ry), w, 2*ry, facecolor=fill,
                         edgecolor=BLACK, linewidth=1.0))
    ax.add_patch(Ellipse((cx, y + h - ry), w, 2*ry, facecolor=fill,
                         edgecolor=BLACK, linewidth=1.0))
    # 侧边线
    ax.plot([cx - w/2, cx - w/2], [y + ry, y + h - ry], color=BLACK, lw=1.0)
    ax.plot([cx + w/2, cx + w/2], [y + ry, y + h - ry], color=BLACK, lw=1.0)
    if text:
        t, fs2 = fit_text(text, w, h - 3*ry, fs)
        _text(ax, cx, y + h/2 - ry*0.5, t, fs2)


def badge(ax, cx, cy, num, color='#A5A5A5', r=15, fs=14):
    """编号圆徽章：灰/蓝底白粗体数字，叠压卡片左上角"""
    ax.add_patch(Circle((cx, cy), r, facecolor=color, edgecolor='none', zorder=5))
    _text(ax, cx, cy, str(num), fs, bold=True, color=WHITE)
    # zorder处理
    ax.texts[-1].set_zorder(6)


def note(ax, x, y, text, fs=12, bold=False, color=BLACK, ha='center'):
    """无框透明标注文本（箭头旁关系词/层名）"""
    _text(ax, x, y, text, fs, bold=bold, color=color, ha=ha)


def connector(ax, x1, y1, x2, y2, color=BLACK, lw=1.5, style='-'):
    """细线连接器+实心小三角端头（只用于微观汇聚/扇出，不做主干）"""
    arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                            color=color, linewidth=lw, mutation_scale=13,
                            linestyle=style)
    ax.add_patch(arrow)


def plus_sign(ax, cx, cy, size=26, color='#70AD47'):
    """加号运算符：A+B组合语义"""
    a = size * 0.32
    s = size / 2
    verts = [(-a/2, -s), (a/2, -s), (a/2, -a/2), (s, -a/2), (s, a/2),
             (a/2, a/2), (a/2, s), (-a/2, s), (-a/2, a/2), (-s, a/2),
             (-s, -a/2), (-a/2, -a/2)]
    ax.add_patch(Polygon([(cx + vx, cy + vy) for vx, vy in verts],
                         facecolor=color, edgecolor='none'))


def page_header(ax, text, x=45, y=678, fs=22, deco_family='blue'):
    """左上角页眉：蓝色小方块装饰+黑粗体标题"""
    acc = FAMILIES[deco_family]['accent']
    deep = FAMILIES[deco_family]['deep']
    ax.add_patch(plt.Rectangle((x, y - 4), 12, 26, facecolor=deep, edgecolor='none'))
    ax.add_patch(plt.Rectangle((x + 15, y - 4), 7, 26, facecolor=acc, edgecolor='none'))
    _text(ax, x + 34, y + 9, text, fs, bold=True, ha='left')


def save(fig, path, dpi=150):
    fig.savefig(path, dpi=dpi, facecolor=WHITE)
    plt.close(fig)
