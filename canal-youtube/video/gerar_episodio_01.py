#!/usr/bin/env python3
"""
Bíblia em Traços — Episódio 01: A Criação (piloto)

Gera o vídeo animado completo (1920x1080, 24 fps) só com código:
  - narração em português com voz neural (Kokoro, gratuita, roda offline)
  - desenhos vetoriais feitos com Pillow (renderizados em 4K e reduzidos = traço suave)
  - legendas embutidas + arquivo .srt (para gravar a narração no ritmo certo)
  - trilha sonora original gerada com numpy (sem direitos autorais de terceiros)

Uso:
  python3 gerar_episodio_01.py [pasta_de_saida] [--sem-voz | --thumbs]
  VOZ=pm_alex python3 gerar_episodio_01.py saida   # troca a voz do narrador

Requisitos: python3, pillow, numpy, ffmpeg, kokoro-onnx, soundfile, espeak-ng.
(O modelo de voz, ~350 MB, é baixado sozinho na primeira vez para a pasta modelos/.)
"""
import math
import os
import random
import shutil
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------
W, H = 1920, 1080
S = 2  # supersampling: desenha em 4K e reduz para 1080p
FPS = 24
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")

FONT_DIR = "/usr/share/fonts/opentype/inter"
F_TITLE = os.path.join(FONT_DIR, "InterDisplay-Black.otf")
F_BOLD = os.path.join(FONT_DIR, "Inter-ExtraBold.otf")
F_SUB = os.path.join(FONT_DIR, "Inter-SemiBold.otf")

INK = (43, 33, 24)
PAPER = (250, 243, 228)
WHITE = (255, 255, 255)
NIGHT = (18, 26, 58)

DAY_TOP, DAY_BOT = (110, 185, 240), (205, 235, 252)
NIGHT_TOP, NIGHT_BOT = (12, 16, 44), (40, 50, 105)

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# ----------------------------------------------------------------------------
# Utilitários matemáticos
# ----------------------------------------------------------------------------
def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def back_out(x):
    x = clamp01(x)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def lerpc(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


# ----------------------------------------------------------------------------
# "Caneta": desenha em coordenadas 1920x1080 sobre a tela 4K
# ----------------------------------------------------------------------------
class Pen:
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img)

    @staticmethod
    def P(pts):
        return [(x * S, y * S) for x, y in pts]

    def poly(self, pts, fill, outline=INK, w=3):
        if w and outline:
            self.d.polygon(self.P(pts), fill=fill, outline=outline, width=int(w * S))
        else:
            self.d.polygon(self.P(pts), fill=fill)

    def circle(self, x, y, r, fill, outline=INK, w=3):
        if r <= 0:
            return
        box = [(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S]
        if w and outline:
            self.d.ellipse(box, fill=fill, outline=outline, width=int(w * S))
        else:
            self.d.ellipse(box, fill=fill)

    def ellipse(self, x0, y0, x1, y1, fill, outline=INK, w=3):
        box = [min(x0, x1) * S, min(y0, y1) * S, max(x0, x1) * S, max(y0, y1) * S]
        if w and outline:
            self.d.ellipse(box, fill=fill, outline=outline, width=int(w * S))
        else:
            self.d.ellipse(box, fill=fill)

    def line(self, pts, fill=INK, w=4):
        self.d.line(self.P(pts), fill=fill, width=int(w * S), joint="curve")
        for x, y in (pts[0], pts[-1]):
            self.circle(x, y, w / 2, fill, None, 0)

    def rect(self, x0, y0, x1, y1, fill, outline=INK, w=3, r=0):
        box = [x0 * S, y0 * S, x1 * S, y1 * S]
        self.d.rounded_rectangle(box, radius=r * S, fill=fill,
                                 outline=outline if w else None, width=int(w * S) if w else 0)

    def arc(self, x0, y0, x1, y1, a0, a1, fill=INK, w=3):
        self.d.arc([x0 * S, y0 * S, x1 * S, y1 * S], a0, a1, fill=fill, width=int(w * S))

    def blob(self, circles, fill, w=3):
        """Vários círculos fundidos com um único contorno (nuvens, copas, lã)."""
        for x, y, r in circles:
            self.circle(x, y, r + w, INK, None, 0)
        for x, y, r in circles:
            self.circle(x, y, r, fill, None, 0)


# ----------------------------------------------------------------------------
# Fundos
# ----------------------------------------------------------------------------
_grad_cache = {}


def vgrad(c1, c2, cache=True):
    key = (c1, c2)
    if cache and key in _grad_cache:
        return _grad_cache[key].copy()
    col = np.linspace(0, 1, H * S)[:, None]
    arr = (np.array(c1)[None, :] * (1 - col) + np.array(c2)[None, :] * col).astype(np.uint8)
    img = Image.fromarray(arr[:, None, :]).resize((W * S, H * S), Image.NEAREST)
    if cache:
        _grad_cache[key] = img
        return img.copy()
    return img


_glow = None


def glow_layer(size, strength=1.0, color=(255, 244, 200)):
    """Brilho radial (para a luz do Dia 1). Retorna (rgb, mask)."""
    global _glow
    if _glow is None:
        n = 768
        yy, xx = np.mgrid[0:n, 0:n]
        r = np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (n / 2)
        a = np.clip(1 - r, 0, 1) ** 1.6
        _glow = Image.fromarray((a * 255).astype(np.uint8), "L")
    size = max(4, int(size))
    mask = _glow.resize((size, size), Image.BILINEAR)
    if strength < 1:
        mask = mask.point(lambda v: int(v * strength))
    return Image.new("RGB", (size, size), color), mask


def paste_glow(img, cx, cy, size, strength=1.0, color=(255, 244, 200)):
    rgb, mask = glow_layer(size * S, strength, color)
    s = rgb.size[0]
    img.paste(rgb, (int(cx * S - s / 2), int(cy * S - s / 2)), mask)


_texture = None


def paper_texture():
    """Textura de papel + vinheta suave (aplicada por multiplicação)."""
    global _texture
    if _texture is None:
        rng = np.random.default_rng(7)
        small = rng.normal(0, 1, (H // 3, W // 3))
        noise = np.array(Image.fromarray(((small * 18) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), dtype=float)
        fine = rng.normal(0, 4, (H, W))
        yy, xx = np.mgrid[0:H, 0:W]
        v = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
        vign = 1 - 0.16 * np.clip(v - 0.25, 0, 2) / 1.75
        val = (243 + (noise - 128) * 0.35 + fine) * vign
        val = val.clip(0, 255).astype(np.uint8)
        _texture = Image.merge("RGB", [Image.fromarray(val)] * 3)
    return _texture


# ----------------------------------------------------------------------------
# Elementos de cenário
# ----------------------------------------------------------------------------
FAR = dict(base=690, amp=28, freq=1 / 170, phase=0.5, start=1000, k=1.2)
NEAR = dict(base=790, amp=24, freq=1 / 140, phase=2.0, start=900, k=1.4)


def hill_y(x, h, off=0):
    return h["base"] + h["amp"] * math.sin(x * h["freq"] + h["phase"]) + max(0, x - h["start"]) * h["k"] + off


def draw_hill(pen, h, color, off=0):
    pts = [(x, hill_y(x, h, off)) for x in range(-40, W + 81, 24)]
    pts += [(W + 40, H + 400), (-40, H + 400)]
    pen.poly(pts, color)


def draw_sea(pen, t, level, night=0.0):
    back = lerpc((64, 144, 206), NIGHT, night * 0.6)
    front = lerpc((92, 178, 228), NIGHT, night * 0.6)
    pts = [(x, level + 10 * math.sin(x / 110 + t * 1.6)) for x in range(-40, W + 81, 30)]
    pen.poly(pts + [(W + 40, H + 40), (-40, H + 40)], back)
    pts = [(x, level + 48 + 12 * math.sin(x / 90 - t * 2.1 + 1)) for x in range(-40, W + 81, 30)]
    pen.poly(pts + [(W + 40, H + 40), (-40, H + 40)], front)
    # brilhos na água
    for i in range(7):
        x = (i * 287 + t * 40) % (W + 200) - 100
        y = level + 110 + (i % 3) * 70
        pen.line([(x, y), (x + 40, y)], lerpc(WHITE, NIGHT, night * 0.6), 4)


def cloud(pen, x, y, s=1.0, color=WHITE):
    pen.blob([(x, y, 40 * s), (x + 45 * s, y - 18 * s, 52 * s), (x + 98 * s, y, 40 * s),
              (x + 48 * s, y + 14 * s, 40 * s)], color)


def tree(pen, x, ground, g, scale=1.0, night=0.0):
    g = clamp01(g)
    if g <= 0:
        return
    s = scale * back_out(g)
    pen.rect(x - 12 * s, ground - 115 * s, x + 12 * s, ground + 10, lerpc((140, 90, 45), NIGHT, night * 0.6), w=3)
    green = lerpc((86, 168, 72), NIGHT, night * 0.6)
    pen.blob([(x, ground - 165 * s, 62 * s), (x - 50 * s, ground - 125 * s, 46 * s),
              (x + 50 * s, ground - 125 * s, 46 * s), (x, ground - 115 * s, 40 * s)], green)
    if g > 0.85:
        fr = (g - 0.85) / 0.15
        red = lerpc((226, 62, 62), NIGHT, night * 0.6)
        for dx, dy in ((-30, -150), (25, -180), (40, -120), (-45, -110), (5, -130)):
            pen.circle(x + dx * s, ground + dy * s, 9 * s * fr, red, INK, 2)


def flower(pen, x, ground, g, color, night=0.0):
    g = clamp01(g)
    if g <= 0:
        return
    s = back_out(g)
    top = ground - 55 * s
    pen.line([(x, ground), (x, top)], lerpc((60, 140, 60), NIGHT, night * 0.6), 5)
    pen.poly([(x, ground - 20 * s), (x + 22 * s, ground - 32 * s), (x + 4 * s, ground - 14 * s)],
             lerpc((90, 170, 70), NIGHT, night * 0.6), INK, 2)
    c = lerpc(color, NIGHT, night * 0.6)
    for k in range(5):
        a = k * 2 * math.pi / 5
        pen.circle(x + math.cos(a) * 13 * s, top + math.sin(a) * 13 * s, 11 * s, c, INK, 2)
    pen.circle(x, top, 9 * s, lerpc((255, 210, 60), NIGHT, night * 0.6), INK, 2)


TREES = [(120, FAR, 1.0), (470, FAR, 0.95), (830, FAR, 1.05), (260, NEAR, 1.35)]
FLOWERS = [(90, (240, 110, 150)), (400, (255, 255, 255)), (560, (170, 120, 230)),
           (690, (255, 150, 60)), (860, (240, 110, 150)), (980, (255, 255, 255))]


def landscape(pen, t, rise=1.0, plants=lambda i: 1.0, night=0.0, sea=True, sea_level=600):
    if sea:
        draw_sea(pen, t, sea_level, night)
    off = (1 - ease(rise)) * 650
    draw_hill(pen, FAR, lerpc((132, 196, 104), NIGHT, night * 0.65), off)
    i = 0
    for x, h, sc in TREES:
        if h is FAR:
            tree(pen, x, hill_y(x, FAR, off) + 6, plants(i), sc, night)
            i += 1
    draw_hill(pen, NEAR, lerpc((102, 176, 82), NIGHT, night * 0.65), off)
    for x, h, sc in TREES:
        if h is NEAR:
            tree(pen, x, hill_y(x, NEAR, off) + 10, plants(i), sc, night)
            i += 1
    for x, c in FLOWERS:
        flower(pen, x, hill_y(x, NEAR, off) + 40, plants(i), c, night)
        i += 1


def sun(pen, x, y, r, t, face=True):
    rays = 12
    for k in range(rays):
        a = t * 0.4 + k * 2 * math.pi / rays
        a1, a2 = a - 0.11, a + 0.11
        pts = [(x + math.cos(a1) * r * 1.15, y + math.sin(a1) * r * 1.15),
               (x + math.cos(a) * r * 1.55, y + math.sin(a) * r * 1.55),
               (x + math.cos(a2) * r * 1.15, y + math.sin(a2) * r * 1.15)]
        pen.poly(pts, (255, 180, 50), INK, 3)
    pen.circle(x, y, r, (255, 210, 64), INK, 4)
    if face:
        pen.ellipse(x - r * 0.38, y - r * 0.28, x - r * 0.22, y - r * 0.02, INK, None, 0)
        pen.ellipse(x + r * 0.22, y - r * 0.28, x + r * 0.38, y - r * 0.02, INK, None, 0)
        pen.arc(x - r * 0.42, y - r * 0.3, x + r * 0.42, y + r * 0.5, 25, 155, INK, 4)
        pen.circle(x - r * 0.55, y + r * 0.2, r * 0.12, (255, 150, 110), None, 0)
        pen.circle(x + r * 0.55, y + r * 0.2, r * 0.12, (255, 150, 110), None, 0)


def moon(img, x, y, r, color=(250, 244, 210)):
    d = int(2 * r * S)
    m = Image.new("L", (d, d), 0)
    dm = ImageDraw.Draw(m)
    dm.ellipse([0, 0, d - 1, d - 1], fill=255)
    dm.ellipse([d * 0.32, -d * 0.08, d * 1.3, d * 0.92], fill=0)
    img.paste(color, (int((x - r) * S), int((y - r) * S)), m)


def star(pen, x, y, r, color=(255, 238, 170)):
    if r <= 0.5:
        return
    pts = []
    for k in range(8):
        a = k * math.pi / 4 - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.38
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    pen.poly(pts, color, None, 0)


RNG = random.Random(42)
STARS = [(RNG.uniform(0, W), RNG.uniform(0, 560), RNG.uniform(6, 15), RNG.uniform(0, 6.28)) for _ in range(70)]
DUST = [(RNG.uniform(0, W), RNG.uniform(0, H), RNG.uniform(2, 6), RNG.uniform(0, 6.28)) for _ in range(90)]


def stars(pen, t, amount=1.0, xmin=0):
    for x, y, r, ph in STARS:
        if x < xmin:
            continue
        tw = 0.65 + 0.35 * math.sin(t * 3 + ph)
        star(pen, x, y, r * tw * amount)


def fish(pen, x, y, s, color, direction=1):
    d = direction
    tail = [(x - d * 38 * s, y), (x - d * 70 * s, y - 24 * s), (x - d * 70 * s, y + 24 * s)]
    pen.poly(tail, color, INK, 3)
    pen.ellipse(x - 45 * s, y - 25 * s, x + 45 * s, y + 25 * s, color, INK, 3)
    pen.arc(x - d * 10 * s - 20 * s, y - 18 * s, x - d * 10 * s + 20 * s, y + 18 * s,
            -60 if d > 0 else 120, 60 if d > 0 else 240, INK, 2)
    pen.circle(x + d * 24 * s, y - 6 * s, 8 * s, WHITE, INK, 2)
    pen.circle(x + d * 26 * s, y - 6 * s, 3.5 * s, INK, None, 0)


def bird(pen, x, y, s, flap, color=(250, 120, 90)):
    f = math.sin(flap)
    pen.ellipse(x - 22 * s, y - 13 * s, x + 22 * s, y + 13 * s, color, INK, 3)
    pen.poly([(x - 4 * s, y - 2 * s), (x - 34 * s, y - 36 * s * f), (x - 18 * s, y + 4 * s)], color, INK, 3)
    pen.poly([(x + 4 * s, y - 2 * s), (x - 10 * s, y - 40 * s * f), (x + 14 * s, y + 2 * s)], lerpc(color, WHITE, 0.25), INK, 3)
    pen.poly([(x + 20 * s, y - 4 * s), (x + 34 * s, y), (x + 20 * s, y + 5 * s)], (255, 200, 60), INK, 2)
    pen.circle(x + 12 * s, y - 4 * s, 3 * s, INK, None, 0)


# --- animais (origem = pés, olhando para a direita) -------------------------
def sheep(pen, x, y, s, t):
    for dx in (-35, -15, 15, 35):
        lift = 6 * max(0, math.sin(t * 8 + dx)) * s
        pen.rect(x + dx * s - 6 * s, y - 40 * s - lift, x + dx * s + 6 * s, y - lift, INK, None, 0, 3)
    pen.blob([(x - 40 * s, y - 70 * s, 28 * s), (x - 10 * s, y - 85 * s, 32 * s), (x + 25 * s, y - 75 * s, 30 * s),
              (x - 20 * s, y - 55 * s, 28 * s), (x + 15 * s, y - 55 * s, 26 * s)], (248, 246, 240))
    pen.ellipse(x + 40 * s, y - 100 * s, x + 80 * s, y - 60 * s, (70, 60, 55), INK, 3)
    pen.ellipse(x + 30 * s, y - 98 * s, x + 50 * s, y - 86 * s, (70, 60, 55), INK, 2)
    pen.circle(x + 66 * s, y - 84 * s, 5 * s, WHITE, None, 0)
    pen.circle(x + 67 * s, y - 84 * s, 2.5 * s, INK, None, 0)


def rabbit(pen, x, y, s, t):
    hop = abs(math.sin(t * 5)) * 45 * s
    y = y - hop
    c = (205, 175, 145)
    pen.circle(x - 38 * s, y - 40 * s, 13 * s, WHITE, INK, 3)
    pen.ellipse(x - 40 * s, y - 75 * s, x + 25 * s, y, c, INK, 3)
    pen.ellipse(x + 8 * s, y - 150 * s, x + 26 * s, y - 85 * s, c, INK, 3)
    pen.ellipse(x + 26 * s, y - 145 * s, x + 44 * s, y - 82 * s, c, INK, 3)
    pen.circle(x + 28 * s, y - 75 * s, 28 * s, c, INK, 3)
    pen.circle(x + 38 * s, y - 82 * s, 4 * s, INK, None, 0)
    pen.circle(x + 54 * s, y - 70 * s, 4 * s, (240, 120, 140), None, 0)


def lion(pen, x, y, s, t):
    body = (232, 172, 82)
    pen.line([(x - 70 * s, y - 70 * s), (x - 105 * s, y - 100 * s + 8 * math.sin(t * 3) * s)], INK, 5)
    pen.circle(x - 105 * s, y - 100 * s + 8 * math.sin(t * 3) * s, 11 * s, (170, 90, 40), INK, 2)
    for dx in (-55, -30, 25, 45):
        lift = 6 * max(0, math.sin(t * 7 + dx)) * s
        pen.rect(x + dx * s - 9 * s, y - 50 * s - lift, x + dx * s + 9 * s, y - lift, body, INK, 3, 5)
    pen.ellipse(x - 80 * s, y - 105 * s, x + 60 * s, y - 35 * s, body, INK, 3)
    mane = [(x + 55 * s + math.cos(a) * 52 * s, y - 115 * s + math.sin(a) * 52 * s, 20 * s)
            for a in np.linspace(0, 2 * math.pi, 11)[:-1]]
    pen.blob(mane, (186, 98, 40))
    pen.circle(x + 55 * s, y - 115 * s, 40 * s, (244, 196, 110), INK, 3)
    pen.circle(x + 42 * s, y - 124 * s, 5 * s, INK, None, 0)
    pen.circle(x + 70 * s, y - 124 * s, 5 * s, INK, None, 0)
    pen.poly([(x + 49 * s, y - 108 * s), (x + 63 * s, y - 108 * s), (x + 56 * s, y - 99 * s)], (120, 60, 40), None, 0)
    pen.arc(x + 42 * s, y - 108 * s, x + 70 * s, y - 88 * s, 20, 160, INK, 3)


def elephant(pen, x, y, s, t):
    c = (156, 166, 182)
    for dx in (-60, -25, 25, 55):
        lift = 5 * max(0, math.sin(t * 5 + dx)) * s
        pen.rect(x + dx * s - 16 * s, y - 70 * s - lift, x + dx * s + 16 * s, y - lift, c, INK, 3, 8)
    pen.ellipse(x - 95 * s, y - 175 * s, x + 75 * s, y - 50 * s, c, INK, 3)
    sw = math.sin(t * 2) * 10 * s
    pen.line([(x + 95 * s, y - 120 * s), (x + 118 * s, y - 80 * s), (x + 120 * s + sw, y - 40 * s)], INK, 30)
    pen.line([(x + 95 * s, y - 120 * s), (x + 118 * s, y - 80 * s), (x + 120 * s + sw, y - 40 * s)], c, 24)
    pen.circle(x + 80 * s, y - 145 * s, 48 * s, c, INK, 3)
    pen.ellipse(x + 22 * s, y - 185 * s, x + 75 * s, y - 100 * s, (190, 160, 175), INK, 3)
    pen.circle(x + 98 * s, y - 158 * s, 6 * s, INK, None, 0)


def person(pen, x, y, s, skin, hair, tunic, female=False, wave_t=None):
    # cabelo comprido atrás (Eva)
    if female:
        pen.ellipse(x - 52 * s, y - 300 * s, x + 52 * s, y - 175 * s, hair, INK, 3)
    pen.rect(x - 22 * s, y - 90 * s, x - 6 * s, y, skin, INK, 3, 6)
    pen.rect(x + 6 * s, y - 90 * s, x + 22 * s, y, skin, INK, 3, 6)
    pen.poly([(x - 34 * s, y - 200 * s), (x + 34 * s, y - 200 * s), (x + 50 * s, y - 80 * s), (x - 50 * s, y - 80 * s)],
             tunic, INK, 3)
    # folhinhas na roupa
    for k in range(4):
        lx = x - 36 * s + k * 24 * s
        pen.poly([(lx, y - 80 * s), (lx + 12 * s, y - 64 * s), (lx + 24 * s, y - 80 * s)], lerpc(tunic, INK, 0.15), INK, 2)
    pen.circle(x, y - 240 * s, 42 * s, skin, INK, 3)
    if female:
        pen.arc(x - 46 * s, y - 290 * s, x + 46 * s, y - 210 * s, 180, 360, hair, 22)
        pen.circle(x + 34 * s, y - 274 * s, 10 * s, (240, 110, 150), INK, 2)
    else:
        pen.blob([(x - 26 * s, y - 274 * s, 18 * s), (x, y - 282 * s, 20 * s), (x + 26 * s, y - 274 * s, 18 * s)], hair)
    pen.circle(x - 14 * s, y - 242 * s, 5 * s, INK, None, 0)
    pen.circle(x + 14 * s, y - 242 * s, 5 * s, INK, None, 0)
    pen.arc(x - 16 * s, y - 240 * s, x + 16 * s, y - 214 * s, 20, 160, INK, 3)
    pen.circle(x - 26 * s, y - 226 * s, 7 * s, (240, 140, 120), None, 0)
    pen.circle(x + 26 * s, y - 226 * s, 7 * s, (240, 140, 120), None, 0)


def heart(pen, cx, cy, size, color=(232, 70, 90)):
    pts = []
    for k in range(60):
        a = k * 2 * math.pi / 60
        hx = 16 * math.sin(a) ** 3
        hy = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((cx + hx * size / 16, cy + hy * size / 16))
    pen.poly(pts, color, INK, 4)
    pen.circle(cx - size * 0.45, cy - size * 0.35, size * 0.12, lerpc(color, WHITE, 0.6), None, 0)


def pencil(pen, x, y, ang=-0.9, L=260):
    ca, sa = math.cos(ang), math.sin(ang)

    def T(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)
    w = 26
    pen.poly([T(0, 0), T(-50, -w / 2), T(-50, w / 2)], (245, 215, 170), INK, 3)
    pen.poly([T(0, 0), T(-17, -w / 6), T(-17, w / 6)], INK, None, 0)
    pen.poly([T(-50, -w / 2), T(-L, -w / 2), T(-L, w / 2), T(-50, w / 2)], (255, 196, 40), INK, 3)
    pen.poly([T(-L, -w / 2), T(-L - 22, -w / 2), T(-L - 22, w / 2), T(-L, w / 2)], (180, 180, 190), INK, 3)
    pen.poly([T(-L - 22, -w / 2), T(-L - 60, -w / 2), T(-L - 60, w / 2), T(-L - 22, w / 2)], (245, 140, 160), INK, 3)


# ----------------------------------------------------------------------------
# Texto (desenhado já em 1080p)
# ----------------------------------------------------------------------------
def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if draw.textlength(test, font=fnt) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def overlay_subtitle(img, text, alpha):
    if alpha <= 0:
        return img
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = font(F_SUB, 46)
    lines = wrap(d, text, f, 1500)
    lh = 60
    tw = max(d.textlength(l, font=f) for l in lines)
    bh = lh * len(lines) + 34
    y0 = H - 70 - bh
    d.rounded_rectangle([W / 2 - tw / 2 - 36, y0, W / 2 + tw / 2 + 36, y0 + bh], radius=26,
                        fill=(28, 22, 16, int(185 * alpha)))
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + 17 + i * lh + lh / 2), l, font=f, fill=(255, 255, 255, int(255 * alpha)), anchor="mm")
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def overlay_badge(img, text, alpha=1.0):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = font(F_BOLD, 44)
    tw = d.textlength(text, font=f)
    a = int(255 * alpha)
    d.rounded_rectangle([50, 44, 50 + tw + 56, 120], radius=22, fill=PAPER + (a,), outline=INK + (a,), width=4)
    d.text((50 + 28 + tw / 2, 82), text, font=f, fill=INK + (a,), anchor="mm")
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def overlay_text(img, text, xy, size, color, alpha=1.0, fpath=F_TITLE, stroke=0, stroke_color=INK):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    a = int(255 * clamp01(alpha))
    d.text(xy, text, font=font(fpath, size), fill=color + (a,), anchor="mm",
           stroke_width=stroke, stroke_fill=stroke_color + (a,))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


# ----------------------------------------------------------------------------
# Cenas — cada uma recebe (t, d, cues) e devolve a imagem 4K
#   t = tempo dentro da cena, d = duração, cues = início de cada fala
# ----------------------------------------------------------------------------
def sc_intro(t, d, cues):
    img = vgrad(PAPER, (244, 228, 200))
    pen = Pen(img)
    # rabiscos decorativos
    for i, (x, y) in enumerate([(300, 260), (1620, 250), (380, 820), (1560, 840), (960, 170)]):
        g = ease((t - 0.2 - i * 0.15) / 0.6)
        star(pen, x, y, 26 * g, (255, 196, 60))
    # título revelado pelo lápis
    f = font(F_TITLE, 150 * S)
    if not hasattr(sc_intro, "mask"):
        m = Image.new("L", (W * S, H * S), 0)
        ImageDraw.Draw(m).text((W * S / 2, 470 * S), "Bíblia em Traços", font=f, fill=255, anchor="mm")
        sc_intro.mask = m
        sc_intro.bbox = m.getbbox()
    x0, _, x1, _ = sc_intro.bbox
    p = ease((t - 0.4) / 2.4)
    rx = x0 + (x1 - x0) * p
    m = sc_intro.mask.copy()
    ImageDraw.Draw(m).rectangle([rx, 0, W * S, H * S], fill=0)
    img.paste(INK, (0, 0), m)
    if 0.3 < t < 3.3:
        pencil(pen, rx / S + 10, 520 + 18 * math.sin(t * 22), -0.95)
    # sublinhado colorido
    u = ease((t - 2.6) / 0.8)
    if u > 0:
        ux0, ux1 = x0 / S, x0 / S + (x1 - x0) / S * u
        pen.line([(ux0, 590), (ux1, 590 + 6 * math.sin(ux1 / 60))], (232, 90, 70), 12)
    return img


def ov_intro(img, t, d):
    return overlay_text(img, "histórias da Bíblia desenhadas para toda a família", (W / 2, 680), 44, (120, 84, 50),
                        ease((t - 3.0) / 0.8), F_SUB)


def sc_title(t, d, cues):
    img = vgrad(PAPER, (244, 228, 200))
    pen = Pen(img)
    sun(pen, 960, 300 + 6 * math.sin(t * 2), 90 * back_out(t / 0.9), t)
    for x, y in [(330, 760), (1590, 760)]:
        star(pen, x, y, 30 * ease(t - 0.5), (255, 196, 60))
    return img


def ov_title(img, t, d):
    a = ease((t - 0.4) / 0.6)
    img = overlay_text(img, "A Criação", (W / 2, 600), 160, INK, a)
    return overlay_text(img, "Gênesis 1 e 2", (W / 2, 730), 54, (150, 90, 50), ease((t - 1.0) / 0.6), F_BOLD)


def sc_dark(t, d, cues):
    img = vgrad((8, 10, 22), (22, 25, 48))
    pen = Pen(img)
    for x, y, r, ph in DUST:
        xx = (x + t * 12 * math.sin(ph)) % W
        yy = (y - t * 8) % H
        pen.circle(xx, yy, r * (0.7 + 0.3 * math.sin(t * 2 + ph)), (52, 60, 98), None, 0)
    if len(cues) > 1 and t > cues[1]:
        g = ease((t - cues[1]) / 2.5)
        paste_glow(img, 960, 470, 260 + 60 * math.sin(t * 2.5), 0.55 * g)
    return img


def sc_day1(t, d, cues):
    dark = vgrad((8, 10, 22), (22, 25, 48))
    light_bg = vgrad((255, 248, 222), (255, 222, 160))
    p = ease((t - 0.6) / 3.0)
    if p < 1:
        img = dark
        if p > 0:
            paste_glow(img, 960, 470, lerp(80, 4600, p))
            if p > 0.7:
                img = Image.blend(img, light_bg, (p - 0.7) / 0.3)
    else:
        img = light_bg
    pen = Pen(img)
    split_start = cues[1] if len(cues) > 1 else d
    s = ease((t - split_start) / 1.6)
    if s > 0:
        edge = W * S * (1 - 0.5 * s)
        row = np.clip((edge - np.arange(W * S)) / (160 * S) * 255 + 127, 0, 255).astype(np.uint8)
        mask = Image.fromarray(row[None, :]).resize((W * S, H * S), Image.NEAREST)
        night = vgrad(NIGHT_TOP, NIGHT_BOT)
        npen = Pen(night)
        stars(npen, t, 1.0, xmin=960)
        img = Image.composite(img, night, mask)
        pen = Pen(img)
    # raios de luz girando
    if 0.5 < p:
        for k in range(10):
            a = t * 0.25 + k * 2 * math.pi / 10
            r0, r1 = 120, 900
            pts = [(960 + math.cos(a - 0.05) * r0, 470 + math.sin(a - 0.05) * r0),
                   (960 + math.cos(a) * r1, 470 + math.sin(a) * r1),
                   (960 + math.cos(a + 0.05) * r0, 470 + math.sin(a + 0.05) * r0)]
            if s <= 0:
                pen.poly(pts, (255, 236, 175), None, 0)
    return img


def ov_day1(img, t, d, cues):
    split_start = cues[1] if len(cues) > 1 else d
    a = ease((t - split_start - 1.0) / 0.6)
    if a > 0:
        img = overlay_text(img, "DIA", (480, 430), 120, (220, 140, 40), a, F_TITLE, 6, WHITE)
        img = overlay_text(img, "NOITE", (1440, 430), 120, (230, 230, 255), a, F_TITLE, 6, INK)
    return img


def sc_day2(t, d, cues):
    img = vgrad(DAY_TOP, DAY_BOT)
    pen = Pen(img)
    for i, (x, y, s) in enumerate([(200, 180, 1.1), (900, 120, 0.9), (1450, 220, 1.2)]):
        cloud(pen, (x + t * (14 + 4 * i)) % (W + 300) - 150, y, s * ease((t - 1.2 - i * 0.3) / 0.8))
    level = lerp(1150, 600, ease((t - 0.3) / 3.2))
    draw_sea(pen, t, level)
    return img


def sc_day3(t, d, cues):
    img = vgrad(DAY_TOP, DAY_BOT)
    pen = Pen(img)
    for x, y, s in [(200, 160, 1.0), (1300, 140, 1.1)]:
        cloud(pen, (x + t * 15) % (W + 300) - 150, y, s)
    start = cues[1] if len(cues) > 1 else 3.0
    landscape(pen, t, rise=(t - 0.3) / 2.8, plants=lambda i: (t - start - i * 0.3) / 0.9)
    return img


def sc_day4(t, d, cues):
    half = cues[1] if len(cues) > 1 else d / 2
    n = ease((t - half + 0.4) / 1.8)
    img = vgrad(lerpc(DAY_TOP, NIGHT_TOP, n), lerpc(DAY_BOT, NIGHT_BOT, n), cache=False)
    pen = Pen(img)
    if n > 0:
        stars(pen, t, n)
        moon(img, lerp(1500, 1450, n), lerp(700, 190, n), 80)
    # sol nasce por trás dos montes e depois se põe
    rise = ease(t / (half * 0.8))
    sx = lerp(240, 900, rise) + 700 * n
    sy = lerp(820, 230, rise) + 700 * n
    if sy < 1000:
        sun(pen, sx, sy, 95, t)
    landscape(pen, t, night=n)
    return img


FISH = [(0, 760, 0.9, (255, 150, 60), 1, 70), (1, 870, 1.1, (250, 210, 70), -1, 55),
        (2, 980, 0.8, (240, 110, 150), 1, 85), (3, 910, 0.7, (130, 210, 120), -1, 95)]


def sc_day5(t, d, cues):
    img = vgrad(DAY_TOP, DAY_BOT)
    pen = Pen(img)
    sun(pen, 1650, 170, 70, t)
    cloud(pen, (300 + t * 15) % (W + 300) - 150, 150, 0.9)
    draw_sea(pen, t, 600)
    appear = ease((t - 0.5) / 1.0)
    for i, y, s, c, dr, spd in FISH:
        span = W - 1180
        x = 1180 + ((i * 210 + dr * t * spd) % span)
        fish(pen, x, y + 10 * math.sin(t * 2 + i), s * appear, c, dr)
    # peixe pulando
    jt = (t % 3.2) / 1.4
    if jt < 1 and appear > 0.5:
        jx = lerp(1350, 1650, jt)
        jy = 640 - math.sin(jt * math.pi) * 260
        fish(pen, jx, jy, 0.9, (90, 170, 240), 1)
    landscape(pen, t, sea=False)
    bstart = cues[1] if len(cues) > 1 else 3.0
    if t > bstart - 0.5:
        for k in range(5):
            bx = -100 + (t - bstart + 0.5) * (170 + k * 18) + (k % 2) * 140 - k * 90
            by = 200 + k * 55 + 20 * math.sin(t * 2 + k)
            bird(pen, bx, by, 1.0 - k * 0.08, t * 12 + k, [(250, 120, 90), (90, 160, 240), (250, 200, 60),
                                                           (170, 120, 230), (240, 110, 150)][k])
    return img


def sc_day6(t, d, cues):
    img = vgrad(DAY_TOP, DAY_BOT)
    pen = Pen(img)
    sun(pen, 1650, 170, 70, t)
    cloud(pen, (600 + t * 15) % (W + 300) - 150, 140, 1.0)
    landscape(pen, t)
    walk = ease(t / 4.0)
    elephant(pen, lerp(-300, 1090, ease((t - 0.3) / 4.5)), 860, 1.05, t)
    lion(pen, lerp(-300, 880, ease((t - 0.8) / 4.0)), 880, 1.05, t)
    sheep(pen, lerp(-250, 150, walk), 880, 1.2, t)
    rabbit(pen, lerp(-200, 350, ease((t - 0.5) / 3.5)), 880, 1.1, t if t < 4.2 else 0)
    p_start = cues[1] if len(cues) > 1 else d / 2
    g = back_out((t - p_start) / 0.9)
    if t > p_start:
        person(pen, 560, 885, 1.05 * g, (190, 130, 90), (70, 45, 30), (110, 170, 70))
        person(pen, 720, 885, 1.0 * g, (200, 140, 100), (120, 70, 35), (150, 190, 80), female=True)
        if g > 0.9:
            pen.line([(594, 740), (640, 755), (686, 740)], (195, 135, 95), 12)
        hg = ease((t - p_start - 1.0) / 0.8)
        if hg > 0:
            heart(pen, 640, 470 + 8 * math.sin(t * 3), 60 * hg * (1 + 0.06 * math.sin(t * 6)))
    return img


def sc_day7(t, d, cues):
    img = vgrad((132, 112, 196), (255, 188, 118))
    pen = Pen(img)
    sun(pen, 1550, 640 + t * 4, 120, t * 0.3)
    draw_sea(pen, t * 0.5, 600)
    landscape(pen, t * 0.5, sea=False)
    elephant(pen, 1090, 860, 1.05, 0)
    lion(pen, 880, 880, 1.05, 0)
    sheep(pen, 150, 880, 1.2, 0)
    rabbit(pen, 350, 880, 1.1, 0)
    person(pen, 560, 885, 1.05, (190, 130, 90), (70, 45, 30), (110, 170, 70))
    person(pen, 720, 885, 1.0, (200, 140, 100), (120, 70, 35), (150, 190, 80), female=True)
    pen.line([(594, 740), (640, 755), (686, 740)], (195, 135, 95), 12)
    a = ease((t - d * 0.55) / 2)
    for x, y, r, ph in STARS[:25]:
        star(pen, x, y * 0.6, r * a * (0.7 + 0.3 * math.sin(t * 3 + ph)))
    # "Zzz" do descanso
    if len(cues) > 1 and t > cues[1]:
        for k in range(3):
            z = ((t - cues[1]) * 0.6 + k / 3) % 1
            zx, zy = 1150 + z * 80 + k * 10, 600 - z * 200
            sz = 18 + z * 18
            pen.line([(zx, zy), (zx + sz, zy), (zx, zy + sz), (zx + sz, zy + sz)], WHITE, 5)
    return img


def sc_lesson(t, d, cues):
    img = vgrad((255, 240, 220), (250, 210, 190))
    pen = Pen(img)
    for k in range(14):
        a = k * 2 * math.pi / 14 + t * 0.3
        r = 330 + 20 * math.sin(t * 2 + k)
        star(pen, 960 + math.cos(a) * r, 430 + math.sin(a) * r * 0.8, 18 + 6 * math.sin(t * 4 + k), (255, 190, 60))
    beat = 1 + 0.07 * max(0, math.sin(t * 5)) ** 4
    heart(pen, 960, 430, 190 * back_out(t / 1.0) * beat)
    if len(cues) > 1 and t > cues[1]:
        g = back_out((t - cues[1]) / 0.7)
        # uma criança pequena dentro do coração
        person(pen, 960, 560, 0.62 * g, (210, 150, 110), (60, 40, 25), (90, 160, 230))
    return img


def sc_end(t, d, cues):
    img = vgrad(PAPER, (244, 228, 200))
    pen = Pen(img)
    pulse = 1 + 0.05 * math.sin(t * 5)
    bw, bh = 520 * pulse, 130 * pulse
    pen.rect(960 - bw / 2, 330 - bh / 2, 960 + bw / 2, 330 + bh / 2, (226, 52, 52), INK, 5, 40)
    # espaços para os elementos de tela final do YouTube (vídeo + playlist)
    for x in (250, 1100):
        pen.rect(x, 520, x + 570, 840, (255, 252, 244), (200, 170, 130), 4, 24)
    star(pen, 960, 170, 28, (255, 196, 60))
    return img


def ov_end(img, t, d):
    pulse = 1 + 0.05 * math.sin(t * 5)
    img = overlay_text(img, "INSCREVA-SE", (W / 2, 330), int(66 * pulse), WHITE, 1, F_TITLE)
    img = overlay_text(img, "Próxima história", (535, 680), 46, (150, 110, 70), 1, F_BOLD)
    img = overlay_text(img, "Todas as histórias", (1385, 680), 46, (150, 110, 70), 1, F_BOLD)
    return overlay_text(img, "Bíblia em Traços", (W / 2, 950), 54, INK, 1, F_TITLE)


# ----------------------------------------------------------------------------
# Roteiro do episódio (mesmo texto do roteiro 01, para narração)
# ----------------------------------------------------------------------------
SCENES = [
    dict(name="intro", func=sc_intro, dur=5.0, overlay=ov_intro, subs=[],
         say=[(2.9, "Bíblia em Traços!")]),
    dict(name="titulo", func=sc_title, dur=4.5, overlay=ov_title, subs=[],
         say=[(0.9, "A Criação.")]),
    dict(name="escuridao", func=sc_dark, subs=[
        "No princípio, antes de existir qualquer coisa, tudo era escuro e vazio.",
        "Não havia céu, nem terra, nem mar... Mas Deus já estava lá.",
    ]),
    dict(name="dia1", func=sc_day1, badge="Dia 1", overlay=ov_day1, subs=[
        "Então Deus disse: “Haja luz!” E a luz apareceu!",
        "Deus viu que a luz era boa. Ele chamou a luz de dia, e a escuridão de noite.",
    ]),
    dict(name="dia2", func=sc_day2, badge="Dia 2", subs=[
        "No segundo dia, Deus separou as águas e fez o céu, lá no alto.",
        "Em cima, o céu azul. Embaixo, as águas do mar.",
    ]),
    dict(name="dia3", func=sc_day3, badge="Dia 3", subs=[
        "No terceiro dia, Deus juntou as águas e fez aparecer a terra seca.",
        "E da terra brotaram plantas, flores e árvores cheias de frutos!",
    ]),
    dict(name="dia4", func=sc_day4, badge="Dia 4", subs=[
        "No quarto dia, Deus colocou no céu o sol, para brilhar durante o dia...",
        "...e a lua e as estrelas, para iluminar a noite.",
    ]),
    dict(name="dia5", func=sc_day5, badge="Dia 5", subs=[
        "No quinto dia, Deus encheu as águas de peixes de todos os tamanhos...",
        "...e o céu de passarinhos que voavam e cantavam.",
    ]),
    dict(name="dia6", func=sc_day6, badge="Dia 6", subs=[
        "No sexto dia, Deus fez os animais da terra: ovelhas, coelhos, leões, elefantes...",
        "E então Deus fez a sua criação mais especial: o homem e a mulher, Adão e Eva.",
        "Deus os fez parecidos com Ele, para cuidarem com carinho de tudo o que Ele criou.",
    ]),
    dict(name="dia7", func=sc_day7, badge="Dia 7", subs=[
        "Deus olhou para tudo o que tinha feito, e viu que era muito bom!",
        "No sétimo dia, Deus descansou, e fez desse dia um dia especial.",
    ]),
    dict(name="licao", func=sc_lesson, subs=[
        "Tudo o que existe foi feito por Deus, com muito amor.",
        "E sabe quem mais Ele fez com todo o carinho? Você!",
        "Agora converse com sua família: qual parte da criação você mais gosta?",
    ]),
    dict(name="final", func=sc_end, dur=12.0, overlay=ov_end, subs=[
        "Inscreva-se no canal! Na próxima história: Adão e Eva no Jardim do Éden.",
    ]),
]

LEAD, TAIL, FADE = 1.0, 1.0, 0.45
GAP = 1.1  # respiro entre uma fala e a próxima

# ----------------------------------------------------------------------------
# Narração (voz neural Kokoro, roda offline depois de baixar o modelo)
# ----------------------------------------------------------------------------
VOICE = os.environ.get("VOZ", "pf_dora")  # pf_dora (feminina) · pm_alex · pm_santa (masculinas)
VOICE_SPEED = float(os.environ.get("VELOCIDADE_VOZ", "0.88"))
MODEL_DIR = os.environ.get("KOKORO_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelos"))
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
NARR_DIR = os.path.join(OUT, "narracao")
NARR_SR = 44100
_narr_len = None


def narration_lengths():
    """Duração (s) de cada fala já sintetizada; vazio se a narração ainda não foi gerada."""
    global _narr_len
    if _narr_len is None:
        path = os.path.join(NARR_DIR, "duracoes.json")
        if os.path.exists(path):
            import json
            with open(path, encoding="utf-8") as fh:
                _narr_len = json.load(fh)
        else:
            _narr_len = {}
    return _narr_len


def tts_text(text):
    """Limpa o texto da legenda para a voz ler com naturalidade."""
    t = text.replace("“", "").replace("”", "").replace('"', "")
    t = t.strip(". ").replace("...", ",") if t.startswith("...") else t.replace("...", ",")
    return t.strip(" ,")


def all_lines():
    lines = []
    for sc in SCENES:
        lines += list(sc["subs"]) + [txt for _, txt in sc.get("say", [])]
    return lines


def synthesize_narration():
    """Gera um .wav (44.1 kHz) por fala e grava as durações em duracoes.json."""
    import json
    import urllib.request

    import soundfile as sf
    from kokoro_onnx import Kokoro

    os.makedirs(MODEL_DIR, exist_ok=True)
    for fn in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        dst = os.path.join(MODEL_DIR, fn)
        if not os.path.exists(dst):
            print(f"Baixando modelo de voz: {fn} ...", flush=True)
            urllib.request.urlretrieve(MODEL_URL + fn, dst)
    kok = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    os.makedirs(NARR_DIR, exist_ok=True)
    lengths = {}
    for i, line in enumerate(all_lines()):
        raw = os.path.join(NARR_DIR, f"bruto_{i:02d}.wav")
        wav = os.path.join(NARR_DIR, f"fala_{i:02d}.wav")
        audio, sr = kok.create(tts_text(line), voice=VOICE, speed=VOICE_SPEED, lang="pt-br")
        # tira silêncio do começo/fim
        thr = 0.01 * np.abs(audio).max()
        idx = np.where(np.abs(audio) > thr)[0]
        audio = audio[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)]
        sf.write(raw, audio, sr)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ar", str(NARR_SR), "-ac", "1", wav], check=True)
        os.remove(raw)
        lengths[line] = sf.info(wav).duration
        print(f"  voz {i + 1:02d}: {lengths[line]:.1f}s  {line}", flush=True)
    with open(os.path.join(NARR_DIR, "duracoes.json"), "w", encoding="utf-8") as fh:
        json.dump(lengths, fh, ensure_ascii=False, indent=1)
    global _narr_len
    _narr_len = lengths


def sub_len(text):
    n = narration_lengths().get(text)
    if n is not None:
        return max(2.4, n + GAP)
    return max(3.4, len(text) / 12.5 + 1.0)


def build_timeline():
    t0 = 0.0
    for sc in SCENES:
        cues, ends, cur = [], [], LEAD
        for s in sc["subs"]:
            cues.append(cur)
            cur += sub_len(s)
            ends.append(cur)
        sc["cues"], sc["ends"] = cues, ends
        sc["dur"] = sc.get("dur") or cur + TAIL
        sc["start"] = t0
        t0 += sc["dur"]
    return t0


def render_frame(sc, t):
    d = sc["dur"]
    big = sc["func"](t, d, sc["cues"])
    img = big.reduce(S)
    img = ImageChops.multiply(img, paper_texture())
    ov = sc.get("overlay")
    if ov is not None:
        img = ov(img, t, d, sc["cues"]) if ov is ov_day1 else ov(img, t, d)
    if sc.get("badge"):
        img = overlay_badge(img, sc["badge"], ease((t - 0.2) / 0.5))
    for text, a0, a1 in zip(sc["subs"], sc["cues"], sc["ends"]):
        if a0 - 0.2 <= t <= a1:
            a = min(ease((t - a0 + 0.2) / 0.3), ease((a1 - t) / 0.25))
            img = overlay_subtitle(img, text, a)
    fade = min(ease(t / FADE), ease((d - t) / FADE))
    if fade < 1:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, fade)
    return img


def render_scene(idx):
    build_timeline()
    sc = SCENES[idx]
    path = os.path.join(OUT, "partes", f"{idx:02d}_{sc['name']}.mp4")
    n = int(round(sc["dur"] * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(render_frame(sc, f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    print(f"  cena pronta: {sc['name']} ({n} quadros)", flush=True)
    return path


# ----------------------------------------------------------------------------
# Trilha sonora original (C – G – Am – F, caixinha de música + pad suave)
# ----------------------------------------------------------------------------
def music(duration, path, sr=44100):
    n = int(duration * sr) + sr
    L, R = np.zeros(n), np.zeros(n)
    bpm = 76
    beat = 60 / bpm
    bar = 4 * beat
    chords = [[48, 60, 64, 67], [43, 59, 62, 67], [45, 60, 64, 69], [41, 60, 65, 69]]

    def f(m):
        return 440 * 2 ** ((m - 69) / 12)

    def add(start, length, freq, amp, kind, pan=0.0):
        i0 = int(start * sr)
        m = min(int(length * sr), n - i0)
        if m <= 0:
            return
        tt = np.arange(m) / sr
        if kind == "pad":
            env = np.minimum(1, tt / 0.8) * np.minimum(1, (length - tt) / 0.9)
            wv = np.sin(2 * np.pi * freq * tt) + 0.5 * np.sin(2 * np.pi * freq * 1.003 * tt) + 0.15 * np.sin(4 * np.pi * freq * tt)
        elif kind == "bell":
            env = np.exp(-tt * 3.2) * np.minimum(1, tt / 0.005)
            wv = np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(2 * np.pi * 2 * freq * tt) + 0.08 * np.sin(2 * np.pi * 3.01 * freq * tt)
        else:  # bass
            env = np.exp(-tt * 1.5) * np.minimum(1, tt / 0.02)
            wv = np.sin(2 * np.pi * freq * tt)
        sig = wv * env * amp
        L[i0:i0 + m] += sig * (1 - pan) / 2 * 2 ** 0.5
        R[i0:i0 + m] += sig * (1 + pan) / 2 * 2 ** 0.5

    nb = int(duration / bar) + 1
    pattern = [0, 1, 2, 3, 2, 1, 2, 1]
    for b in range(nb):
        ch = chords[b % 4]
        st = b * bar
        add(st, beat * 3.5, f(ch[0] - 12), 0.16, "bass")
        for m_ in ch[1:]:
            add(st, bar + 0.6, f(m_), 0.035, "pad", 0.0)
        arp = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24]
        if b >= 1:  # caixinha entra no 2º compasso
            for k, pi in enumerate(pattern):
                add(st + k * beat / 2, 1.6, f(arp[pi]), 0.05, "bell", -0.4 if k % 2 == 0 else 0.4)
    # eco suave (sensação de espaço)
    for dly, g in ((0.29, 0.28), (0.58, 0.14), (0.87, 0.07)):
        k = int(dly * sr)
        L[k:] += R[:-k] * g
        R[k:] += L[:-k] * g
    tt = np.arange(n) / sr
    env = np.minimum(1, tt / 2.0) * np.clip((duration - tt) / 4.0, 0, 1)
    L, R = L * env, R * env
    peak = max(np.abs(L).max(), np.abs(R).max())
    L, R = L / peak * 0.55, R / peak * 0.55
    mix = np.stack([L, R], axis=1)[: int(duration * sr)]
    if narration_lengths():
        mix = add_voice(mix, sr)
    data = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


def add_voice(mix, sr):
    """Coloca cada fala no tempo certo e abaixa a música (ducking) enquanto o narrador fala."""
    import soundfile as sf

    n = len(mix)
    voice = np.zeros(n)
    active = np.zeros(n)
    lines = all_lines()
    starts = []
    for sc in SCENES:
        starts += [sc["start"] + c for c in sc["cues"]]
        starts += [sc["start"] + t for t, _ in sc.get("say", [])]
    for i, (line, st) in enumerate(zip(lines, starts)):
        a, _ = sf.read(os.path.join(NARR_DIR, f"fala_{i:02d}.wav"))
        rms = np.sqrt(np.mean(a ** 2)) + 1e-9
        a = a * (0.11 / rms)  # nível uniforme entre as falas (~ -19 dBFS RMS)
        i0 = int(st * sr)
        m = min(len(a), n - i0)
        voice[i0:i0 + m] += a[:m]
        active[i0:i0 + m] = 1
    # envelope suave: a música desce 0,25 s antes da fala e volta 0,6 s depois
    def smooth(x, win):
        c = np.concatenate([[0.0], np.cumsum(x)])
        h = win // 2
        idx = np.arange(len(x))
        lo, hi = np.clip(idx - h, 0, len(x)), np.clip(idx + h, 0, len(x))
        return (c[hi] - c[lo]) / np.maximum(hi - lo, 1)

    env = np.clip(smooth(active, int(0.5 * sr)) * 2.5, 0, 1)  # cobre ~0,25 s antes/depois da fala
    env = smooth(env, int(0.6 * sr))                            # subida/descida suave
    duck = 1 - 0.8 * np.clip(env, 0, 1)
    out = mix * duck[:, None] + voice[:, None] * 0.95
    return 0.89 * np.tanh(out * 1.1) / np.tanh(1.1)  # limitador suave (pico ~ -1 dB)


def srt_time(x):
    h, x = divmod(x, 3600)
    m, x = divmod(x, 60)
    s = int(x)
    ms = int(round((x - s) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{int(h):02d}:{int(m):02d}:{s:02d},{ms:03d}"


def write_srt(path):
    k = 1
    with open(path, "w", encoding="utf-8") as fh:
        for sc in SCENES:
            for text, a0, a1 in zip(sc["subs"], sc["cues"], sc["ends"]):
                fh.write(f"{k}\n{srt_time(sc['start'] + a0)} --> {srt_time(sc['start'] + a1)}\n{text}\n\n")
                k += 1


def main():
    os.makedirs(os.path.join(OUT, "partes"), exist_ok=True)
    if "--thumbs" not in sys.argv and "--sem-voz" not in sys.argv:
        print(f"Gerando narração (voz {VOICE}) ...", flush=True)
        synthesize_narration()
    total = build_timeline()
    print(f"Duração total: {total:.1f} s ({int(total * FPS)} quadros)")
    if "--thumbs" in sys.argv:
        for i, sc in enumerate(SCENES):
            render_frame(sc, sc["dur"] * 0.75).save(os.path.join(OUT, f"previa_{i:02d}_{sc['name']}.png"))
        return
    write_srt(os.path.join(OUT, "ep01_a_criacao.srt"))
    music(total, os.path.join(OUT, "trilha.wav"))
    with Pool(os.cpu_count()) as pool:
        parts = pool.map(render_scene, range(len(SCENES)))
    lst = os.path.join(OUT, "partes", "lista.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{os.path.abspath(p)}'\n")
    final = os.path.join(OUT, "ep01_a_criacao.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", os.path.join(OUT, "trilha.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", final], check=True)
    shutil.rmtree(os.path.join(OUT, "partes"))
    if os.path.isdir(NARR_DIR):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(OUT, "trilha.wav"),
                        "-b:a", "192k", os.path.join(OUT, "audio_narrado.mp3")], check=True)
    print("Vídeo pronto:", final)


if __name__ == "__main__":
    main()
