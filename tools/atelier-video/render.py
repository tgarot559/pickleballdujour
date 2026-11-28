"""Séance vidéo Pickleball du Jour : terrain animé, geste de raquette, voix off, sous-titres.
Usage : python3 render.py [--frames]   (--frames : quelques images clés seulement)"""
import math, os, subprocess, sys, json, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, S = 1280, 720, 30, 2
ROOT = os.path.dirname(os.path.abspath(__file__))
F = lambda name, size: ImageFont.truetype(os.path.join(ROOT, "fonts", name), size * S)
COURT, DEEP, KIT, GRASS, BALL, INK = (31, 95, 191), (14, 58, 120), (47, 116, 214), (42, 138, 87), (214, 240, 63), (15, 28, 46)
WHITE, RED, SOFT = (255, 255, 255), (230, 70, 60), (219, 230, 255)

SCENES = [
 dict(id="intro", step="", text="Bonjour, et bienvenue dans votre séance. Aujourd'hui, on travaille un coup qui change tout en double : le troisième coup amorti, qu'on appelle le drop. Comptez vingt minutes, un partenaire et une dizaine de balles."),
 dict(id="principe", step="Le principe", text="Rappel rapide. Vous servez, l'adversaire retourne, puis monte tout de suite à la cuisine. Si vous frappez fort, il vous attend au filet. Le drop, c'est une balle douce, qui retombe dans sa cuisine. Bien placée, elle l'oblige à jouer vers le haut, sans pouvoir attaquer. Et vous, pendant ce temps, vous avancez."),
 dict(id="geste", step="Le geste", text="Le geste, maintenant. Raquette basse, poignet ferme, et un mouvement de bas en haut, comme si vous lanciez la balle à la main. On ne frappe pas, on pousse. La balle monte doucement, passe le filet, et redescend dans la cuisine."),
 dict(id="ex1", step="Exercice 1 sur 2", text="Premier exercice. Placez-vous sur la ligne de fond. Votre partenaire, à la cuisine, vous envoie la balle. Jouez dix drops, et comptez ceux qui tombent dans la cuisine. Objectif : six sur dix. Pas de vitesse, juste de la régularité."),
 dict(id="ex2", step="Exercice 2 sur 2", text="Deuxième exercice. Même chose, mais après chaque drop, avancez de trois pas vers le filet, puis arrêtez-vous, raquette devant vous. Vous apprenez à monter au bon moment, sans vous faire surprendre. Faites trois séries de dix."),
 dict(id="recap", step="À retenir", text="À retenir : balle douce, geste de bas en haut, et on avance après le drop. Notez votre score aujourd'hui, et refaites l'exercice la semaine prochaine. Votre prochaine séance : le dink. À bientôt sur Pickleball du Jour."),
]
LEAD, TAIL = 0.5, 1.0


# ---------- helpers ----------
def ease(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)
def seg(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= b)
def lerp(a, b, t): return a + (b - a) * t


class Pen:
    def __init__(self, img): self.d = ImageDraw.Draw(img, "RGBA")
    def rect(self, x, y, w, h, fill=None, outline=None, width=1, r=0):
        self.d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=r * S, fill=fill, outline=outline, width=int(width * S))
    def circle(self, x, y, r, fill=None, outline=None, width=1):
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=fill, outline=outline, width=int(width * S))
    def ellipse(self, x, y, rx, ry, fill): self.d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S], fill=fill)
    def line(self, pts, fill, width=2): self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint="curve")
    def poly(self, pts, fill): self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
    def text(self, x, y, s, font, fill=WHITE, anchor="la"): self.d.text((x * S, y * S), s, font=font, fill=fill, anchor=anchor)
    def tw(self, s, font): return self.d.textlength(s, font=font) / S


FT = {"h1": F("Archivo-800.ttf", 54), "h2": F("Archivo-800.ttf", 30), "lab": F("Inter-600.ttf", 20), "sub": F("Inter-600.ttf", 30),
      "small": F("Inter-600.ttf", 17), "body": F("Inter-400.ttf", 24), "big": F("Archivo-800.ttf", 40), "chip": F("Inter-600.ttf", 22)}


def header(p, step):
    p.rect(0, 0, W, 64, fill=WHITE)
    p.rect(24, 14, 36, 36, fill=COURT, r=9)
    p.circle(42, 34, 9, fill=BALL)
    p.rect(30, 38, 24, 5, fill=WHITE, r=2)
    p.text(72, 20, "Pickleball", FT["chip"], INK)
    p.text(72 + p.tw("Pickleball ", FT["chip"]), 20, "du Jour", FT["chip"], COURT)
    p.text(W - 24, 21, "Séance 1 · Le drop" + (f"  ·  {step}" if step else ""), FT["small"], (85, 101, 124), anchor="ra")


def subtitle(p, text):
    if not text: return
    font = FT["sub"]; words = text.split(); lines = [""]
    for w in words:
        t = (lines[-1] + " " + w).strip()
        if p.tw(t, font) > 1080 and lines[-1]: lines.append(w)
        else: lines[-1] = t
    lh = 42; bh = lh * len(lines) + 24; y0 = H - 22 - bh
    wmax = max(p.tw(l, font) for l in lines)
    p.rect((W - wmax) / 2 - 22, y0, wmax + 44, bh, fill=(10, 20, 40, 205), r=14)
    for i, l in enumerate(lines):
        p.text(W / 2, y0 + 12 + i * lh, l, font, WHITE, anchor="ma")


def chunks(text):
    import re
    parts = re.split(r"(?<=[.!?:])\s+", text)
    out = []
    for s in parts:
        while len(s) > 84:
            cut = s.rfind(",", 0, 84)
            cut = cut + 1 if cut > 30 else s.rfind(" ", 0, 84)
            out.append(s[:cut].strip()); s = s[cut:].strip()
        if s: out.append(s)
    return out


# ---------- court (top view) ----------
CX, CY, M = 64, 116, 60          # court origin and px per metre
CL, CWD, NET, K1, K2 = 13.41, 6.10, 6.705, 4.575, 8.835
def P(x, y): return CX + x * M, CY + y * M


def court(p, glow=0.0, label_kitchen=False):
    p.rect(CX - 46, CY - 28, CL * M + 92, CWD * M + 56, fill=GRASS, r=18)
    p.rect(CX, CY, CL * M, CWD * M, fill=COURT)
    for a, b in ((K1, NET), (NET, K2)):
        p.rect(CX + a * M, CY, (b - a) * M, CWD * M, fill=KIT)
    if glow > 0:
        p.rect(CX + NET * M, CY, (K2 - NET) * M, CWD * M, fill=BALL + (int(110 * glow),))
    lw = 3
    p.rect(CX, CY, CL * M, CWD * M, outline=WHITE, width=lw)
    for x in (K1, K2): p.line([P(x, 0), P(x, CWD)], WHITE, lw)
    p.line([P(0, CWD / 2), P(K1, CWD / 2)], WHITE, lw); p.line([P(K2, CWD / 2), P(CL, CWD / 2)], WHITE, lw)
    p.line([(CX + NET * M, CY - 14), (CX + NET * M, CY + CWD * M + 14)], (235, 240, 248), 6)
    if label_kitchen:
        for a in ((NET + K2) / 2, (K1 + NET) / 2):
            x, y = P(a, CWD + 0.22); p.text(x, y, "cuisine", FT["small"], WHITE, "mm")


def player(p, x, y, me=True, label=None):
    px, py = P(x, y)
    p.ellipse(px, py + 14, 15, 6, (0, 0, 0, 60))
    p.circle(px, py, 15, fill=BALL if me else WHITE, outline=INK, width=3)
    if label:
        w = p.tw(label, FT["small"]) + 16
        p.rect(px - w / 2, py - 46, w, 24, fill=(10, 20, 40, 200), r=12)
        p.text(px, py - 34, label, FT["small"], WHITE, "mm")


def ball_at(p, x0, y0, x1, y1, t, hmax, trail=True, color=BALL):
    def pos(u):
        gx, gy = P(lerp(x0, x1, u), lerp(y0, y1, u)); return gx, gy, 4 * hmax * u * (1 - u)
    if trail:
        n = 14
        for i in range(n):
            u = t * i / n
            gx, gy, h = pos(u)
            p.circle(gx, gy - h, 2.2, fill=color + (150,))
    gx, gy, h = pos(t)
    p.ellipse(gx, gy + 2, 7, 3, (0, 0, 0, 70))
    p.circle(gx, gy - h, 8, fill=color, outline=INK, width=2)


def bounce_mark(p, x, y, good=True, a=1.0):
    px, py = P(x, y)
    c = (BALL if good else RED) + (int(255 * a),)
    p.circle(px, py, 11, outline=c, width=3)


def check(p, x, y, size=26, a=1.0, bg=BALL):
    p.rect(x, y, size, size, fill=bg + (int(255 * a),), r=size * 0.28)
    p.line([(x + size * 0.24, y + size * 0.52), (x + size * 0.43, y + size * 0.7), (x + size * 0.78, y + size * 0.3)], INK + (int(255 * a),), size * 0.13)


PX = 952
def panel(p, title, items, u, extra=None):
    p.text(PX, 104, title, FT["h2"], INK)
    y = 160
    for s, st in items:
        a = seg(u, st, st + 0.03)
        if a > 0:
            check(p, PX, y, 26, a)
            words = s.split(); lines = [""]
            for w in words:
                t2 = (lines[-1] + " " + w).strip()
                if p.tw(t2, FT["lab"]) > 266 and lines[-1]: lines.append(w)
                else: lines[-1] = t2
            for k, l in enumerate(lines):
                p.text(PX + 38, y + 1 + k * 26, l, FT["lab"], INK + (int(255 * a),))
            y += 26 * len(lines) + 18
        else:
            y += 44


def tag(p, x, y, s, a=1.0, color=WHITE, bg=(10, 20, 40)):
    if a <= 0: return
    w = p.tw(s, FT["lab"]) + 28
    p.rect(x - w / 2, y - 18, w, 36, fill=bg + (int(220 * a),), r=18)
    p.text(x, y, s, FT["lab"], color + (int(255 * a),), "mm")


# ---------- scenes ----------
def sc_intro(p, t, D):
    p.rect(0, 0, W, H, fill=COURT)
    # court lines in the background
    for i in range(6):
        p.line([(0, 140 + i * 90), (W, 140 + i * 90)], (255, 255, 255, 18), 2)
    a = seg(t, 0.2, 1.0)
    p.text(96, 170 + 20 * (1 - a), "SÉANCE 1  ·  PROFIL INITIÉ", FT["chip"], BALL + (int(255 * a),))
    b = seg(t, 0.6, 1.4)
    p.text(96, 220 + 20 * (1 - b), "Le troisième coup", FT["h1"], WHITE + (int(255 * b),))
    p.text(96, 290 + 20 * (1 - b), "amorti : le drop", FT["h1"], WHITE + (int(255 * b),))
    c = seg(t, 1.4, 2.2)
    x = 96
    for s in ("20 minutes", "1 partenaire", "10 balles", "2 exercices"):
        w = p.tw(s, FT["chip"]) + 32
        p.rect(x, 390, w, 44, fill=(255, 255, 255, int(40 * c)), outline=(255, 255, 255, int(120 * c)), width=2, r=22)
        p.text(x + w / 2, 412, s, FT["chip"], WHITE + (int(255 * c),), "mm"); x += w + 12
    # ball arcing over a net on the right
    nx, gy = 1010, 470
    p.line([(nx, gy - 70), (nx, gy)], WHITE, 6); p.line([(840, gy), (1190, gy)], (255, 255, 255, 120), 3)
    u = (t * 0.55) % 1
    bx = lerp(860, 1150, u); by = gy - 10 - 4 * 170 * u * (1 - u)
    p.ellipse(bx, gy + 4, 10, 4, (0, 0, 0, 60)); p.circle(bx, by, 16, fill=BALL, outline=INK, width=3)


def sc_principe(p, t, D):
    u = t / D
    court(p, glow=0, label_kitchen=True)
    me1, me2 = [0.4, 1.6], [0.4, 4.5]
    op1, op2 = [12.9, 4.5], [12.9, 1.6]
    # opponents move up after return
    k = seg(u, 0.22, 0.34)
    op1 = [lerp(12.9, 9.2, k), 4.5]; op2 = [lerp(12.9, 9.2, k), 1.6]
    # we advance at the end
    adv = seg(u, 0.80, 0.95)
    me1 = [lerp(0.4, 4.2, adv), 1.6]; me2 = [lerp(0.4, 4.2, adv), 4.5]
    glow = seg(u, 0.56, 0.62) * (1 - seg(u, 0.98, 1.0))
    if glow: court(p, glow=0.5 + 0.5 * math.sin(t * 6) * 0.5, label_kitchen=True)
    if u < 0.12: ball_at(p, 0.4, 1.6, 12.4, 4.2, seg(u, 0.02, 0.12), 60)
    elif u < 0.24: ball_at(p, 12.6, 4.4, 1.2, 1.9, seg(u, 0.13, 0.24), 70)
    elif u < 0.36: pass
    elif u < 0.52:
        v = seg(u, 0.38, 0.47)
        if v > 0: ball_at(p, 1.0, 1.7, 9.0, 1.7, v, 14, color=RED)
        if u > 0.47:
            tag(p, *P(10.6, -0.05), "Trop facile pour lui", seg(u, 0.47, 0.5), WHITE, (160, 40, 30))
    elif u < 0.80:
        v = seg(u, 0.56, 0.72)
        ball_at(p, 1.0, 1.7, 7.7, 2.2, v, 150)
        if v >= 1: bounce_mark(p, 7.7, 2.2, True)

    else:
        bounce_mark(p, 7.7, 2.2, True, 1 - adv)
        tag(p, *P(2.4, -0.05), "Vous avancez", seg(u, 0.80, 0.84))
        for yy in (1.6, 4.5):
            a0, a1 = P(lerp(0.4, 4.2, adv) + 0.4, yy), P(4.4, yy)
            if adv < 0.98: p.line([a0, a1], (214, 240, 63, 160), 3)
    player(p, *op1, False); player(p, *op2, False)
    player(p, *me1, True, "Vous" if u < 0.4 else None); player(p, *me2, True, "Partenaire" if u < 0.4 else None)
    panel(p, "Le principe", [("Vous servez", 0.01), ("Il retourne et monte à la cuisine", 0.14), ("Frappe forte : il vous attend", 0.40), ("Le drop retombe dans sa cuisine", 0.58), ("Il doit jouer vers le haut", 0.68), ("Vous avancez", 0.80)], u)


GY, NX = 540, 700      # side view ground and net
def sc_geste(p, t, D):
    u = t / D
    p.rect(0, 64, W, H - 64, fill=(236, 243, 252))
    p.rect(0, GY, W, H - GY, fill=COURT)
    p.rect(NX, GY, 160, H - GY, fill=KIT)
    p.line([(NX, GY), (NX, GY - 70)], INK, 6); p.line([(NX - 2, GY - 70), (NX + 2, GY - 70)], INK, 4)
    p.text(NX + 80, GY + 30, "cuisine", FT["small"], WHITE, "mm")
    p.text(NX, GY - 92, "filet", FT["small"], (85, 101, 124), "mm")
    # player (simple silhouette), shoulder pivot
    sx, sy = 300, 360
    p.circle(sx - 20, 270, 26, fill=(255, 214, 170), outline=INK, width=3)
    p.line([(sx - 20, 300), (sx - 20, 430)], INK, 10)
    p.line([(sx - 20, 430), (sx - 50, GY)], INK, 9); p.line([(sx - 20, 430), (sx + 20, GY)], INK, 9)
    # swing cycle (2.6 s), contact at phase 0.45
    cyc = 2.8; ph = (t % cyc) / cyc
    LO, HI, REST = -32, 45, -10
    if ph < 0.25: ang = lerp(REST, LO, ease(ph / 0.25))            # back, low
    elif ph < 0.6: ang = lerp(LO, HI, ease((ph - 0.25) / 0.35))    # low to high
    else: ang = lerp(HI, REST, ease((ph - 0.6) / 0.4))             # recover
    def center(angle):
        a = math.radians(angle); hx, hy = sx + 110 * math.cos(a), sy + 60 - 110 * math.sin(a)
        return hx + math.cos(a) * 52, hy - math.sin(a) * 52
    ccx, ccy = center(lerp(LO, HI, ease(0.2 / 0.35)))
    def paddle(angle, alpha=255):
        a = math.radians(angle)
        ex, ey = sx + 70 * math.sin(a + 1.2) * 0.6, sy + 60
        hx, hy = sx + 110 * math.cos(a), sy + 110 * math.sin(a) * -1 + 60
        p.line([(sx - 20, 330), (ex, ey), (hx, hy)], (255, 214, 170, alpha), 9)
        # paddle face along the angle
        dx, dy = math.cos(a), -math.sin(a)
        nx_, ny_ = -dy, dx
        cx, cy = hx + dx * 52, hy + dy * 52
        pts = [(cx + dx * 46 + nx_ * 30, cy + dy * 46 + ny_ * 30), (cx + dx * 46 - nx_ * 30, cy + dy * 46 - ny_ * 30),
               (cx - dx * 46 - nx_ * 30, cy - dy * 46 - ny_ * 30), (cx - dx * 46 + nx_ * 30, cy - dy * 46 + ny_ * 30)]
        p.line([(hx, hy), (hx + dx * 10, hy + dy * 10)], INK + (alpha,), 10)
        p.poly(pts, (31, 95, 191, alpha)); p.line(pts + pts[:1], INK + (alpha,), 3)
        return cx, cy
    for g in (1, 2, 3):   # ghost trail of the swing
        if 0.3 < ph < 0.75:
            ga = max(LO, ang - g * 14)
            paddle(ga, 50)
    cx, cy = paddle(ang)
    # ball: arrives, contact at ph 0.45, then soft arc into the kitchen
    if ph < 0.45:
        v = ph / 0.45
        if v < 0.6:   # incoming ball from the partner, bounces in front of you
            w = v / 0.6; bx = lerp(660, ccx + 70, w); by = lerp(380, GY - 9, w) - 60 * math.sin(math.pi * w)
        else:         # rises after the bounce into the paddle
            w = (v - 0.6) / 0.4; bx = lerp(ccx + 70, ccx + 14, w); by = lerp(GY - 9, ccy, w) - 30 * math.sin(math.pi * w)
    else:
        v = min(1, (ph - 0.45) / 0.45)
        x0, y0, x1 = ccx + 14, ccy, 790
        bx = lerp(x0, x1, v); by = lerp(y0, GY - 9, v) - 210 * 4 * v * (1 - v)
        for i in range(12):
            w = v * i / 12
            p.circle(lerp(x0, x1, w), lerp(y0, GY - 9, w) - 210 * 4 * w * (1 - w), 2.4, fill=(214, 240, 63, 170))
    p.circle(bx, by, 10, fill=BALL, outline=INK, width=2)
    # callouts in order of the narration
    items = [("Raquette basse", 0.08), ("Poignet ferme", 0.20), ("De bas en haut", 0.30), ("On pousse, on ne frappe pas", 0.50), ("Retombe dans la cuisine", 0.70)]
    y = 130
    for s, st in items:
        a = seg(u, st, st + 0.04)
        if a > 0:
            check(p, 900, y - 4, 26, a)
            p.text(938, y - 1, s, FT["lab"], INK + (int(255 * a),))
        y += 44


PATTERN = [1, 1, 0, 1, 1, 1, 0, 1, 1, 1]
def sc_ex1(p, t, D):
    start = 3.2; rep = (D - start - 1.2) / 10
    court(p, glow=0.25, label_kitchen=True)
    me, mate = (0.5, 3.05), (9.1, 3.05)
    n = 0; ball = None
    if t >= start:
        i = min(9, int((t - start) / rep)); v = ((t - start) - i * rep) / rep
        n = sum(PATTERN[:i]); good = PATTERN[i]
        land = (7.8, 2.3 + (i % 3) * 0.8) if good else (9.9, 2.0 + (i % 2) * 2)
        if v < 0.38: ball = (8.9, 3.05, 1.2, 3.0, v / 0.38, 50)
        elif v < 0.88:
            ball = (1.0, 3.0, land[0], land[1], (v - 0.38) / 0.5, 140)
        else:
            bounce_mark(p, *land, bool(good)); ball = None
            n += good
        if t - start > 10 * rep: n = sum(PATTERN)
    for (dx, dy) in [] : pass
    player(p, *me, True, "Vous"); player(p, *mate, False, "Partenaire")
    if ball: ball_at(p, *ball)
    # scoreboard
    u = t / D
    panel(p, "Exercice 1", [("Sur la ligne de fond", 0.08), ("Le partenaire envoie depuis la cuisine", 0.16), ("10 drops, comptez les bons", 0.30)], u)
    p.rect(PX, 420, 300, 104, fill=WHITE, outline=(225, 231, 240), width=2, r=16)
    p.text(PX + 20, 432, "Dans la cuisine", FT["small"], (85, 101, 124))
    p.text(PX + 20, 456, f"{n} / 10", FT["big"], COURT)
    p.text(PX + 280, 476, "objectif 6", FT["lab"], (85, 101, 124), "ra")


def sc_ex2(p, t, D):
    start = 3.0; rep = (D - start - 1.0) / 3
    court(p, glow=0.2, label_kitchen=True)
    mate = (9.1, 3.05); mx = 0.5; ball = None
    if t >= start:
        i = min(2, int((t - start) / rep)); v = ((t - start) - i * rep) / rep
        if v < 0.25: ball = (8.9, 3.05, 1.2, 3.0, v / 0.25, 50)
        elif v < 0.55: ball = (1.0, 3.0, 7.8, 2.6 + i * 0.6, (v - 0.25) / 0.3, 140)
        if v > 0.55: bounce_mark(p, 7.8, 2.6 + i * 0.6, True, 1 - seg(v, 0.85, 1))
        mx = lerp(0.5, 2.6, seg(v, 0.45, 0.75)) if v < 0.92 else lerp(2.6, 0.5, seg(v, 0.92, 1.0))
        if 0.45 < v < 0.92:
            x0, y0 = P(0.5, 3.6); x1, y1 = P(2.6, 3.6)
            p.line([(x0, y0 + 26), (x1, y1 + 26)], BALL, 4)
            p.poly([(x1 + 10, y1 + 26), (x1 - 4, y1 + 18), (x1 - 4, y1 + 34)], BALL)
            p.text((x0 + x1) / 2, y0 + 50, "3 pas", FT["lab"], WHITE, "mm")
        if 0.75 < v < 0.92: tag(p, *P(2.6, 1.6), "Stop, raquette devant", 1)
    player(p, mx, 3.05, True, "Vous"); player(p, *mate, False, "Partenaire")
    if ball: ball_at(p, *ball)
    u = t / D
    panel(p, "Exercice 2", [("Un drop", 0.10), ("Trois pas vers le filet", 0.20), ("Stop, raquette devant vous", 0.32), ("3 séries de 10", 0.62)], u)


def sc_recap(p, t, D):
    p.rect(0, 0, W, H, fill=DEEP)
    p.text(96, 120, "À retenir", FT["h1"], BALL)
    for i, s in enumerate(["Une balle douce, qui retombe dans la cuisine", "Un geste de bas en haut : on pousse", "Après le drop, on avance"]):
        a = seg(t, 1.0 + i * 1.6, 1.4 + i * 1.6)
        y = 220 + i * 70
        check(p, 100, y, 36, a)
        p.text(152, y + 4, s, FT["h2"], WHITE + (int(255 * a),))
    b = seg(t, D * 0.55, D * 0.62)
    p.rect(96, 450, 560, 64, fill=(255, 255, 255, int(30 * b)), r=16)
    p.text(120, 482, "Prochaine séance : le dink", FT["chip"], WHITE + (int(255 * b),), "lm")
    p.text(96, 548, "pickleballdujour.fr/progresser", FT["chip"], SOFT + (int(255 * b),))


DRAW = {"intro": sc_intro, "principe": sc_principe, "geste": sc_geste, "ex1": sc_ex1, "ex2": sc_ex2, "recap": sc_recap}


def frame(sc, t, D, subs):
    img = Image.new("RGB", (W * S, H * S), (236, 243, 252))
    p = Pen(img)
    DRAW[sc["id"]](p, t, D)
    if sc["id"] not in ("intro", "recap") or True:
        header(p, sc["step"]) if sc["id"] != "intro" else None
    cur = next((s for (a, b, s) in subs if a <= t < b), "")
    subtitle(p, cur)
    return img.resize((W, H), Image.LANCZOS)


def build_audio():
    meta = []
    for sc in SCENES:
        wav = os.path.join(ROOT, "audio", sc["id"] + ".wav")
        if not os.path.exists(wav):
            os.makedirs(os.path.dirname(wav), exist_ok=True)
            subprocess.run([sys.executable, os.path.join(ROOT, "tts.py"), sc["text"], wav], check=True, capture_output=True)
        with wave.open(wav) as w:
            dur = w.getnframes() / w.getframerate()
        D = LEAD + dur + TAIL
        D = math.ceil(D * FPS) / FPS
        parts = chunks(sc["text"]); total = sum(len(x) for x in parts); t0 = LEAD; subs = []
        for x in parts:
            d = dur * len(x) / total; subs.append((t0, t0 + d, x)); t0 += d
        meta.append(dict(sc=sc, D=D, dur=dur, subs=subs, wav=wav))
    return meta


def main():
    meta = build_audio()
    out = os.path.join(ROOT, "out"); os.makedirs(out, exist_ok=True)
    if "--frames" in sys.argv:
        for m in meta:
            for f in (0.35, 0.6, 0.85):
                frame(m["sc"], m["D"] * f, m["D"], m["subs"]).save(os.path.join(out, f"k_{m['sc']['id']}_{int(f*100)}.png"))
        print("frames ok"); return
    files = []
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    for m in meta:
        if only and m["sc"]["id"] != only:
            files.append(os.path.join(out, m["sc"]["id"] + ".mp4")); continue
        tmp = os.path.join(out, m["sc"]["id"] + ".tmp.mp4"); fin = os.path.join(out, m["sc"]["id"] + ".mp4")
        n = int(round(m["D"] * FPS))
        pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for k in range(n):
            pr.stdin.write(frame(m["sc"], k / FPS, m["D"], m["subs"]).tobytes())
        pr.stdin.close()
        if pr.wait() == 0: os.replace(tmp, fin)
        files.append(fin); print(m["sc"]["id"], round(m["D"], 2))
    with open(os.path.join(out, "list.txt"), "w") as f:
        f.write("".join(f"file '{x}'\n" for x in files))
    # audio track
    rate = None; chunks_ = []
    for m in meta:
        with wave.open(m["wav"]) as w:
            rate = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        lead = np.zeros(int(LEAD * rate), np.int16)
        tail = np.zeros(int(round(m["D"] * rate)) - len(lead) - len(a), np.int16)
        chunks_ += [lead, a, tail]
    with wave.open(os.path.join(out, "voice.wav"), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(np.concatenate(chunks_).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(out, "list.txt"), "-c", "copy", os.path.join(out, "video.mp4")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(out, "video.mp4"), "-i", os.path.join(out, "voice.wav"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", os.path.join(out, "seance-1-le-drop.mp4")], check=True)
    print("done")


if __name__ == "__main__":
    main()
