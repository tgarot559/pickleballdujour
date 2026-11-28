"""Situation diagrams for each daily tip: original SVG, portrait court, mobile first.

Court in metres: x across 0..6.10, y along 0..13.41.
Top half = opponents, bottom half = you. Net at y=6.705, kitchen lines at 4.575 and 8.835.
"""

S = 34          # px per metre
OX, OY = 46, 62  # court origin in the SVG
CW, CL = 6.10, 13.41
NET, KT, KB = 6.705, 4.575, 8.835
W = int(CW * S + 2 * OX)
H = int(CL * S + 2 * OY)
FONT = "font-family:Inter,system-ui,sans-serif"
LIME, BLUE, DEEP, KIT = "#d6f03f", "#1f5fbf", "#0e3a78", "#2f74d6"


def X(x): return OX + x * S
def Y(y): return OY + y * S


def tr(v, lang):
    return v if isinstance(v, str) else (v[0] if lang == "fr" else v[1])


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def court():
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" rx="18" fill="#2a8a57"/>',
         f'<rect x="{X(0)}" y="{Y(0)}" width="{CW*S}" height="{CL*S}" fill="{BLUE}"/>',
         f'<rect x="{X(0)}" y="{Y(KT)}" width="{CW*S}" height="{(KB-KT)*S}" fill="{KIT}"/>']
    st = 'stroke="#fff" stroke-width="3" fill="none"'
    o.append(f'<rect x="{X(0)}" y="{Y(0)}" width="{CW*S}" height="{CL*S}" {st}/>')
    for y in (KT, KB):
        o.append(f'<line x1="{X(0)}" y1="{Y(y)}" x2="{X(CW)}" y2="{Y(y)}" {st}/>')
    o.append(f'<line x1="{X(CW/2)}" y1="{Y(0)}" x2="{X(CW/2)}" y2="{Y(KT)}" {st}/>')
    o.append(f'<line x1="{X(CW/2)}" y1="{Y(KB)}" x2="{X(CW/2)}" y2="{Y(CL)}" {st}/>')
    o.append(f'<line x1="{X(-0.5)}" y1="{Y(NET)}" x2="{X(CW+0.5)}" y2="{Y(NET)}" stroke="#0f1c2e" stroke-width="5" stroke-dasharray="2 4"/>')
    return o


def player(x, y, label, team, lang):
    fill, ink = (LIME, "#0f1c2e") if team == "us" else ("#ffffff", DEEP)
    lab = tr(label, lang)
    o = [f'<circle cx="{X(x)}" cy="{Y(y)}" r="12" fill="{fill}" stroke="#0f1c2e" stroke-width="2.5"/>']
    ty = Y(y) + (27 if y > NET else -18)
    if lab:
        o.append(f'<text x="{X(x)}" y="{ty}" text-anchor="middle" font-size="11.5" font-weight="700" fill="#fff" style="paint-order:stroke;stroke:#0f1c2e;stroke-width:3.5px">{esc(lab)}</text>')
    return o


def arrow(x1, y1, x2, y2, kind="ball", bend=0.0, color=None):
    """kind: ball (lime dashed arc), fast (lime solid straight), move (white), bad (red dashed)."""
    ax, ay, bx, by = X(x1), Y(y1), X(x2), Y(y2)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    dx, dy = bx - ax, by - ay
    cx, cy = mx - dy * bend, my + dx * bend
    col = color or {"ball": LIME, "fast": LIME, "move": "#ffffff", "bad": "#ff5a5a"}[kind]
    dash = {"ball": 'stroke-dasharray="7 6"', "bad": 'stroke-dasharray="7 6"', "fast": "", "move": 'stroke-dasharray="2 5"'}[kind]
    wdt = 4 if kind in ("ball", "fast", "bad") else 3
    mid = f"m{abs(hash((x1, y1, x2, y2, kind))) % 99999}"
    return [f'<defs><marker id="{mid}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{col}"/></marker></defs>',
            f'<path d="M{ax:.1f} {ay:.1f} Q{cx:.1f} {cy:.1f} {bx:.1f} {by:.1f}" fill="none" stroke="{col}" stroke-width="{wdt}" stroke-linecap="round" {dash} marker-end="url(#{mid})"/>']


def bounce(x, y, color=LIME):
    return [f'<circle cx="{X(x)}" cy="{Y(y)}" r="7" fill="{color}" stroke="#0f1c2e" stroke-width="2"/>']


def zone(x1, y1, x2, y2, color=LIME, label=None, lang="fr", op=0.35, at=None):
    o = [f'<rect x="{X(x1)}" y="{Y(y1)}" width="{(x2-x1)*S}" height="{(y2-y1)*S}" fill="{color}" fill-opacity="{op}" stroke="{color}" stroke-width="2" stroke-dasharray="5 4"/>']
    if label:
        lx, ly = at if at else ((x1 + x2) / 2, (y1 + y2) / 2)
        o.append(f'<text x="{X(lx)}" y="{Y(ly)+4}" text-anchor="middle" font-size="11.5" font-weight="800" fill="#fff" style="paint-order:stroke;stroke:#0f1c2e;stroke-width:3.5px">{esc(tr(label, lang))}</text>')
    return o


def bubble(x, y, text, lang, color="#ffffff", ink="#0f1c2e"):
    t = tr(text, lang)
    w = 8 + 7.2 * len(t)
    bx, by = X(x) - w / 2, Y(y) - 15
    return [f'<rect x="{bx:.1f}" y="{by:.1f}" width="{w:.1f}" height="26" rx="13" fill="{color}" stroke="#0f1c2e" stroke-width="2"/>',
            f'<text x="{X(x):.1f}" y="{Y(y)+3:.1f}" text-anchor="middle" font-size="12.5" font-weight="800" fill="{ink}">{esc(t)}</text>']


def label(x, y, text, lang, size=12, color="#fff"):
    return [f'<text x="{X(x):.1f}" y="{Y(y):.1f}" text-anchor="middle" font-size="{size}" font-weight="800" fill="{color}" style="paint-order:stroke;stroke:#0f1c2e;stroke-width:3.5px">{esc(tr(text, lang))}</text>']


def cross(x, y, color="#ff5a5a"):
    a, b = X(x), Y(y)
    return [f'<path d="M{a-8} {b-8}L{a+8} {b+8}M{a+8} {b-8}L{a-8} {b+8}" stroke="{color}" stroke-width="4.5" stroke-linecap="round"/>']


YOU, PART, OPP = ("Vous", "You"), ("Partenaire", "Partner"), ("Adversaire", "Opponent")


def kitchen4(lang, labels=True):
    o = []
    o += player(1.5, KT - 0.4, OPP if labels else "", "them", lang)
    o += player(4.6, KT - 0.4, "", "them", lang)
    o += player(1.5, KB + 0.4, YOU if labels else "", "us", lang)
    o += player(4.6, KB + 0.4, PART if labels else "", "us", lang)
    return o


def scene(i, lang):
    """Return the drawing for tip number i (0-based, same order in FR and EN)."""
    o = []
    if i == 0:  # service profond
        o += zone(0, 0, CW / 2, 2.2, LIME, ("Zone visée", "Target"), lang, at=(1.5, 1.85))
        o += player(1.5, -0.6, OPP, "them", lang)
        o += player(4.6, CL + 0.6, YOU, "us", lang)
        o += arrow(4.6, CL + 0.3, 2.2, 0.8, "ball", 0.18)
        o += bounce(2.2, 0.8)
        o += arrow(4.6, CL - 1, 2.2, NET + 1.6, "bad", -0.1)
        o += label(3.6, NET + 2.4, ("Court = attaqué", "Short = attacked"), lang, 11, "#ffd0d0")
    elif i == 1:  # retour puis monter
        o += player(4.6, -0.6, OPP, "them", lang)
        o += player(1.5, CL + 0.6, YOU, "us", lang)
        o += arrow(1.5, CL + 0.2, 4.4, 1.2, "ball", 0.15)
        o += bounce(4.4, 1.2)
        o += arrow(1.9, CL - 0.2, 1.9, KB + 0.6, "move")
        o += bubble(3.6, KB + 2.2, ("Montez !", "Move up!"), lang, LIME)
    elif i == 2:  # troisième coup drop
        o += zone(0, KT, CW, NET, LIME, ("Cuisine adverse", "Their kitchen"), lang, 0.3, at=(1.4, 6.2))
        o += player(1.5, KT - 0.4, OPP, "them", lang)
        o += player(4.6, KT - 0.4, "", "them", lang)
        o += player(1.5, CL + 0.6, YOU, "us", lang)
        o += player(4.6, CL + 0.6, PART, "us", lang)
        o += arrow(4.6, CL + 0.2, 3.6, 5.5, "ball", 0.22)
        o += bounce(3.6, 5.5)
        o += arrow(1.2, CL - 0.3, 1.2, KB + 1.2, "move")
        o += arrow(4.9, CL - 0.3, 4.9, KB + 1.2, "move")
    elif i == 3:  # raquette haute
        o += kitchen4(lang)
        o += arrow(1.7, KB - 0.1, 4.3, KT + 0.1, "fast", 0.02)
        o += arrow(4.3, KT + 0.3, 1.9, KB - 0.3, "fast", 0.02)
        o += bubble(CW / 2, NET + 0.1, ("Raquette devant la poitrine", "Paddle up, chest high"), lang, "#fff")
    elif i == 4:  # patience dink
        o += kitchen4(lang)
        pts = [(1.6, KB - 0.2), (1.9, KT + 0.9), (2.6, KB - 0.9), (3.4, KT + 0.8), (4.2, KB - 0.8)]
        for a, b in zip(pts, pts[1:]):
            o += arrow(a[0], a[1], b[0], b[1], "ball", 0.25 if a[1] > NET else -0.25)
        o += bubble(CW / 2, CL - 1.2, ("Attendez la balle haute", "Wait for the high ball"), lang, LIME)
    elif i == 5:  # communiquer
        o += player(3.05, KT - 0.4, OPP, "them", lang)
        o += player(1.6, KB + 0.4, YOU, "us", lang)
        o += player(4.5, KB + 0.4, PART, "us", lang)
        o += arrow(3.05, KT, 3.05, KB + 1.2, "fast")
        o += bounce(3.05, KB + 1.2)
        o += bubble(1.3, KB + 2.6, ("« Moi ! »", "“Mine!”"), lang, LIME)
        o += bubble(4.8, KB + 2.6, ("« Toi ! »", "“Yours!”"), lang, "#fff")
    elif i == 6:  # pieds cuisine
        o += zone(0, NET, CW, KB, "#ff5a5a", ("Cuisine", "Kitchen"), lang, 0.28, at=(1.2, 7.3))
        o += player(3.0, KB + 0.4, YOU, "us", lang)
        o += arrow(3.6, KT + 0.2, 3.3, KB + 0.1, "fast")
        o += arrow(3.0, KB + 0.1, 4.2, KB - 1.2, "bad")
        o += cross(4.5, KB - 1.5)
        o += label(CW / 2, KB + 2.8, ("Volée puis pied dedans = faute", "Volley then step in = fault"), lang, 11.5, "#ffd0d0")
    elif i == 7:  # viser les pieds
        o += kitchen4(lang)
        o += zone(1.0, KT - 0.3, 2.0, KT + 0.5, LIME, None, lang, 0.5)
        o += arrow(1.6, KB, 1.5, KT + 0.2, "fast", 0.04)
        o += label(1.5, KT + 1.4, ("Dans les pieds", "At the feet"), lang, 12, LIME)
    elif i == 8:  # échauffement
        o += player(3.05, KB + 0.4, YOU, "us", lang)
        o += arrow(3.05, KB + 1.4, 0.6, KB + 1.4, "move")
        o += arrow(3.05, KB + 1.4, 5.5, KB + 1.4, "move")
        o += bubble(CW / 2, CL - 1.4, ("Pas chassés · fentes · épaules", "Shuffles · lunges · shoulders"), lang, LIME)
        o += bubble(CW / 2, 2.6, ("5 minutes", "5 minutes"), lang, "#fff")
    elif i == 9:  # annoncer le score
        o += player(1.5, -0.6, OPP, "them", lang)
        o += player(4.6, CL + 0.6, YOU, "us", lang)
        o += bubble(CW / 2, NET + 3.4, ("« 4 – 2 – 1 »", "“4 – 2 – 1”"), lang, LIME)
        o += label(CW / 2, NET + 4.6, ("nous · eux · serveur", "us · them · server"), lang, 11.5)
    elif i == 10:  # revers adverse
        o += kitchen4(lang)
        o += zone(3.4, KT - 0.1, CW, NET, LIME, ("Son revers", "Backhand"), lang, 0.35, at=(4.75, 6.3))
        o += arrow(1.6, KB - 0.1, 4.5, KT + 0.8, "ball", 0.18)
        o += bounce(4.5, KT + 0.8)
    elif i == 11:  # lob
        o += kitchen4(lang)
        o += arrow(1.6, KB, 2.4, 0.8, "ball", 0.28)
        o += bounce(2.4, 0.8)
        o += arrow(4.4, KB, 4.4, KT - 1.4, "bad", -0.25)
        o += cross(4.4, KT - 1.8)
        o += label(4.4, KT - 2.7, ("Trop court = smash", "Too short = smash"), lang, 11, "#ffd0d0")
    elif i == 12:  # reset
        o += player(1.5, KT - 0.4, OPP, "them", lang)
        o += player(4.6, KT - 0.4, "", "them", lang)
        o += player(2.0, KB + 2.6, YOU, "us", lang)
        o += arrow(1.6, KT, 2.1, KB + 2.0, "fast", 0.0, "#ff8a3d")
        o += arrow(2.2, KB + 2.2, 3.0, KT + 1.1, "ball", 0.25)
        o += bounce(3.0, KT + 1.1)
        o += label(CW / 2, CL - 0.5, ("Balle rapide → balle douce", "Fast ball → soft ball"), lang, 11)
    elif i == 15:  # milieu du terrain
        o += zone(0, KB, CW, CL - 1.0, "#ff8a3d", ("Zone de transition", "Transition zone"), lang, 0.35, at=(CW / 2, CL - 1.15))
        o += player(3.05, KB + 2.0, YOU, "us", lang)
        o += arrow(3.05, KB + 1.6, 3.05, KB + 0.5, "move")
        o += player(1.5, KT - 0.4, OPP, "them", lang)
        o += arrow(1.6, KT, 3.4, KB + 2.3, "fast", 0.0, "#ff8a3d")
    elif i == 16:  # bouger ensemble
        o += player(1.5, KT - 0.4, OPP, "them", lang)
        o += player(4.6, KT - 0.4, "", "them", lang)
        o += player(0.9, KB + 0.4, YOU, "us", lang)
        o += player(3.6, KB + 0.4, PART, "us", lang)
        o += [f'<path d="M{X(1.3)} {Y(KB+0.4)} Q{X(2.25)} {Y(KB+1.3)} {X(3.2)} {Y(KB+0.4)}" stroke="#fff" stroke-width="3" fill="none" stroke-dasharray="4 4"/>']
        o += arrow(1.5, KT, 0.6, KB - 0.6, "ball", 0.1)
        o += label(2.25, KB + 2.2, ("Une corde de 3 m", "A 3 m rope"), lang, 12, LIME)
    elif i == 17:  # accélérer la bonne balle
        o += kitchen4(lang)
        o += arrow(1.6, KT + 0.1, 2.2, KB - 0.6, "ball", 0.32, "#ffffff")
        o += label(3.6, KB - 1.1, ("Balle haute", "High ball"), lang, 11.5)
        o += arrow(2.2, KB - 0.5, 4.5, KT - 0.1, "fast", 0.03)
    elif i == 18:  # vent
        for yy in (2.0, 5.0, 8.0, 11.0):
            o += arrow(-0.3, yy, CW + 0.3, yy - 0.6, "move", 0.05)
        o += bubble(CW / 2, NET, ("Vent", "Wind"), lang, "#fff")
        o += player(3.05, CL + 0.6, YOU, "us", lang)
    elif i == 19:  # un point à la fois
        o += player(4.6, CL + 0.6, ("Serveur", "Server"), "us", lang)
        o += player(1.5, -0.6, OPP, "them", lang)
        o += bubble(CW / 2, NET + 3.0, ("Seul le serveur marque", "Only the server scores"), lang, LIME)
        o += bubble(CW / 2, 3.0, ("Point suivant", "Next point"), lang, "#fff")
    elif i == 20:  # erne
        o += zone(0, NET, CW, KB, "#ff5a5a", None, lang, 0.18)
        o += player(1.5, KT - 0.4, OPP, "them", lang)
        o += player(5.4, KB + 0.4, YOU, "us", lang)
        o += arrow(5.6, KB + 0.2, 6.6, NET + 0.8, "move", -0.3)
        o += arrow(1.8, KT, 5.9, NET + 0.6, "ball", -0.06)
        o += label(3.4, CL - 1.2, ("Par l'extérieur de la cuisine", "Around the kitchen, outside"), lang, 11)
    elif i == 22:  # jouer au centre
        o += kitchen4(lang)
        o += arrow(3.05, KB, 3.05, KT - 0.2, "fast")
        o += bubble(CW / 2, KT - 1.6, ("« À toi ? À moi ? »", "“Yours? Mine?”"), lang, "#fff")
    elif i == 23:  # chaussures
        o += player(3.05, KB + 0.6, YOU, "us", lang)
        o += arrow(3.05, KB + 1.6, 0.5, KB + 1.6, "move")
        o += arrow(3.05, KB + 1.6, 5.6, KB + 1.6, "move")
        o += cross(0.4, KB + 2.4, LIME)
        o += cross(5.7, KB + 2.4, LIME)
        o += bubble(CW / 2, CL - 1.0, ("Appuis latéraux et freinages", "Side steps and sudden stops"), lang, LIME)
    elif i == 24:  # simple : retour profond puis monter
        o += zone(3.6, 0, CW, 2.2, LIME, ("Coin revers", "Backhand corner"), lang, at=(4.85, -0.55))
        o += player(1.5, -0.6, ("Serveur", "Server"), "them", lang)
        o += player(4.6, CL + 0.6, YOU, "us", lang)
        o += arrow(4.6, CL + 0.2, 4.8, 0.9, "ball", -0.08)
        o += bounce(4.8, 0.9)
        o += arrow(4.3, CL - 0.3, 3.7, KB + 0.5, "move")
        o += label(1.8, KB + 1.6, ("Décalé côté balle", "Shade to the ball"), lang, 11.5, LIME)
    else:
        return None
    return o


# ---- tips that are not about a court position ---------------------------------

def balls(lang):
    t = (("Intérieur", "Extérieur", "gros trous, souple", "40 petits trous, dure") if lang == "fr"
         else ("Indoor", "Outdoor", "big holes, softer", "40 small holes, harder"))
    o = [f'<rect x="0" y="0" width="{W}" height="300" rx="18" fill="{BLUE}"/>']
    import math
    for cx, col, n, r, name, sub in ((W * 0.28, "#ffb347", 26, 9, t[0], t[2]), (W * 0.72, LIME, 40, 5.5, t[1], t[3])):
        o.append(f'<circle cx="{cx}" cy="130" r="62" fill="{col}" stroke="#0f1c2e" stroke-width="3"/>')
        k = 0
        for ring, cnt in ((0, 1), (24, 8), (46, max(n - 9, 8))):
            for j in range(cnt):
                if k >= n:
                    break
                a = 2 * math.pi * j / cnt
                if ring == 46 and abs(math.sin(a)) > 0.95:
                    continue
                o.append(f'<circle cx="{cx + ring*math.cos(a):.1f}" cy="{130 + ring*0.8*math.sin(a):.1f}" r="{r}" fill="#0f1c2e" fill-opacity=".55"/>')
                k += 1
        o.append(f'<text x="{cx}" y="228" text-anchor="middle" font-size="17" font-weight="800" fill="#fff">{name}</text>')
        o.append(f'<text x="{cx}" y="250" text-anchor="middle" font-size="11" fill="#dbe6ff">{sub}</text>')
    return o, 300


def grip(lang):
    t = ("Prise marteau", "la tranche face à la cible", "coup droit, revers, volée") if lang == "fr" else ("Hammer grip", "edge pointing at the target", "forehand, backhand, volley")
    o = [f'<rect x="0" y="0" width="{W}" height="320" rx="18" fill="{BLUE}"/>',
         # paddle seen from the edge, like a hammer
         f'<rect x="{W/2-9}" y="40" width="18" height="150" rx="9" fill="{LIME}" stroke="#0f1c2e" stroke-width="3"/>',
         f'<rect x="{W/2-11}" y="190" width="22" height="80" rx="8" fill="#0f1c2e"/>',
         # hand
         f'<path d="M{W/2-34} 200 q-6 30 6 58 h56 q12-28 6-58 q-8-12-20-4 q-6-12-16-4 q-8-10-18 0 q-10-6-14 8z" fill="#f2c9a0" stroke="#0f1c2e" stroke-width="2.5"/>',
         f'<path d="M{W/2-8} 202 l8 18 l8 -18" stroke="#0f1c2e" stroke-width="3" fill="none"/>',
         f'<text x="{W/2}" y="26" text-anchor="middle" font-size="17" font-weight="800" fill="#fff">{t[0]}</text>',
         f'<text x="{W/2}" y="292" text-anchor="middle" font-size="12" fill="#fff">{t[1]}</text>',
         f'<text x="{W/2}" y="310" text-anchor="middle" font-size="11" fill="#dbe6ff">{t[2]}</text>']
    return o, 320


def weight(lang):
    t = ("Débutant", "Joueur confirmé", "pardonne, protège le coude", "plus de puissance") if lang == "fr" else ("Beginner", "Experienced", "forgiving, easy on the elbow", "more power")
    o = [f'<rect x="0" y="0" width="{W}" height="300" rx="18" fill="{BLUE}"/>']
    for cx, g, name, sub, col, big in ((W * 0.28, "200–230 g", t[0], t[2], LIME, False), (W * 0.72, "230–250 g", t[1], t[3], "#ffffff", True)):
        w = 66 if not big else 74
        o.append(f'<rect x="{cx-w/2}" y="50" width="{w}" height="{w*1.2}" rx="{w/2.4}" fill="{col}" stroke="#0f1c2e" stroke-width="3"/>')
        o.append(f'<rect x="{cx-8}" y="{50+w*1.2-4}" width="16" height="56" rx="6" fill="#0f1c2e"/>')
        o.append(f'<text x="{cx}" y="{50+w*0.65}" text-anchor="middle" font-size="11" font-weight="800" fill="#0f1c2e">{g}</text>')
        o.append(f'<text x="{cx}" y="236" text-anchor="middle" font-size="16" font-weight="800" fill="#fff">{name}</text>')
        o.append(f'<text x="{cx}" y="256" text-anchor="middle" font-size="11" fill="#dbe6ff">{sub}</text>')
    return o, 300


SPECIAL = {13: balls, 14: grip, 21: weight}

ORDER = ["service-profond", "retour-et-monter", "troisieme-coup-drop", "raquette-haute", "patience-dink", "communiquer-double",
         "pieds-cuisine", "viser-pieds", "echauffement", "score-annonce", "revers-dink", "lob-prudence", "reset",
         "balles-interieur-exterieur", "grip-continental", "milieu-terrain", "partenaire-ensemble", "speed-up", "vent-exterieur",
         "mental-point", "ernes", "raquette-legere", "cible-centre", "chaussures", "simple-retour-profond"]
INDEX = {k: n for n, k in enumerate(ORDER)}

FALLBACK = {  # used for new tips without a dedicated drawing, by category
    "Service": 0, "Retour": 1, "Stratégie": 2, "Technique": 3, "Double": 22, "Règles": 6, "Santé": 8, "Extérieur": 18,
    "Mental": 19, "Avancé": 20, "Return": 1, "Strategy": 2, "Technique ": 3, "Doubles": 22, "Rules": 6, "Health": 8,
    "Outdoor": 18, "Advanced": 20, "Serve": 0, "Simple": 24, "Singles": 24,
}


def svg(key, lang, cat="", caption=""):
    i = INDEX.get(key, -1)
    aria = esc(caption) or ("Schéma de la situation" if lang == "fr" else "Diagram of the situation")
    if i in SPECIAL:
        parts, h = SPECIAL[i](lang)
        return f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="{aria}" style="{FONT}">' + "".join(parts) + "</svg>"
    parts = scene(i, lang)
    if parts is None:
        j = FALLBACK.get(cat, 4)
        parts = scene(j, lang) if j not in SPECIAL else scene(4, lang)
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{aria}" style="{FONT}">' + "".join(court() + parts) + "</svg>"


LEGEND = {
    "fr": '<span><i style="background:#d6f03f"></i>vous et votre partenaire</span><span><i style="background:#fff"></i>adversaires</span><span><i class="dash"></i>trajectoire de la balle</span>',
    "en": '<span><i style="background:#d6f03f"></i>you and your partner</span><span><i style="background:#fff"></i>opponents</span><span><i class="dash"></i>ball path</span>',
}
