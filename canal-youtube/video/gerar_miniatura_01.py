#!/usr/bin/env python3
"""Gera a miniatura (thumbnail 1280x720) do Episódio 01 — A Criação."""
import os
import sys

from PIL import Image, ImageChops, ImageDraw

import gerar_episodio_01 as ep

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "miniatura_ep01.png")
img = ep.vgrad((90, 170, 240), (190, 228, 252))
pen = ep.Pen(img)
ep.landscape(pen, 1.0)
ep.elephant(pen, 1090, 860, 1.05, 0)
ep.lion(pen, 880, 880, 1.05, 0)
ep.sheep(pen, 150, 880, 1.2, 0)
ep.rabbit(pen, 350, 880, 1.1, 0)
ep.person(pen, 560, 885, 1.05, (190, 130, 90), (70, 45, 30), (110, 170, 70))
ep.person(pen, 720, 885, 1.0, (200, 140, 100), (120, 70, 35), (150, 190, 80), female=True)
ep.sun(pen, 1560, 300, 210, 0.3)
ep.bird(pen, 1150, 330, 1.6, 1.2, (240, 110, 150))
ep.bird(pen, 1300, 520, 1.3, 2.0, (250, 200, 60))
img = ImageChops.multiply(img.reduce(ep.S), ep.paper_texture())
img = ep.overlay_text(img, "7 DIAS", (560, 230), 250, (255, 214, 64), 1, ep.F_TITLE, 16, ep.INK)
img = ep.overlay_text(img, "A CRIAÇÃO", (560, 420), 130, ep.WHITE, 1, ep.F_TITLE, 12, ep.INK)
d = ImageDraw.Draw(img)
d.rounded_rectangle([40, 960, 520, 1040], 24, fill=ep.PAPER, outline=ep.INK, width=5)
d.text((280, 1000), "Bíblia em Traços", font=ep.font(ep.F_BOLD, 46), fill=ep.INK, anchor="mm")
img.resize((1280, 720), Image.LANCZOS).save(out)
print("Miniatura:", out)
