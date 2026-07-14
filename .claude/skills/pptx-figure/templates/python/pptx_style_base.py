# -*- coding: utf-8 -*-
"""
PPTX风格绘图组件库 v2 (双后端: matplotlib PNG + 手写SVG矢量)
============================================================
基于对源PPTX全部41页的逐页视觉分析+OOXML提取重建。

风格签名：
  浅色tint填充 + 黑色1.5pt实线边框 + 黑色粗体标题/常规正文；
  sysDash虚线分组框配“骑缝标签”；块状实心箭头（金黄FFC000+黑描边）做宏观流程；
  细线连接器只做微观汇聚；一区一色、同色相三档深浅递进；白字只出现在饱和深色窄条上。

坐标系：1280×720，原点左下（y向上）。1pt = 96/72 坐标单位。

后端：
  - 'mpl'  matplotlib 栅格 PNG（默认，需要 matplotlib）
  - 'svg'  手写 SVG 矢量图，元素为内联属性、无CSS/defs/clip，
           PowerPoint 可直接“插入图片”导入，并可“转换为形状”变为原生可编辑图形：
           rect[rx]→圆角矩形, ellipse→椭圆, line→连接线, polygon→任意多边形, text→文本框。

组件函数对两个后端完全通用；生成器只需按输出扩展名 set_backend('svg'|'mpl')。
"""

import math

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
FAMILY_CYCLE = ['blue', 'orange', 'green', 'purple', 'gold', 'gray']

BLACK = '#000000'
WHITE = '#FFFFFF'
GOLD = '#FFC000'
RED = '#FF0000'
LW = 1.5                  # 签名线宽(pt)
DASH = (0, (3.2, 1.8))    # matplotlib sysDash近似
PX_PER_PT = 96 / 72       # pt → 坐标单位
CANVAS_W, CANVAS_H = 1280, 720
FONT_STACK = 'Microsoft YaHei, SimHei, Noto Sans CJK SC, WenQuanYi Zen Hei, sans-serif'

_FONT_RC = ['Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'sans-serif']

_BACKEND = 'mpl'


def set_backend(name):
    """选择渲染后端: 'mpl'(PNG) 或 'svg'(矢量)"""
    global _BACKEND
    if name not in ('mpl', 'svg'):
        raise ValueError(f"未知后端: {name}")
    _BACKEND = name


# ============================================================
# 2. 文字工具（CJK折行+自动缩字，后端无关）
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


# ============================================================
# 3. 渲染后端（Surface）：矢量/栅格双实现，图元接口一致
#    坐标一律用数据坐标(1280×720, 原点左下, y向上)；线宽/字号用pt。
# ============================================================

def _norm(c):
    """None/'none' → None"""
    if c is None or (isinstance(c, str) and c.lower() == 'none'):
        return None
    return c


class MplSurface:
    """matplotlib后端：复刻栅格PNG外观"""

    def __init__(self, figsize=(13.33, 7.5), dpi=150):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        self.plt = plt
        plt.rcParams.update({
            'font.family': _FONT_RC,
            'font.size': 12,
            'axes.unicode_minus': False,
        })
        self.fig = plt.figure(figsize=figsize, dpi=dpi)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, CANVAS_W)
        self.ax.set_ylim(0, CANVAS_H)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.fig.patch.set_facecolor(WHITE)

    def rect(self, x, y, w, h, fill=None, stroke=None, stroke_width=0, dash=False, rx=0):
        from matplotlib.patches import FancyBboxPatch, Rectangle
        fill, stroke = _norm(fill), _norm(stroke)
        ls = DASH if dash else '-'
        if rx and rx > 0:
            p = FancyBboxPatch((x, y), w, h,
                               boxstyle=f"round,pad=0,rounding_size={rx}",
                               facecolor=fill or 'none',
                               edgecolor=stroke or 'none',
                               linewidth=stroke_width, linestyle=ls)
        else:
            p = Rectangle((x, y), w, h, facecolor=fill or 'none',
                          edgecolor=stroke or 'none',
                          linewidth=stroke_width, linestyle=ls)
        self.ax.add_patch(p)

    def polygon(self, points, fill=None, stroke=None, stroke_width=0):
        from matplotlib.patches import Polygon
        fill, stroke = _norm(fill), _norm(stroke)
        self.ax.add_patch(Polygon(points, closed=True, facecolor=fill or 'none',
                                  edgecolor=stroke or 'none', linewidth=stroke_width))

    def ellipse(self, cx, cy, rx, ry, fill=None, stroke=None, stroke_width=0):
        from matplotlib.patches import Ellipse
        fill, stroke = _norm(fill), _norm(stroke)
        self.ax.add_patch(Ellipse((cx, cy), 2 * rx, 2 * ry, facecolor=fill or 'none',
                                  edgecolor=stroke or 'none', linewidth=stroke_width))

    def line(self, x1, y1, x2, y2, stroke=BLACK, stroke_width=1.0):
        self.ax.plot([x1, x2], [y1, y2], color=_norm(stroke) or BLACK,
                     linewidth=stroke_width, solid_capstyle='round')

    def text(self, cx, cy, s, fs, bold=False, color=BLACK, anchor='middle'):
        ha = {'start': 'left', 'middle': 'center', 'end': 'right'}[anchor]
        self.ax.text(cx, cy, s, fontsize=fs, ha=ha, va='center',
                     fontweight='bold' if bold else 'normal', color=color)

    def arrowline(self, x1, y1, x2, y2, color=BLACK, stroke_width=1.5, head=8):
        from matplotlib.patches import FancyArrowPatch
        self.ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                          color=_norm(color) or BLACK,
                                          linewidth=stroke_width, mutation_scale=13))

    def save(self, path, dpi=150):
        self.fig.savefig(path, dpi=dpi, facecolor=WHITE)
        self.plt.close(self.fig)


def _n(v):
    """紧凑数字格式"""
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def _esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


class SvgSurface:
    """手写SVG后端：内联属性、无CSS/defs/clip，PowerPoint可导入并转形状"""

    def __init__(self):
        self.elems = ['<rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>']

    def _y(self, y):
        return CANVAS_H - y

    def _stroke_attrs(self, stroke, stroke_width, dash):
        stroke = _norm(stroke)
        if not stroke or stroke_width <= 0:
            return ''
        a = f' stroke="{stroke}" stroke-width="{_n(stroke_width * PX_PER_PT)}"'
        if dash:
            sw = stroke_width * PX_PER_PT
            a += f' stroke-dasharray="{_n(3.2 * sw)} {_n(2.0 * sw)}"'
        return a

    def rect(self, x, y, w, h, fill=None, stroke=None, stroke_width=0, dash=False, rx=0):
        fill = _norm(fill)
        a = f'<rect x="{_n(x)}" y="{_n(self._y(y + h))}" width="{_n(w)}" height="{_n(h)}"'
        if rx and rx > 0:
            a += f' rx="{_n(rx)}" ry="{_n(rx)}"'
        a += f' fill="{fill or "none"}"'
        a += self._stroke_attrs(stroke, stroke_width, dash)
        self.elems.append(a + '/>')

    def polygon(self, points, fill=None, stroke=None, stroke_width=0):
        fill = _norm(fill)
        pts = ' '.join(f'{_n(px)},{_n(self._y(py))}' for px, py in points)
        a = f'<polygon points="{pts}" fill="{fill or "none"}"'
        a += self._stroke_attrs(stroke, stroke_width, False)
        self.elems.append(a + '/>')

    def ellipse(self, cx, cy, rx, ry, fill=None, stroke=None, stroke_width=0):
        fill = _norm(fill)
        a = (f'<ellipse cx="{_n(cx)}" cy="{_n(self._y(cy))}" '
             f'rx="{_n(rx)}" ry="{_n(ry)}" fill="{fill or "none"}"')
        a += self._stroke_attrs(stroke, stroke_width, False)
        self.elems.append(a + '/>')

    def line(self, x1, y1, x2, y2, stroke=BLACK, stroke_width=1.0):
        a = (f'<line x1="{_n(x1)}" y1="{_n(self._y(y1))}" '
             f'x2="{_n(x2)}" y2="{_n(self._y(y2))}" '
             f'stroke="{_norm(stroke) or BLACK}" '
             f'stroke-width="{_n(stroke_width * PX_PER_PT)}" stroke-linecap="round"/>')
        self.elems.append(a)

    def text(self, cx, cy, s, fs, bold=False, color=BLACK, anchor='middle'):
        lines = s.split('\n')
        fu = fs * PX_PER_PT
        lh = fu * 1.32
        n = len(lines)
        base = self._y(cy) - (n - 1) / 2.0 * lh + 0.34 * fu
        w = ' font-weight="bold"' if bold else ''
        head = (f'<text x="{_n(cx)}" font-family="{FONT_STACK}" '
                f'font-size="{_n(fu)}" fill="{color}" text-anchor="{anchor}"{w}>')
        spans = ''.join(
            f'<tspan x="{_n(cx)}" y="{_n(base + k * lh)}">{_esc(ln)}</tspan>'
            for k, ln in enumerate(lines))
        self.elems.append(head + spans + '</text>')

    def arrowline(self, x1, y1, x2, y2, color=BLACK, stroke_width=1.5, head=8):
        color = _norm(color) or BLACK
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1.0
        ux, uy = dx / L, dy / L
        bx, by = x2 - ux * head, y2 - uy * head       # 头部底边中点
        self.line(x1, y1, bx, by, stroke=color, stroke_width=stroke_width)
        px, py = -uy, ux
        p1 = (bx + px * head * 0.5, by + py * head * 0.5)
        p2 = (bx - px * head * 0.5, by - py * head * 0.5)
        self.polygon([(x2, y2), p1, p2], fill=color)

    def save(self, path, dpi=None):
        body = '\n'.join(self.elems)
        svg = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
               'width="13.333in" height="7.5in" viewBox="0 0 1280 720">\n'
               f'{body}\n</svg>\n')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(svg)


def init_figure(figsize=(13.33, 7.5), dpi=150, backend=None):
    """新建画布，返回 (surface, surface)。按当前后端选择实现。"""
    b = backend or _BACKEND
    surf = SvgSurface() if b == 'svg' else MplSurface(figsize, dpi)
    return surf, surf


def save(surface, path, dpi=150):
    surface.save(path, dpi)


# ============================================================
# 4. 组件（对两后端通用；第一参数为 surface）
# ============================================================

def card(ax, x, y, w, h, family='blue', text='', fs=12, bold=False,
         tier='card', radius=5, lw=LW, edge=BLACK, text_color=BLACK):
    """浅填充+黑1.5pt边+黑字 圆角内容卡（全库最高频组件）。"""
    fill = FAMILIES[family][tier] if isinstance(family, str) and family in FAMILIES else family
    ax.rect(x, y, w, h, fill=fill, stroke=edge, stroke_width=lw, rx=radius)
    if text:
        t, fs2 = fit_text(text, w, h, fs)
        ax.text(x + w / 2, y + h / 2, t, fs2, bold=bold, color=text_color)


def deep_card(ax, x, y, w, h, family='blue', text='', fs=14, radius=5,
              use='accent', edge=BLACK, lw=LW):
    """饱和深色底+白粗体字：一级节点/结论条/标题卡。"""
    fill = FAMILIES[family][use] if isinstance(family, str) and family in FAMILIES else family
    ax.rect(x, y, w, h, fill=fill, stroke=edge, stroke_width=lw, rx=radius)
    if text:
        tc = BLACK if str(fill).upper() == '#FFC000' else WHITE
        t, fs2 = fit_text(text, w, h, fs)
        ax.text(x + w / 2, y + h / 2, t, fs2, bold=True, color=tc)


def title_bar(ax, cx, y, w, h, text, family='blue', fs=18, use='deep'):
    """深蓝总标题条（白粗体，水平居中），cx为中心x"""
    deep_card(ax, cx - w / 2, y, w, h, family=family, text=text, fs=fs,
              use=use, edge='none', lw=0)


def frame(ax, x, y, w, h, fill='none', edge=BLACK, lw=LW, radius=0):
    """外层容器框：白底/无填充+黑实线。"""
    ax.rect(x, y, w, h, fill=fill, stroke=edge, stroke_width=lw, rx=radius)


def dashed_group(ax, x, y, w, h, fill='none', edge=BLACK, lw=LW, radius=6,
                 label=None, label_family='blue', label_w=None, label_h=36,
                 label_fs=14):
    """sysDash虚线分组框；label给出时绘制“骑缝标签”压在上边线（重叠约50%）。"""
    if isinstance(fill, tuple):
        fill = FAMILIES[fill[0]][fill[1]]
    ax.rect(x, y, w, h, fill=fill, stroke=edge, stroke_width=lw, rx=radius, dash=True)
    if label:
        lw_ = label_w or min(w * 0.72, max(150, len(label) * label_fs * 1.4 + 30))
        lx = x + (w - lw_) / 2
        ly = y + h - label_h * 0.5
        deep_card(ax, lx, ly, lw_, label_h, family=label_family,
                  text=label, fs=label_fs, edge='none', lw=0)


def chevron_row(ax, x, y, seg_ws, h, labels, colors=None, fs=17, overlap=5,
                tip=None):
    """燕尾页签行：首段homePlate(单尖五边形)+后续chevron，白粗体字。"""
    if colors is None:
        colors = [FAMILIES[FAMILY_CYCLE[i % 6]]['accent'] for i in range(len(labels))]
    colors = [FAMILIES[c]['accent'] if isinstance(c, str) and c in FAMILIES else c
              for c in colors]
    tip = tip or h * 0.55
    spans = []
    cx = x
    for i, (w, lab, col) in enumerate(zip(seg_ws, labels, colors)):
        if i == 0:
            verts = [(cx, y), (cx + w - tip, y), (cx + w, y + h / 2),
                     (cx + w - tip, y + h), (cx, y + h)]
        else:
            verts = [(cx, y), (cx + w - tip, y), (cx + w, y + h / 2),
                     (cx + w - tip, y + h), (cx, y + h), (cx + tip, y + h / 2)]
        ax.polygon(verts, fill=col)
        tx = cx + (w - tip) / 2 + (tip / 2 if i else 0)
        t, fs2 = fit_text(lab, w - tip - 16, h, fs)
        ax.text(tx, y + h / 2, t, fs2, bold=True, color=WHITE)
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
    """块状实心箭头（宏观流程/支撑专用）。direction: up/down/left/right。"""
    st = ARROW_STYLES[style]
    L, W = length, width
    hd = L * 0.45
    sw = W * 0.58
    pts = [(0, -sw / 2), (L - hd, -sw / 2), (L - hd, -W / 2), (L, 0),
           (L - hd, W / 2), (L - hd, sw / 2), (0, sw / 2)]
    ang = {'right': 0, 'up': 90, 'left': 180, 'down': 270}[direction]
    rad = math.radians(ang)
    cosr, sinr = math.cos(rad), math.sin(rad)
    ox = -L / 2
    rot = [(cx + (px + ox) * cosr - py * sinr, cy + (px + ox) * sinr + py * cosr)
           for px, py in pts]
    ax.polygon(rot, fill=st['fill'], stroke=st['edge'], stroke_width=st['lw'])
    if note:
        if note_dx is None:
            note_dx = (W / 2 + 8 + len(note) * note_fs * 0.67) if direction in ('up', 'down') else 0
        ny = cy + note_dy if direction in ('up', 'down') else cy + W / 2 + 12
        ax.text(cx + note_dx, ny, note, note_fs, bold=True)


def side_label(ax, x, y, w, h, text, family='blue', tier='card', fs=14,
               bold=True, edge=BLACK, lw=1.0, red_head=None, radius=5):
    """竖排侧标签（伪竖排：逐字换行）。red_head: 顶部红色关键词（也竖排）"""
    fam_fill = FAMILIES[family][tier] if isinstance(family, str) and family in FAMILIES else family
    ax.rect(x, y, w, h, fill=fam_fill, stroke=edge, stroke_width=lw, rx=radius)
    body = '\n'.join(text)
    if red_head:
        head = '\n'.join(red_head)
        ax.text(x + w / 2, y + h * 0.82, head, fs + 1, bold=True, color=RED)
        ax.text(x + w / 2, y + h * 0.40, body, fs, bold=bold)
    else:
        ax.text(x + w / 2, y + h / 2, body, fs, bold=bold)


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
    """数据库圆柱（浅底黑边黑字）"""
    fill = FAMILIES[family]['band']
    ry = h * 0.14
    ax.rect(cx - w / 2, y + ry, w, h - 2 * ry, fill=fill)
    ax.ellipse(cx, y + ry, w / 2, ry, fill=fill, stroke=BLACK, stroke_width=1.0)
    ax.ellipse(cx, y + h - ry, w / 2, ry, fill=fill, stroke=BLACK, stroke_width=1.0)
    ax.line(cx - w / 2, y + ry, cx - w / 2, y + h - ry, stroke=BLACK, stroke_width=1.0)
    ax.line(cx + w / 2, y + ry, cx + w / 2, y + h - ry, stroke=BLACK, stroke_width=1.0)
    if text:
        t, fs2 = fit_text(text, w, h - 3 * ry, fs)
        ax.text(cx, y + h / 2 - ry * 0.5, t, fs2)


def badge(ax, cx, cy, num, color='#A5A5A5', r=15, fs=14):
    """编号圆徽章：灰/蓝底白粗体数字，叠压卡片左上角（绘制次序在卡片之后即置顶）"""
    ax.ellipse(cx, cy, r, r, fill=color)
    ax.text(cx, cy, str(num), fs, bold=True, color=WHITE)


def note(ax, x, y, text, fs=12, bold=False, color=BLACK, ha='center'):
    """无框透明标注文本（箭头旁关系词/层名）"""
    anchor = {'left': 'start', 'center': 'middle', 'right': 'end'}.get(ha, 'middle')
    ax.text(x, y, text, fs, bold=bold, color=color, anchor=anchor)


def connector(ax, x1, y1, x2, y2, color=BLACK, lw=1.5):
    """细线连接器+实心小三角端头（只用于微观汇聚/扇出，不做主干）"""
    ax.arrowline(x1, y1, x2, y2, color=color, stroke_width=lw, head=9)


def plus_sign(ax, cx, cy, size=26, color='#70AD47'):
    """加号运算符：A+B组合语义"""
    a = size * 0.32
    s = size / 2
    verts = [(-a / 2, -s), (a / 2, -s), (a / 2, -a / 2), (s, -a / 2), (s, a / 2),
             (a / 2, a / 2), (a / 2, s), (-a / 2, s), (-a / 2, a / 2), (-s, a / 2),
             (-s, -a / 2), (-a / 2, -a / 2)]
    ax.polygon([(cx + vx, cy + vy) for vx, vy in verts], fill=color)


def page_header(ax, text, x=45, y=678, fs=22, deco_family='blue'):
    """左上角页眉：蓝色小方块装饰+黑粗体标题"""
    acc = FAMILIES[deco_family]['accent']
    deep = FAMILIES[deco_family]['deep']
    ax.rect(x, y - 4, 12, 26, fill=deep)
    ax.rect(x + 15, y - 4, 7, 26, fill=acc)
    ax.text(x + 34, y + 9, text, fs, bold=True, anchor='start')
