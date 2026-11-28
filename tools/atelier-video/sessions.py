"""Catalogue de séances courtes (30 à 60 s) : terrain animé, raquettes, balle, voix off, sous-titres, miniature.
Usage : python3 sessions.py frames|thumbs|render [slug ...]"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import render as R
from render import Pen, FT, P, court, ball_at, bounce_mark, tag, check, seg, lerp, ease, subtitle, chunks
from render import W, H, FPS, S, COURT, DEEP, KIT, GRASS, BALL, INK, WHITE, RED, SOFT, NET, K1, K2, CL, CWD

ROOT = R.ROOT
OUT = os.path.join(ROOT, "catalogue")
LEVELS = {"decouverte": ("Découverte", (42, 138, 87)), "initie": ("Initié", (31, 95, 191)),
          "confirme": ("Confirmé", (14, 58, 120)), "avance": ("Avancé", (200, 55, 30))}
LEAD, GAP, TAIL = 0.3, 0.25, 0.6

# ---------- helpers to describe a scene ----------
def shot(a, b, f, t, h=60, c="ball", mark=None, who=None, n=False):
    return dict(u=(a, b), f=f, t=t, h=h, c=c, mark=mark, who=who, n=n)
def mv(who, a, b, to): return dict(who=who, u=(a, b), to=to)
DOUBLES = {"me1": (-0.3, 1.5, True, "Vous"), "me2": (0.4, 4.6, True, "Partenaire"), "op1": (13.0, 4.6, False, None), "op2": (13.0, 1.5, False, None)}
def team(**over):
    d = dict(DOUBLES); d.update(over); return d
KIT_OP, KIT_ME, DEEP_OP = (NET, K2), (K1, NET), (10.4, CL)


def reps(n, a, b, feed_from, feed_to, shot_from, lands, pattern, h_feed=40, h_shot=120, who_feed="op1", who="me1", count=True, c="ball"):
    """n repetitions between u=a and u=b: a feed then the player's shot; lands[i] = landing point, pattern[i] = 1 good / 0 bad."""
    out = []; step = (b - a) / n
    for i in range(n):
        s = a + i * step
        if feed_from: out.append(shot(s, s + step * 0.38, feed_from, feed_to, h_feed, who=who_feed))
        g = pattern[i % len(pattern)]
        out.append(shot(s + step * (0.42 if feed_from else 0.05), s + step * 0.9, shot_from, lands[i % len(lands)], h_shot, c=c, mark="good" if g else "bad", who=who, n=count and bool(g)))
    return out


def rep_moves(n, a, b, who, go, back):
    """Déplacements répétés à chaque essai : go/back = [(début, fin, destination)] en fraction de l'essai."""
    out = []; step = (b - a) / n
    for i in range(n):
        s0 = a + i * step
        for f0, f1, to in go: out.append(mv(who, s0 + f0 * step, s0 + f1 * step, to))
        for f0, f1, to in back: out.append(mv(who, s0 + f0 * step, s0 + f1 * step, to))
    return out


def atp_reps(n, a, b, lands, pattern):
    """Tour du poteau : dink croisé qui rebondit dans le terrain, sort, puis frappe autour du poteau."""
    out = []; step = (b - a) / n
    for i in range(n):
        s0 = a + i * step; g = pattern[i % len(pattern)]
        out += [shot(s0, s0 + step * .3, (8.9, 4.8), (6.2, 0.35), 30, who="op1"), shot(s0 + step * .3, s0 + step * .42, (6.2, 0.35), (6.4, -0.6), 14),
                shot(s0 + step * .45, s0 + step * .9, (6.4, -0.6), lands[i % len(lands)], 6, c="red", mark="good" if g else "bad", who="me1", n=bool(g))]
    return out


def pair_reps(n, a, b, feed_from, hit_from, go_to, home, lands, call=False):
    """Balles au milieu : le joueur du côté de la balle se déplace, l'annonce et la joue (en alternance)."""
    shots_, moves_, bubbles_ = [], [], []; step = (b - a) / n; names = ["me1", "me2"]
    for i in range(n):
        s0 = a + i * step; k = i % 2; who = names[k]
        shots_.append(shot(s0, s0 + step * .38, feed_from, (hit_from[k][0] + .2, hit_from[k][1]), 30, who="op1"))
        shots_.append(shot(s0 + step * .42, s0 + step * .9, hit_from[k], lands[k], 25, mark="good", who=who, n=True))
        moves_ += [mv(who, s0 + step * .05, s0 + step * .35, go_to[k]), mv(who, s0 + step * .9, s0 + step * .99, home[k])]
        if call: bubbles_.append((s0 + step * .2, s0 + step * .55, who, "J'ai !"))
    return dict(shots=shots_, moves=moves_, bubbles=bubbles_)


def slide_reps(n, a, b):
    """Balles à gauche puis à droite : les deux partenaires glissent ensemble, celui du côté de la balle joue."""
    shots_, moves_ = [], []; step = (b - a) / n
    for i in range(n):
        s0 = a + i * step; left = i % 2 == 0
        y_hit, who = (0.9, "me1") if left else (5.2, "me2")
        shots_.append(shot(s0, s0 + step * .38, (9.0, 3.05), (5.1, y_hit), 30, who="op1"))
        shots_.append(shot(s0 + step * .45, s0 + step * .9, (4.4, y_hit), (8.4, 2.6 if left else 3.5), 26, mark="good", who=who, n=True))
        to1, to2 = ((4.3, 0.9), (4.3, 3.9)) if left else ((4.3, 2.2), (4.3, 5.2))
        moves_ += [mv("me1", s0 + step * .05, s0 + step * .38, to1), mv("me2", s0 + step * .05, s0 + step * .38, to2)]
    return dict(shots=shots_, moves=moves_)


# ---------- the catalogue ----------
S_ = []
def session(**kw): S_.append(kw)

# DÉCOUVERTE
session(slug="d1-service-profond", level="decouverte", title="Le service, simple et profond",
 intro="Niveau découverte. Aujourd'hui : un service simple et profond.",
 demo=dict(text="Le service se fait à la cuillère, sous la taille, en diagonale. La balle doit passer la cuisine : si elle touche la ligne de la cuisine, c'est faute. Visez plutôt le fond du terrain, l'adversaire restera loin du filet.",
   players=team(), panel=("Les règles", [("À la cuillère, sous la taille", .03), ("En diagonale", .2), ("Au-delà de la cuisine", .38), ("Ligne de cuisine : faute", .55), ("Visez le fond", .78)]),
   shots=[shot(.08, .3, (-0.3, 1.5), (10.2, 4.4), 70, mark="good", who="me1"), shot(.42, .6, (-0.3, 1.5), (8.8, 4.3), 55, mark="bad", who="me1"), shot(.74, .95, (-0.3, 1.5), (12.4, 4.5), 80, mark="good", who="me1")],
   glows=[(.74, 1, DEEP_OP)], tags=[(.58, .74, 8.8, 7.0, "Sur la ligne de cuisine : faute", "red"), (.9, 1, 11.8, 7.0, "Profond : parfait", "lime")]),
 exo=dict(text="Exercice : dix services, en visant le dernier tiers du terrain. Comptez ceux qui y tombent. Objectif : six sur dix.",
   players=team(me2=(0.4, 4.6, True, None)), panel=("L'exercice", [("10 services", .05), ("Visez le dernier tiers", .2), ("Objectif 6 / 10", .55)]),
   shots=reps(10, .12, .98, None, None, (-0.3, 1.5), [(12.2, 4.3), (11.4, 4.9), (9.8, 4.4), (12.6, 3.9), (11.0, 4.5), (12.0, 5.2), (9.4, 4.1), (11.8, 4.6), (12.5, 4.2), (11.2, 4.8)], [1, 1, 0, 1, 1, 1, 0, 1, 1, 1], h_shot=70),
   glows=[(0, 1, DEEP_OP)], counter=("Au fond", 10, "objectif 6")),
 outro="Retenez : à la cuillère, en diagonale, et profond.")

session(slug="d2-deux-rebonds", level="decouverte", title="La règle des deux rebonds",
 intro="Niveau découverte. Aujourd'hui : la règle des deux rebonds.",
 demo=dict(text="Le service doit rebondir avant d'être retourné. Le retour doit rebondir lui aussi, avant d'être joué. Ensuite seulement, vous avez le droit de volleyer.",
   players=team(op2=(9.0, 1.5, False, None)), panel=("La règle", [("Le service rebondit", .05), ("Le retour rebondit", .35), ("Ensuite, volée permise", .68)]),
   shots=[shot(.05, .28, (-0.3, 1.5), (11.0, 4.4), 70, mark="good", who="me1"), shot(.32, .58, (13.0, 4.6), (1.6, 4.2), 80, mark="good", who="op1"),
          shot(.62, .76, (0.6, 4.4), (8.9, 1.9), 40, who="me2"), shot(.78, .9, (9.0, 1.6), (1.0, 2.0), 30, who="op2")],
   moves=[mv("op1", .3, .5, (9.0, 4.6))],
   tags=[(.24, .4, 11.0, 7.0, "Rebond n°1", "lime"), (.55, .7, 1.8, 7.0, "Rebond n°2", "lime"), (.78, 1, 6.7, 7.0, "Volée permise", "normal")]),
 exo=dict(text="Exercice : à deux, échangez en laissant rebondir les deux premières balles, puis volleyez. Dix échanges sans oublier un rebond.",
   players={"me1": (1.0, 3.05, True, "Vous"), "op1": (12.4, 3.05, False, "Partenaire")}, panel=("L'exercice", [("2 rebonds, puis volée", .08), ("10 échanges", .3), ("Objectif 8 / 10", .55)]),
   shots=reps(10, .1, .98, (12.4, 3.05), (1.6, 3.0), (1.2, 3.0), [(11.6, 3.1), (11.2, 2.6), (11.9, 3.5)], [1, 1, 1, 0, 1, 1, 1, 1, 0, 1], h_feed=60, h_shot=60),
   counter=("Échanges réussis", 10, "objectif 8")),
 outro="Retenez : un rebond de chaque côté, puis la volée est permise.")

session(slug="d3-la-cuisine", level="decouverte", title="La cuisine : pas de volée dedans",
 intro="Niveau découverte. Aujourd'hui : la zone de la cuisine.",
 demo=dict(text="La cuisine, c'est la zone de deux mètres treize de chaque côté du filet. Vous pouvez y entrer, mais pas y frapper de volée. Volée depuis la ligne : c'est bon. Un pied dedans, même sur la ligne : faute. Si la balle a rebondi, vous pouvez entrer pour la jouer.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.1, 3.05, False, None)},
   panel=("La cuisine", [("2,13 m de chaque côté", .03), ("Entrer : oui", .18), ("Volée dedans : non", .3), ("Volée depuis la ligne : bon", .42), ("Pied sur la ligne : faute", .6), ("Après rebond : vous entrez", .8)]),
   shots=[shot(.36, .48, (9.0, 3.0), (4.4, 3.0), 30, who="op1"), shot(.48, .56, (4.4, 3.0), (9.6, 3.3), 25, who="me1"),
          shot(.58, .68, (9.0, 3.2), (5.2, 3.2), 30, who="op1"), shot(.76, .84, (9.0, 3.0), (5.6, 2.6), 40, mark="good", who="op1"), shot(.9, .98, (5.6, 2.7), (8.2, 2.8), 30, who="me1")],
   moves=[mv("me1", .6, .66, (5.1, 3.1)), mv("me1", .7, .74, (4.3, 3.05)), mv("me1", .84, .9, (5.5, 2.8))],
   glows=[(0, .3, KIT_ME)],
   tags=[(.5, .58, 4.4, 7.0, "Derrière la ligne : bon", "lime"), (.66, .76, 5.2, 7.0, "Pied dans la cuisine : faute", "red"), (.88, 1, 5.6, 7.0, "Après rebond : autorisé", "lime")]),
 exo=dict(text="Exercice : à la ligne de cuisine, votre partenaire vous envoie dix balles. Volleyez sans jamais poser un pied dans la zone. Objectif : neuf sur dix.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.1, 3.05, False, "Partenaire")}, panel=("L'exercice", [("À la ligne de cuisine", .05), ("10 volées", .2), ("Aucun pied dans la zone", .32), ("Objectif 9 / 10", .6)]),
   shots=reps(10, .1, .98, (9.0, 3.05), (4.6, 3.0), (4.5, 3.0), [(9.8, 3.0), (10.2, 2.4), (9.6, 3.7)], [1, 1, 1, 1, 1, 0, 1, 1, 1, 1], h_feed=30, h_shot=25),
   glows=[(0, 1, KIT_ME)], counter=("Volées propres", 10, "objectif 9")),
 outro="Retenez : jamais de volée les pieds dans la cuisine.")

# INITIÉ
session(slug="i1-retour-et-monter", level="initie", title="Retour long, puis on monte",
 intro="Niveau initié. Aujourd'hui : retourner, puis monter au filet.",
 demo=dict(text="Quand vous retournez le service, jouez long, vers le fond. La balle met du temps à traverser : profitez-en pour monter jusqu'à la ligne de cuisine. Votre partenaire y est déjà. À deux au filet, vous avez l'avantage.",
   players=team(me1=(0.4, 4.6, True, "Vous"), me2=(4.3, 1.5, True, "Partenaire"), op1=(13.7, 1.5, False, None), op2=(13.0, 4.6, False, None)),
   panel=("Le principe", [("Retour long, vers le fond", .1), ("Montez pendant le vol", .4), ("À deux au filet", .75)]),
   shots=[shot(.03, .22, (13.7, 1.6), (1.0, 4.4), 70, mark="good", who="op1"), shot(.26, .55, (1.0, 4.4), (12.4, 1.8), 110, mark="good", who="me1")],
   moves=[mv("me1", .3, .6, (4.3, 4.6))], glows=[(.26, .6, DEEP_OP)], tags=[(.6, 1, 2.4, 7.0, "Les deux à la ligne de cuisine", "lime")]),
 exo=dict(text="Exercice : votre partenaire sert, vous retournez long et vous montez. Dix fois. Arrêtez-vous à la ligne, raquette devant vous. Objectif : sept retours au fond.",
   players={"me1": (0.6, 4.4, True, "Vous"), "op1": (13.7, 1.6, False, "Partenaire")}, panel=("L'exercice", [("Retour long", .05), ("On monte à la ligne", .18), ("10 fois, objectif 7", .5)]),
   shots=reps(10, .1, .98, (13.7, 1.6), (1.2, 4.2), (1.2, 4.2), [(12.2, 3.0), (11.6, 2.4), (9.6, 3.4), (12.5, 3.6)], [1, 1, 0, 1, 1, 1, 0, 1, 1, 0], h_feed=60, h_shot=100),
   glows=[(0, 1, DEEP_OP)], counter=("Retours au fond", 10, "objectif 7"), moves=rep_moves(10, .1, .98, "me1", [(.5, .97, (4.3, 4.4))], [(0, .3, (0.6, 4.4))])),
 outro="Retenez : retour long, et on monte.")

session(slug="i2-le-drop", level="initie", title="Le troisième coup : le drop",
 intro="Niveau initié. Aujourd'hui : le troisième coup amorti, le drop.",
 demo=dict(text="Le drop, c'est une balle douce qui retombe dans la cuisine adverse. Geste de bas en haut : on pousse, on ne frappe pas. Il oblige l'adversaire à jouer vers le haut, et vous laisse le temps d'avancer.",
   players=team(op1=(9.0, 4.6, False, None), op2=(9.0, 1.5, False, None)), panel=("Le principe", [("Balle douce", .05), ("De bas en haut", .25), ("Dans sa cuisine", .45), ("Vous avancez", .75)]),
   shots=[shot(.1, .5, (-0.2, 1.6), (7.7, 2.2), 150, mark="good", who="me1")], moves=[mv("me1", .65, .9, (4.2, 1.5)), mv("me2", .65, .9, (4.2, 4.6))],
   glows=[(.4, .7, KIT_OP)], tags=[(.5, .7, 7.8, 7.0, "Dans la cuisine", "lime"), (.75, 1, 2.4, 7.0, "Vous avancez", "normal")]),
 exo=dict(text="Exercice : depuis la ligne de fond, dix drops. Comptez ceux qui tombent dans la cuisine. Objectif : six sur dix.",
   players={"me1": (0.5, 3.05, True, "Vous"), "op1": (9.1, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Ligne de fond", .05), ("10 drops", .2), ("Objectif 6 / 10", .5)]),
   shots=reps(10, .1, .98, (9.0, 3.05), (1.2, 3.0), (1.0, 3.0), [(7.8, 2.3), (7.6, 3.1), (9.9, 2.0), (8.1, 3.9), (7.5, 2.7), (8.3, 3.4), (9.8, 4.1), (7.9, 2.5), (7.7, 3.6), (8.2, 3.0)], [1, 1, 0, 1, 1, 1, 0, 1, 1, 1], h_feed=40, h_shot=140),
   glows=[(0, 1, KIT_OP)], counter=("Dans la cuisine", 10, "objectif 6")),
 outro="Retenez : balle douce, et on avance.")

session(slug="i3-parler-en-double", level="initie", title="En double, on se parle",
 intro="Niveau initié. Aujourd'hui : se parler en double.",
 demo=dict(text="En double, la balle au milieu est la plus dangereuse : chacun croit que l'autre va la jouer. Annoncez à voix haute. J'ai, quand vous la prenez. À toi, pour votre partenaire. Laisse, si elle sort.",
   players=team(me1=(4.3, 1.5, True, "Vous"), me2=(4.3, 4.6, True, "Partenaire"), op1=(9.0, 4.6, False, None), op2=(9.0, 1.5, False, None)),
   panel=("Trois mots", [("La balle au milieu", .05), ("« J'ai »", .45), ("« À toi »", .6), ("« Laisse »", .78)]),
   shots=[shot(.1, .3, (9.0, 2.0), (3.6, 3.05), 30, who="op2"), shot(.4, .52, (9.0, 4.0), (3.8, 2.6), 30, who="op1"), shot(.52, .6, (4.2, 2.4), (9.6, 3.3), 25, who="me1"),
          shot(.62, .72, (9.0, 2.0), (3.8, 3.6), 30, who="op2"), shot(.72, .78, (4.2, 4.4), (9.6, 2.6), 25, who="me2"), shot(.82, .98, (9.0, 4.4), (-0.6, 3.4), 160, mark="bad", who="op1")],
   moves=[mv("me1", .4, .5, (4.3, 2.3)), mv("me1", .6, .66, (4.3, 1.5))],
   bubbles=[(.12, .32, "me1", "?"), (.12, .32, "me2", "?"), (.42, .56, "me1", "J'ai !"), (.6, .74, "me1", "À toi !"), (.84, 1, "me2", "Laisse !")]),
 exo=dict(text="Exercice : votre adversaire envoie dix balles au milieu. Annoncez chaque balle avant de la jouer. Zéro balle sans un mot.",
   players=team(me1=(4.3, 1.5, True, "Vous"), me2=(4.3, 4.6, True, "Partenaire"), op1=(9.0, 3.05, False, None), op2=(13.0, 1.5, False, None)),
   panel=("L'exercice", [("10 balles au milieu", .05), ("Annoncez chacune", .2), ("Objectif 10 / 10", .5)]),
   **pair_reps(10, .1, .98, (9.0, 3.05), [(4.4, 2.6), (4.4, 3.5)], [(4.3, 2.5), (4.3, 3.6)], [(4.3, 1.5), (4.3, 4.6)], [(9.8, 2.4), (9.6, 3.6)], call=True),
   counter=("Balles annoncées", 10, "objectif 10")),
 outro="Retenez : j'ai, à toi, laisse.")

# CONFIRMÉ
session(slug="c1-dink-patient", level="confirme", title="Le dink, avec patience",
 intro="Niveau confirmé. Aujourd'hui : le dink patient.",
 demo=dict(text="Le dink, c'est une balle douce jouée depuis la ligne de cuisine, qui retombe dans la cuisine adverse. Le but n'est pas de gagner tout de suite. Gardez la balle basse, en diagonale, et attendez la faute, ou la balle trop haute.",
   players=team(me1=(4.3, 1.5, True, "Vous"), me2=(4.3, 4.6, True, "Partenaire"), op1=(9.0, 4.6, False, None), op2=(9.0, 1.5, False, None)),
   panel=("Le dink", [("Depuis la ligne de cuisine", .05), ("Dans la cuisine adverse", .2), ("Bas et en diagonale", .55), ("Patience", .78)]),
   shots=[shot(.08 + i * .12, .18 + i * .12, (4.4, 1.6) if i % 2 == 0 else (8.9, 4.5), (7.6, 4.3) if i % 2 == 0 else (5.8, 1.8), 32, who="me1" if i % 2 == 0 else "op1") for i in range(7)],
   glows=[(0, 1, KIT_OP), (0, 1, KIT_ME)]),
 exo=dict(text="Exercice : en diagonale, enchaînez vingt dinks sans faute avec votre partenaire. Une faute, et on repart à zéro.",
   players={"me1": (4.3, 1.5, True, "Vous"), "op1": (9.0, 4.6, False, "Partenaire")}, panel=("L'exercice", [("En diagonale", .05), ("20 dinks sans faute", .2), ("Une faute : on repart à zéro", .5)]),
   shots=[shot(.1 + i * .044, .14 + i * .044, (4.4, 1.6) if i % 2 == 0 else (8.9, 4.5), (7.6, 4.2) if i % 2 == 0 else (5.8, 1.9), 26, who="me1" if i % 2 == 0 else "op1", mark="good", n=True) for i in range(20)],
   glows=[(0, 1, KIT_OP), (0, 1, KIT_ME)], counter=("Dinks d'affilée", 20, "objectif 20")),
 outro="Retenez : bas, en diagonale, et patient.")

session(slug="c2-le-reset", level="confirme", title="Le reset sous pression",
 intro="Niveau confirmé. Aujourd'hui : le reset sous pression.",
 demo=dict(text="Vous êtes au milieu du terrain, et l'adversaire accélère sur vous. Ne contrez pas plus fort. Raquette ouverte, geste court : amortissez, pour que la balle retombe dans sa cuisine. C'est le reset. Vous revenez au neutre, et vous pouvez avancer.",
   players={"me1": (2.8, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, None)}, panel=("Le reset", [("Il accélère sur vous", .05), ("Pas plus fort", .25), ("On amortit", .4), ("Dans sa cuisine", .55), ("Puis on avance", .8)]),
   shots=[shot(.08, .2, (9.0, 3.0), (3.0, 3.1), 12, c="red", who="op1"), shot(.38, .5, (9.0, 3.0), (3.0, 3.1), 12, c="red", who="op1"), shot(.5, .7, (3.0, 3.1), (7.6, 3.0), 70, mark="good", who="me1")],
   moves=[mv("me1", .78, .95, (4.3, 3.05))], glows=[(.55, .8, KIT_OP)], tags=[(.68, .85, 7.6, 7.0, "La balle meurt dans la cuisine", "lime")]),
 exo=dict(text="Exercice : votre partenaire, à la cuisine, accélère sur vous. Depuis le milieu du terrain, renvoyez chaque balle dans sa cuisine. Dix balles, objectif six.",
   players={"me1": (2.8, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Vous au milieu du terrain", .05), ("Il accélère", .18), ("10 resets, objectif 6", .5)]),
   shots=reps(10, .1, .98, (9.0, 3.05), (3.1, 3.0), (3.0, 3.0), [(7.6, 3.0), (7.9, 2.4), (9.8, 3.4), (7.4, 3.7)], [1, 1, 0, 1, 0, 1, 1, 1, 0, 1], h_feed=10, h_shot=70),
   glows=[(0, 1, KIT_OP)], counter=("Dans la cuisine", 10, "objectif 6"), feed_red=True),
 outro="Retenez : on absorbe, on ne renvoie pas plus fort.")

session(slug="c3-accelerer", level="confirme", title="Accélérer la bonne balle",
 intro="Niveau confirmé. Aujourd'hui : choisir la balle à accélérer.",
 demo=dict(text="En échange de dinks, n'accélérez pas n'importe quelle balle. Si elle reste basse, sous le filet, continuez à dinker. Si elle monte au-dessus du filet, accélérez, vers les pieds ou la hanche de l'adversaire.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, None)}, panel=("Le bon choix", [("Balle basse : on dinke", .3), ("Balle haute : on accélère", .6), ("Vers les pieds", .8)]),
   shots=[shot(.1, .22, (9.0, 3.0), (5.8, 3.1), 26, who="op1"), shot(.22, .34, (4.4, 3.0), (7.6, 2.9), 26, who="me1"), shot(.36, .5, (9.0, 3.0), (4.6, 3.2), 90, who="op1"),
          shot(.62, .72, (4.5, 3.1), (8.9, 3.3), 10, c="red", who="me1", mark="good")],
   tags=[(.24, .36, 6.7, 7.0, "Basse : on dinke", "normal"), (.5, .62, 4.6, 7.0, "Au-dessus du filet !", "lime"), (.72, 1, 9.0, 7.0, "Dans les pieds", "lime")]),
 exo=dict(text="Exercice : dinkez avec votre partenaire, et accélérez seulement quand la balle monte au-dessus du filet. Comptez vos bons choix sur dix. Objectif : huit.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Dinks en continu", .05), ("Accélérez la balle haute", .2), ("10 choix, objectif 8", .55)]),
   shots=reps(10, .1, .98, (9.0, 3.05), (5.0, 3.0), (4.5, 3.0), [(7.7, 3.0), (8.9, 3.3)], [1, 1, 1, 0, 1, 1, 1, 1, 0, 1], h_feed=50, h_shot=26),
   glows=[(0, 1, KIT_OP)], counter=("Bons choix", 10, "objectif 8")),
 outro="Retenez : balle basse, on dinke. Balle haute, on accélère.")

# AVANCÉ
session(slug="a1-stacking", level="avance", title="Le stacking en double",
 intro="Niveau avancé. Aujourd'hui : le stacking.",
 demo=dict(text="Le stacking, c'est un placement en double. Au service, les deux partenaires se placent du même côté, puis l'un traverse juste après la frappe. Chacun garde ainsi son côté préféré. Attention : l'ordre de service, lui, ne change pas.",
   players=team(me1=(-0.3, 1.5, True, "Vous"), me2=(-0.3, 2.5, True, "Partenaire")), panel=("Le stacking", [("Même côté au départ", .2), ("On traverse après la frappe", .4), ("Chacun son côté préféré", .62), ("Ordre de service inchangé", .82)]),
   shots=[shot(.3, .5, (-0.3, 1.5), (11.0, 4.4), 70, mark="good", who="me1")], moves=[mv("me2", .34, .5, (-0.3, 4.6))],
   tags=[(.08, .3, 1.6, 7.0, "Les deux du même côté", "lime"), (.4, .6, 1.6, 7.0, "Il traverse", "normal")]),
 exo=dict(text="Exercice : jouez dix points en stacking. Après chaque service et chaque retour, vérifiez que chacun est bien de son côté. Objectif : huit points bien placés.",
   players=team(me1=(-0.3, 1.5, True, "Vous"), me2=(-0.3, 2.5, True, "Partenaire")), panel=("L'exercice", [("10 points en stacking", .05), ("Chacun de son côté", .2), ("Objectif 8 / 10", .55)]),
   shots=reps(10, .1, .98, None, None, (-0.3, 1.5), [(11.0, 4.4), (11.6, 4.1)], [1, 1, 1, 1, 0, 1, 1, 1, 1, 0], h_shot=70),
   counter=("Points bien placés", 10, "objectif 8"), stack=True),
 outro="Retenez : même côté, puis on traverse. L'ordre de service ne change pas.")

session(slug="a2-erne", level="avance", title="L'erne, sans toucher la cuisine",
 intro="Niveau avancé. Aujourd'hui : l'erne.",
 demo=dict(text="L'erne, c'est une volée jouée à côté de la cuisine, en dehors du terrain. Vous contournez la zone, ou vous sautez par-dessus son coin, et vous frappez près du filet. C'est légal tant que vous ne touchez pas la cuisine.",
   players={"me1": (4.3, 0.8, True, "Vous"), "op1": (9.0, 0.8, False, None)}, panel=("L'erne", [("Volée hors du terrain", .05), ("À côté de la cuisine", .2), ("Frappe près du filet", .5), ("Jamais dans la cuisine", .78)]),
   shots=[shot(.25, .45, (9.0, 0.6), (5.9, -0.3), 40, who="op1"), shot(.45, .55, (5.9, -0.45), (8.4, 1.6), 15, c="red", who="me1", mark="good")],
   moves=[mv("me1", .14, .28, (4.3, -0.45)), mv("me1", .28, .42, (5.9, -0.45)), mv("me1", .7, .8, (4.3, -0.45)), mv("me1", .8, .9, (4.3, 0.8))], glows=[(0, 1, KIT_ME)],
   tags=[(.42, .7, 5.6, 7.0, "Hors du terrain, cuisine intacte", "lime")]),
 exo=dict(text="Exercice : votre partenaire dinke le long de la ligne de côté. Sortez du terrain et volleyez, sans jamais toucher la cuisine. Dix essais, objectif six.",
   players={"me1": (4.3, 0.8, True, "Vous"), "op1": (9.0, 0.8, False, "Partenaire")}, panel=("L'exercice", [("Dink le long de la ligne", .05), ("Sortez et volleyez", .2), ("10 essais, objectif 6", .55)]),
   shots=reps(10, .1, .98, (9.0, 0.6), (5.9, -0.3), (5.9, -0.45), [(8.4, 1.6), (9.2, 2.4), (10.4, 0.2)], [1, 1, 0, 1, 1, 0, 1, 1, 0, 1], h_feed=40, h_shot=15, c="red"),
   glows=[(0, 1, KIT_ME)], counter=("Ernes propres", 10, "objectif 6"), moves=rep_moves(10, .1, .98, "me1", [(.0, .18, (4.3, -0.45)), (.18, .4, (5.9, -0.45))], [(.9, .95, (4.3, -0.45)), (.95, .995, (4.3, 0.8))])),
 outro="Retenez : on contourne la cuisine, jamais dedans.")

session(slug="a3-bloquer", level="avance", title="Bloquer une accélération",
 intro="Niveau avancé. Aujourd'hui : bloquer une accélération au filet.",
 demo=dict(text="Au filet, l'adversaire peut accélérer à tout moment. Gardez la raquette haute, devant la poitrine, entre chaque coup. Sur l'accélération, ne frappez pas : bloquez, avec un geste court, et renvoyez la balle bas, dans ses pieds.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, None)}, panel=("Le blocage", [("Raquette haute", .25), ("Devant la poitrine", .38), ("On bloque, geste court", .6), ("Bas, dans ses pieds", .8)]),
   shots=[shot(.1, .2, (9.0, 3.0), (5.8, 3.0), 26, who="op1"), shot(.2, .3, (4.4, 3.0), (7.6, 3.1), 26, who="me1"), shot(.52, .6, (9.0, 3.1), (4.5, 3.0), 8, c="red", who="op1"),
          shot(.6, .74, (4.5, 3.0), (8.6, 3.0), 30, who="me1", mark="good")],
   tags=[(.6, .76, 4.4, 7.0, "Bloquée", "lime"), (.74, 1, 8.6, 7.0, "Dans ses pieds", "lime")]),
 exo=dict(text="Exercice : votre partenaire accélère sur vous sans prévenir, depuis la cuisine. Bloquez dix balles, raquette haute. Objectif : sept balles remises en jeu.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Il accélère sans prévenir", .05), ("Raquette haute", .2), ("10 blocages, objectif 7", .5)]),
   shots=reps(10, .1, .98, (9.0, 3.05), (4.6, 3.0), (4.5, 3.0), [(8.6, 3.0), (8.4, 2.4), (10.6, 3.6)], [1, 1, 0, 1, 1, 1, 0, 1, 1, 0], h_feed=8, h_shot=30),
   counter=("Balles remises", 10, "objectif 7"), feed_red=True),
 outro="Retenez : raquette haute, et on bloque.")


# ---------- nouvelles séances (28/11) ----------
# DÉCOUVERTE
session(slug="d4-annoncer-le-score", level="decouverte", title="Annoncer le score en double",
 intro="Niveau découverte. Aujourd'hui : annoncer le score en double.",
 demo=dict(text="En double, le serveur annonce trois chiffres avant de servir. D'abord les points de son équipe, puis ceux de l'adversaire, puis un ou deux, selon le serveur. Seule l'équipe qui sert marque des points. En début de partie, on annonce zéro, zéro, deux.",
   players=team(), panel=("Trois chiffres", [("Nos points", .1), ("Leurs points", .22), ("Serveur 1 ou 2", .36), ("Seul le serveur marque", .55), ("Départ : 0-0-2", .8)]),
   shots=[shot(.12, .3, (-0.3, 1.5), (11.0, 4.4), 70, mark="good", who="me1"), shot(.32, .5, (13.0, 4.6), (1.4, 4.0), 80, who="op1"), shot(.52, .68, (0.6, 4.4), (12.6, 1.0), 60, who="me2"), shot(.7, .86, (13.0, 1.5), (-0.9, 1.2), 70, mark="bad", who="op2")],
   bubbles=[(.02, .14, "me1", "0 - 0 - 2"), (.86, 1, "me1", "1 - 0 - 2")],
   tags=[(.84, 1, 2.0, 7.0, "Balle dehors : point pour l'équipe au service", "lime")]),
 exo=dict(text="Exercice : jouez dix points, et annoncez le score à voix haute avant chaque service. Votre partenaire vérifie. Objectif : dix annonces justes.",
   players=team(), panel=("L'exercice", [("10 points", .05), ("Annonce avant chaque service", .18), ("Objectif 10 / 10", .55)]),
   shots=reps(10, .1, .98, None, None, (-0.3, 1.5), [(11.0, 4.4), (11.8, 4.0), (10.6, 4.7)], [1], h_shot=70),
   counter=("Annonces justes", 10, "objectif 10")),
 outro="Retenez : nos points, leurs points, puis le serveur.")

session(slug="d5-rester-au-fond", level="decouverte", title="Après le service, restez au fond",
 intro="Niveau découverte. Aujourd'hui : où se placer après son service.",
 demo=dict(text="Après votre service, ne montez pas tout de suite. Le retour doit rebondir chez vous : restez derrière la ligne de fond. Si vous avancez trop tôt, la balle arrive dans vos pieds. Laissez-la rebondir, jouez-la, puis avancez.",
   players=team(), panel=("Le placement", [("Après le service", .05), ("Restez au fond", .2), ("Le retour rebondit", .42), ("Puis on avance", .78)]),
   shots=[shot(.08, .28, (-0.3, 1.5), (11.0, 4.4), 70, mark="good", who="me1"), shot(.32, .58, (13.0, 4.6), (1.2, 1.9), 90, mark="good", who="op1"), shot(.62, .82, (0.9, 1.9), (12.0, 2.4), 100, who="me1")],
   moves=[mv("me1", .34, .58, (0.9, 1.9)), mv("me1", .84, .98, (3.0, 1.6))],
   tags=[(.28, .58, 1.4, 7.0, "On attend derrière la ligne", "lime"), (.84, 1, 3.0, 7.0, "Maintenant, on avance", "normal")]),
 exo=dict(text="Exercice : servez, restez au fond, laissez rebondir le retour et renvoyez-le profond. Dix fois. Objectif : huit retours bien joués.",
   players={"me1": (0.5, 3.05, True, "Vous"), "op1": (13.0, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Service, on reste au fond", .05), ("Rebond, puis balle profonde", .2), ("10 fois, objectif 8", .55)]),
   shots=reps(10, .1, .98, (13.0, 3.0), (1.0, 3.0), (0.9, 3.0), [(12.0, 3.0), (11.5, 2.4), (9.4, 3.4), (12.3, 3.7)], [1, 1, 1, 0, 1, 1, 1, 1, 0, 1], h_feed=80, h_shot=100),
   glows=[(0, 1, DEEP_OP)], counter=("Balles profondes", 10, "objectif 8")),
 outro="Retenez : après le service, on attend le rebond au fond.")

session(slug="d6-echange-regulier", level="decouverte", title="Échanger long et régulier",
 intro="Niveau découverte. Aujourd'hui : tenir l'échange depuis le fond.",
 demo=dict(text="Au début, le plus important, c'est de remettre la balle. Visez le milieu du terrain adverse, assez haut au-dessus du filet, et assez long. Une balle simple et régulière vaut mieux qu'un coup risqué.",
   players={"me1": (0.8, 3.05, True, "Vous"), "op1": (12.6, 3.05, False, None)}, panel=("La régularité", [("Remettre la balle", .05), ("Vers le milieu", .25), ("Assez haut, assez long", .45), ("Simple avant tout", .75)]),
   shots=[shot(.05 + i * .13, .17 + i * .13, (0.9, 3.0) if i % 2 == 0 else (12.5, 3.1), (11.6, 2.8 + (i % 3) * .3) if i % 2 == 0 else (1.6, 3.2 - (i % 3) * .3), 110, who="me1" if i % 2 == 0 else "op1") for i in range(7)],
   glows=[(.2, .8, (9.5, 12.6))]),
 exo=dict(text="Exercice : depuis le fond, échangez avec votre partenaire. Comptez les balles d'affilée. Objectif : quinze balles sans faute.",
   players={"me1": (0.8, 3.05, True, "Vous"), "op1": (12.6, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Depuis le fond", .05), ("Balles d'affilée", .2), ("Objectif 15", .5)]),
   shots=[shot(.08 + i * .058, .13 + i * .058, (0.9, 3.0) if i % 2 == 0 else (12.5, 3.1), (11.6, 3.0) if i % 2 == 0 else (1.6, 3.0), 100, who="me1" if i % 2 == 0 else "op1", mark="good", n=True) for i in range(15)],
   counter=("Balles d'affilée", 15, "objectif 15")),
 outro="Retenez : au milieu, assez haut, assez long.")

# INITIÉ
session(slug="i4-dink-croise", level="initie", title="Le dink croisé, plus sûr",
 intro="Niveau initié. Aujourd'hui : le dink croisé.",
 demo=dict(text="Pour dinker, préférez la diagonale. Le filet est plus bas au centre, et la distance est plus longue : vous avez plus de marge. Le dink droit, le long de la ligne, est plus court et passe au-dessus de la partie haute du filet.",
   players={"me1": (4.3, 1.2, True, "Vous"), "op1": (9.0, 4.9, False, None), "op2": (9.0, 1.2, False, None)},
   panel=("Le dink croisé", [("En diagonale", .05), ("Filet plus bas au centre", .25), ("Plus de marge", .45), ("Le droit : plus risqué", .7)]),
   shots=[shot(.1, .26, (4.4, 1.3), (7.7, 4.6), 32, mark="good", who="me1"), shot(.28, .42, (8.9, 4.8), (5.8, 1.5), 32, who="op1"), shot(.66, .8, (4.4, 1.3), (6.9, 1.0), 20, mark="bad", who="me1")],
   tags=[(.24, .44, 7.7, 7.0, "Croisé : de la marge", "lime"), (.78, 1, 6.9, 7.0, "Droit : dans le filet", "red")]),
 exo=dict(text="Exercice : en diagonale, avec votre partenaire, jouez dix dinks croisés qui retombent dans la cuisine. Objectif : huit sur dix.",
   players={"me1": (4.3, 1.2, True, "Vous"), "op1": (9.0, 4.9, False, "Partenaire")}, panel=("L'exercice", [("Diagonale", .05), ("10 dinks croisés", .2), ("Objectif 8 / 10", .55)]),
   shots=reps(10, .1, .98, (8.9, 4.8), (4.6, 1.4), (4.4, 1.3), [(7.7, 4.6), (7.5, 4.1), (9.9, 4.8), (7.8, 5.0)], [1, 1, 1, 0, 1, 1, 1, 1, 0, 1], h_feed=30, h_shot=32),
   glows=[(0, 1, KIT_OP)], counter=("Dinks croisés", 10, "objectif 8")),
 outro="Retenez : en diagonale, on a plus de marge.")

session(slug="i5-bouger-ensemble", level="initie", title="Bouger ensemble, comme une corde",
 intro="Niveau initié. Aujourd'hui : se déplacer avec son partenaire.",
 demo=dict(text="En double, imaginez une corde de trois mètres entre vous et votre partenaire. Quand la balle part sur un côté, vous glissez tous les deux de ce côté. Vous ne laissez jamais un trou au milieu.",
   players=team(me1=(4.3, 1.5, True, "Vous"), me2=(4.3, 4.6, True, "Partenaire"), op1=(9.0, 4.6, False, None), op2=(9.0, 1.5, False, None)),
   panel=("La corde", [("Trois mètres entre vous", .05), ("La balle va sur un côté", .3), ("Vous glissez ensemble", .5), ("Pas de trou au milieu", .78)]),
   shots=[shot(.25, .4, (9.0, 1.6), (5.5, 0.4), 30, who="op2"), shot(.4, .5, (4.4, 0.6), (8.0, 2.5), 26, who="me1"), shot(.62, .76, (9.0, 4.4), (5.5, 5.6), 30, who="op1"), shot(.76, .86, (4.4, 5.5), (8.0, 3.4), 26, who="me2")],
   moves=[mv("me1", .26, .36, (4.3, 0.6)), mv("me2", .26, .36, (4.3, 3.6)), mv("me1", .62, .72, (4.3, 2.5)), mv("me2", .62, .72, (4.3, 5.5))],
   tags=[(.36, .6, 2.4, 7.0, "Les deux glissent", "lime"), (.72, .95, 2.4, 7.0, "Et de l'autre côté", "lime")]),
 exo=dict(text="Exercice : votre adversaire envoie dix balles, tantôt à gauche, tantôt à droite. Glissez ensemble à chaque balle, sans laisser le milieu ouvert. Objectif : dix déplacements à deux.",
   players=team(me1=(4.3, 1.5, True, "Vous"), me2=(4.3, 4.6, True, "Partenaire"), op1=(9.0, 3.05, False, None), op2=(13.0, 1.5, False, None)),
   panel=("L'exercice", [("Gauche, droite", .05), ("On glisse à deux", .2), ("Objectif 10 / 10", .55)]),
   **slide_reps(10, .1, .98),
   counter=("Déplacements à deux", 10, "objectif 10")),
 outro="Retenez : une corde entre vous, on bouge ensemble.")

session(slug="i6-viser-le-milieu", level="initie", title="Viser le milieu en double",
 intro="Niveau initié. Aujourd'hui : jouer au milieu des deux adversaires.",
 demo=dict(text="En cas de doute, jouez au milieu. Le filet y est plus bas, la balle reste dans le terrain, et les deux adversaires hésitent : qui va la prendre ? Une balle au milieu provoque souvent une faute, ou un coup faible.",
   players=team(me1=(4.3, 1.5, True, "Vous"), me2=(4.3, 4.6, True, "Partenaire"), op1=(9.0, 4.6, False, None), op2=(9.0, 1.5, False, None)),
   panel=("Le milieu", [("Filet plus bas", .1), ("Moins de risque de faute", .3), ("Ils hésitent", .55), ("Faute ou coup faible", .8)]),
   shots=[shot(.15, .35, (4.4, 1.6), (10.6, 3.05), 40, mark="good", who="me1"), shot(.5, .64, (9.5, 3.15), (6.2, 3.3), 80, who="op1")],
   moves=[mv("op1", .38, .5, (9.4, 3.3))],
   bubbles=[(.36, .5, "op1", "À toi ?"), (.36, .5, "op2", "À toi ?")],
   tags=[(.64, .9, 6.2, 7.0, "Balle facile pour vous", "lime")]),
 exo=dict(text="Exercice : à quatre, jouez dix balles en visant toujours le milieu, entre les deux adversaires. Comptez celles qui passent au centre. Objectif : sept.",
   players=team(me1=(4.3, 1.5, True, "Vous"), me2=(4.3, 4.6, True, "Partenaire"), op1=(9.0, 4.6, False, None), op2=(9.0, 1.5, False, None)),
   panel=("L'exercice", [("À quatre", .05), ("10 balles au milieu", .2), ("Objectif 7 / 10", .55)]),
   shots=reps(10, .1, .98, (9.0, 4.5), (4.6, 2.0), (4.4, 1.8), [(10.4, 3.05), (10.0, 2.8), (10.2, 0.9), (10.6, 3.3)], [1, 1, 0, 1, 1, 1, 0, 1, 1, 0], h_feed=30, h_shot=40, who_feed="op1"),
   glows=[(0, 1, (8.835, 13.41))], counter=("Balles au milieu", 10, "objectif 7")),
 outro="Retenez : dans le doute, au milieu.")

# CONFIRMÉ
session(slug="c4-drive-ou-drop", level="confirme", title="Drive ou drop au troisième coup ?",
 intro="Niveau confirmé. Aujourd'hui : choisir entre drive et drop.",
 demo=dict(text="Au troisième coup, regardez où sont les adversaires. S'ils sont déjà au filet, jouez le drop, dans leur cuisine. Si le relanceur est encore au fond, ou si le retour est court, frappez un drive, long et appuyé, puis enchaînez.",
   players=team(op1=(9.0, 4.6, False, None), op2=(11.6, 1.5, False, None)),
   panel=("Le choix", [("Regardez-les", .05), ("Au filet : drop", .25), ("Encore au fond : drive", .5), ("Puis on enchaîne", .8)]),
   shots=[shot(.1, .32, (-0.2, 1.6), (7.7, 4.0), 140, mark="good", who="me1"), shot(.52, .66, (-0.2, 1.6), (11.9, 2.2), 20, c="red", mark="good", who="me1")],
   moves=[mv("me1", .7, .95, (3.0, 1.6))],
   tags=[(.3, .48, 7.7, 7.0, "Ils sont au filet : drop", "lime"), (.64, .9, 11.9, 7.0, "Encore au fond : drive", "lime")]),
 exo=dict(text="Exercice : votre partenaire retourne, puis monte ou reste au fond. Choisissez drive ou drop selon sa place. Dix balles, objectif huit bons choix.",
   players={"me1": (0.6, 3.05, True, "Vous"), "op1": (12.6, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Il monte ou il reste", .05), ("Drive ou drop", .2), ("10 balles, objectif 8", .55)]),
   shots=reps(10, .1, .98, (12.6, 3.05), (1.0, 3.0), (0.9, 3.0), [(7.8, 3.0), (11.8, 2.8)], [1, 1, 1, 1, 0, 1, 1, 1, 0, 1], h_feed=80, h_shot=90),
   counter=("Bons choix", 10, "objectif 8")),
 outro="Retenez : au filet, drop. Au fond, drive.")

session(slug="c5-viser-les-pieds", level="confirme", title="Viser les pieds de l'adversaire",
 intro="Niveau confirmé. Aujourd'hui : attaquer bas, dans les pieds.",
 demo=dict(text="Une attaque vers la tête se renvoie facilement. Une attaque dans les pieds oblige l'adversaire à jouer vers le haut, et vous offre la balle suivante. Visez bas, sur la hanche ou sur les lacets.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, None)}, panel=("L'attaque basse", [("Vers la tête : renvoyée", .1), ("Dans les pieds : gênante", .35), ("Il joue vers le haut", .55), ("Balle suivante pour vous", .8)]),
   shots=[shot(.08, .18, (4.5, 3.0), (11.2, 3.2), 70, mark="bad", who="me1"), shot(.4, .5, (4.5, 3.0), (9.1, 3.2), 8, c="red", mark="good", who="me1"), shot(.52, .68, (9.0, 3.2), (5.2, 3.0), 100, who="op1")],
   tags=[(.18, .36, 11.2, 7.0, "Trop haut : renvoyée", "red"), (.5, .7, 9.1, 7.0, "Dans les pieds", "lime"), (.7, 1, 5.2, 7.0, "Balle haute pour vous", "lime")]),
 exo=dict(text="Exercice : votre partenaire vous sert une balle haute à la cuisine. Attaquez dans ses pieds. Dix balles, objectif six attaques basses.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Balle haute", .05), ("Attaque dans les pieds", .2), ("10 balles, objectif 6", .55)]),
   shots=reps(10, .1, .98, (9.0, 3.05), (4.8, 3.0), (4.6, 3.0), [(9.1, 3.1), (9.2, 2.8), (11.4, 3.3), (9.0, 3.4)], [1, 1, 0, 1, 0, 1, 1, 0, 1, 1], h_feed=90, h_shot=8, c="red"),
   counter=("Attaques basses", 10, "objectif 6")),
 outro="Retenez : on attaque bas, jamais à hauteur de raquette.")

session(slug="c6-lob-offensif", level="confirme", title="Le lob offensif, au bon moment",
 intro="Niveau confirmé. Aujourd'hui : le lob offensif.",
 demo=dict(text="Pendant l'échange de dinks, si les adversaires se penchent vers le filet, ils ne peuvent plus reculer vite. Un lob haut et long, côté revers, les oblige à courir en arrière. Ne le jouez pas trop souvent : c'est la surprise qui fait sa force.",
   players={"me1": (4.3, 1.5, True, "Vous"), "op1": (9.0, 4.6, False, None), "op2": (9.0, 1.5, False, None)},
   panel=("Le lob offensif", [("Ils sont penchés au filet", .05), ("Lob haut et long", .3), ("Côté revers", .45), ("Effet de surprise", .78)]),
   shots=[shot(.08, .2, (4.4, 1.6), (7.7, 4.3), 30, who="me1"), shot(.2, .32, (9.0, 4.5), (5.8, 1.7), 30, who="op1"), shot(.36, .7, (4.4, 1.6), (12.6, 1.2), 230, mark="good", who="me1")],
   moves=[mv("op2", .4, .7, (12.0, 1.4))],
   tags=[(.66, .9, 12.4, 7.0, "Il doit courir en arrière", "lime")]),
 exo=dict(text="Exercice : dinkez avec votre partenaire, et glissez un lob quand il s'approche trop du filet. Dix lobs, objectif six au fond du terrain.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Dinks, puis lob", .05), ("Quand il est penché", .2), ("10 lobs, objectif 6", .55)]),
   shots=reps(10, .1, .98, (9.0, 3.05), (5.8, 3.0), (4.4, 3.0), [(12.5, 3.0), (12.2, 2.2), (13.9, 3.4), (12.7, 3.7)], [1, 1, 0, 1, 1, 0, 1, 1, 0, 1], h_feed=30, h_shot=200),
   glows=[(0, 1, DEEP_OP)], counter=("Lobs au fond", 10, "objectif 6")),
 outro="Retenez : haut, long, côté revers, et rarement.")

# AVANCÉ
session(slug="a4-interception", level="avance", title="L'interception au filet",
 intro="Niveau avancé. Aujourd'hui : intercepter la balle de votre partenaire.",
 demo=dict(text="Quand l'adversaire dinke en diagonale vers votre partenaire, vous pouvez traverser et intercepter la balle de volée. Partez au moment où il frappe, attaquez au milieu, et votre partenaire couvre votre côté.",
   players=team(me1=(4.3, 4.6, True, "Vous"), me2=(4.3, 1.5, True, "Partenaire"), op1=(9.0, 4.6, False, None), op2=(9.0, 1.5, False, None)),
   panel=("L'interception", [("Dink en diagonale", .05), ("Partez à sa frappe", .3), ("Volée au milieu", .5), ("Le partenaire couvre", .78)]),
   shots=[shot(.08, .2, (4.4, 1.6), (7.7, 4.3), 30, who="me2"), shot(.3, .42, (8.9, 4.5), (5.6, 1.9), 30, who="op1"), shot(.42, .5, (4.5, 2.6), (9.6, 3.05), 10, c="red", mark="good", who="me1")],
   moves=[mv("me1", .3, .42, (4.4, 2.5)), mv("me2", .44, .6, (4.3, 4.4))],
   tags=[(.42, .62, 4.4, 7.0, "Vous traversez", "lime"), (.62, .9, 4.3, 7.0, "Il couvre votre côté", "normal")]),
 exo=dict(text="Exercice : votre partenaire et un adversaire dinkent en diagonale. Traversez et interceptez au bon moment. Dix essais, objectif six.",
   players=team(me1=(4.3, 4.6, True, "Vous"), me2=(4.3, 1.5, True, "Partenaire"), op1=(9.0, 4.6, False, None), op2=(13.0, 1.5, False, None)),
   panel=("L'exercice", [("Dinks en diagonale", .05), ("On traverse", .2), ("10 essais, objectif 6", .55)]),
   shots=reps(10, .1, .98, (8.9, 4.5), (5.4, 2.2), (4.5, 2.5), [(9.6, 3.05), (9.4, 2.6), (6.6, 3.1)], [1, 1, 0, 1, 1, 0, 1, 1, 0, 1], h_feed=30, h_shot=10, who_feed="op1", c="red"),
   counter=("Interceptions", 10, "objectif 6"), moves=rep_moves(10, .1, .98, "me1", [(.25, .42, (4.4, 2.5))], [(.9, .99, (4.3, 4.6))])),
 outro="Retenez : on part à sa frappe, et le partenaire couvre.")

session(slug="a5-tour-du-poteau", level="avance", title="Le tour du poteau",
 intro="Niveau avancé. Aujourd'hui : le tour du poteau.",
 demo=dict(text="Quand une balle très croisée vous sort du terrain, vous n'êtes pas obligé de passer au-dessus du filet. Vous pouvez la jouer par le côté, autour du poteau, même très bas. C'est légal, tant que la balle retombe dans le terrain adverse.",
   players={"me1": (4.3, 1.5, True, "Vous"), "op1": (9.0, 4.8, False, None), "op2": (9.0, 1.5, False, None)},
   panel=("Le tour du poteau", [("Balle très croisée", .05), ("Vous sortez du terrain", .25), ("Autour du poteau", .5), ("Légal, même très bas", .75)]),
   shots=[shot(.1, .26, (8.9, 4.8), (6.2, 0.35), 30, mark="good", who="op1"), shot(.26, .42, (6.2, 0.35), (6.4, -0.6), 14), shot(.46, .62, (6.4, -0.6), (10.2, 0.9), 6, c="red", mark="good", who="me1")],
   moves=[mv("me1", .12, .42, (6.4, -0.6))],
   tags=[(.24, .44, 6.2, 7.0, "Rebond dans le terrain, puis elle sort", "normal"), (.62, .92, 9.8, 7.0, "Autour du poteau : point", "lime")]),
 exo=dict(text="Exercice : votre partenaire joue un dink très croisé qui vous sort du terrain. Courez et jouez autour du poteau. Dix essais, objectif cinq dans le terrain.",
   players={"me1": (4.3, 1.5, True, "Vous"), "op1": (9.0, 4.8, False, "Partenaire")}, panel=("L'exercice", [("Dink très croisé", .05), ("Autour du poteau", .2), ("10 essais, objectif 5", .55)]),
   shots=atp_reps(10, .1, .98, [(10.2, 0.9), (9.6, 1.6), (11.8, -0.6), (10.8, 0.5)], [1, 0, 1, 1, 0, 1, 0, 1, 1, 0]),
   counter=("Dans le terrain", 10, "objectif 5"), moves=rep_moves(10, .1, .98, "me1", [(.04, .4, (6.4, -0.6))], [(.9, .99, (4.3, 1.5))])),
 outro="Retenez : quand la balle vous sort, passez par le côté.")

session(slug="a6-deplacer-et-finir", level="avance", title="Déplacer, puis finir au centre",
 intro="Niveau avancé. Aujourd'hui : construire le point en dink.",
 demo=dict(text="Ne cherchez pas le coup gagnant tout de suite. Déplacez l'adversaire avec un dink croisé large, puis un dink droit. Il doit courir, et le milieu s'ouvre. C'est là que vous accélérez.",
   players=team(me1=(4.3, 1.5, True, "Vous"), me2=(4.3, 4.6, True, "Partenaire"), op1=(9.0, 4.6, False, None), op2=(9.0, 1.5, False, None)),
   panel=("Construire", [("Pas de gagnant direct", .05), ("Croisé large", .22), ("Puis droit", .42), ("Le milieu s'ouvre", .62), ("On accélère", .82)]),
   shots=[shot(.12, .26, (4.4, 1.6), (7.6, 5.7), 30, who="me1"), shot(.28, .4, (8.9, 5.6), (5.6, 1.8), 30, who="op1"), shot(.42, .56, (4.4, 1.7), (7.7, 0.5), 30, who="me1"),
          shot(.58, .7, (8.9, 0.6), (5.8, 2.0), 50, who="op2"), shot(.78, .86, (4.5, 2.0), (10.2, 3.05), 10, c="red", mark="good", who="me1")],
   moves=[mv("op1", .14, .26, (9.0, 5.6)), mv("op2", .44, .56, (9.0, 0.6))],
   tags=[(.56, .78, 9.4, 7.0, "Le milieu est ouvert", "lime"), (.86, 1, 10.2, 7.0, "Point", "lime")]),
 exo=dict(text="Exercice : enchaînez trois dinks pour déplacer votre partenaire, croisé, droit, croisé, puis accélérez au centre. Dix séquences, objectif six.",
   players={"me1": (4.3, 3.05, True, "Vous"), "op1": (9.0, 3.05, False, "Partenaire")}, panel=("L'exercice", [("Trois dinks", .05), ("Puis accélération", .2), ("10 séquences, objectif 6", .55)]),
   shots=reps(10, .1, .98, (9.0, 3.05), (5.8, 3.0), (4.5, 3.0), [(10.0, 3.05), (9.6, 2.6), (12.0, 3.4)], [1, 1, 0, 1, 1, 0, 1, 1, 0, 1], h_feed=30, h_shot=10, c="red"),
   counter=("Séquences réussies", 10, "objectif 6")),
 outro="Retenez : on déplace, puis on finit au centre.")


# ---------- objectifs des exercices : une réussite tombe dans la zone visée, un raté n'y tombe pas ----------
def _court(x, y): return 0 <= x <= CL and 0 <= y <= CWD
def _kit(x, y): return NET < x <= K2 and 0 <= y <= CWD
OBJ = {
    "d1-service-profond": lambda x, y: _court(x, y) and x >= 11.0,
    "d5-rester-au-fond": lambda x, y: _court(x, y) and x >= 11.0,
    "i1-retour-et-monter": lambda x, y: _court(x, y) and x >= 11.0,
    "i2-le-drop": _kit, "i4-dink-croise": _kit, "c1-dink-patient": _kit, "c2-le-reset": _kit,
    "c5-viser-les-pieds": lambda x, y: 8.8 <= x <= 9.8 and 0 <= y <= CWD,
    "c6-lob-offensif": lambda x, y: _court(x, y) and x >= 11.5,
    "i6-viser-le-milieu": lambda x, y: _court(x, y) and 2.3 <= y <= 3.8 and x > NET,
}
def _fix_marks(ses):
    pred = OBJ.get(ses["slug"], lambda x, y: _court(x, y) and x > NET)
    sc = ses["exo"]; mine = [s for s in sc["shots"] if s["mark"] and s["who"] and sc["players"][s["who"]][2]]
    good = [s["t"] for s in mine if pred(*s["t"])]
    bad = [s["t"] for s in mine if not pred(*s["t"])]
    gi = bi = 0
    for s in mine:
        if s["mark"] == "good":
            if not pred(*s["t"]): s["t"] = good[gi % len(good)]; gi += 1
        else:
            if pred(*s["t"]):
                s["t"] = bad[bi % len(bad)] if bad else (NET - 0.15, s["t"][1]); bi += 1
                if s["t"][0] < NET: s["h"] = min(s["h"], 20)
for _s in S_: _fix_marks(_s)


# Au service (score pair, dont 0-0-2), on sert depuis la moitié DROITE du terrain :
# pour le joueur de gauche qui regarde le filet, c'est le bas de l'écran. On retourne ces séances.
def _flip(sc):
    f = lambda p: (p[0], round(CWD - p[1], 3))
    sc["players"] = {k: (v[0], round(CWD - v[1], 3), v[2], v[3]) for k, v in sc["players"].items()}
    for sh in sc.get("shots", []): sh["f"], sh["t"] = f(sh["f"]), f(sh["t"])
    for m in sc.get("moves", []): m["to"] = f(m["to"])
for _s in S_:
    if _s["slug"] in ("d1-service-profond", "d2-deux-rebonds", "d4-annoncer-le-score", "d5-rester-au-fond", "a1-stacking"):
        _flip(_s["demo"]); _flip(_s["exo"])


# ---------- drawing ----------
def ppos(sc, name, u):
    x, y, me, lab = sc["players"][name]
    for m in sc.get("moves", []):
        if m["who"] != name: continue
        a, b = m["u"]
        if u >= b: x, y = m["to"]
        elif u > a: k = ease((u - a) / (b - a)); x, y = lerp(x, m["to"][0], k), lerp(y, m["to"][1], k)
    return x, y, me, lab


def paddle(p, px, py, me, swing):
    d = 1 if me else -1
    ang = math.radians((-35 + 85 * swing) * d)
    cx, cy = px + d * 22 + d * 6 * math.cos(ang), py - 2 - 8 * math.sin(ang)
    dx, dy = math.cos(ang) * d, -math.sin(ang)
    nx, ny = -dy, dx
    hw, hh = 7, 11
    pts = [(cx + dx * hh + nx * hw, cy + dy * hh + ny * hw), (cx + dx * hh - nx * hw, cy + dy * hh - ny * hw),
           (cx - dx * hh - nx * hw, cy - dy * hh - ny * hw), (cx - dx * hh + nx * hw, cy - dy * hh + ny * hw)]
    p.line([(cx - dx * hh, cy - dy * hh), (cx - dx * (hh + 7), cy - dy * (hh + 7))], INK, 3)
    p.poly(pts, (240, 120, 40) if me else (70, 80, 100)); p.line(pts + pts[:1], INK, 1.6)


def draw_court_scene(p, sc, t, D, counter_mode):
    u = t / D
    zone_alpha = {}
    court(p, 0, True)
    for a, b, z in sc.get("glows", []):
        g = seg(u, a, a + .04) * (1 - seg(u, b - .02, b)) if b < 1 else seg(u, a, a + .04)
        if g > 0:
            p.rect(R.CX + z[0] * R.M, R.CY, (z[1] - z[0]) * R.M, CWD * R.M, fill=BALL + (int(90 * g),))
    # marks
    n = 0
    for s in sc["shots"]:
        a, b = s["u"]
        if s["mark"] and u >= b:
            keep = 0.12 if counter_mode else 0.3
            if u < b + keep: bounce_mark(p, *s["t"], s["mark"] == "good", 1 - seg(u, b + keep * .6, b + keep))
        if s["n"] and u >= b: n += 1
    # players and paddles
    for name in sc["players"]:
        x, y, me, lab = ppos(sc, name, u)
        sw = 0.0
        for s in sc["shots"]:
            if s["who"] == name:
                dt = t - s["u"][0] * D
                if -0.25 < dt < 0.3: sw = max(sw, 1 - abs(dt) / 0.3)
        px, py = P(x, y)
        R.player(p, x, y, me, lab if u < 0.45 or not counter_mode else lab)
        paddle(p, px, py, me, sw)
        for a, b, who, txt in sc.get("bubbles", []):
            if who == name and a <= u < b:
                w = p.tw(txt, FT["lab"]) + 24
                p.rect(px - w / 2, py - 84, w, 34, fill=WHITE, outline=INK, width=2, r=14)
                p.poly([(px - 8, py - 51), (px + 8, py - 51), (px, py - 40)], WHITE)
                p.text(px, py - 67, txt, FT["lab"], INK, "mm")
    if sc.get("call"):
        for s in sc["shots"]:
            if s["who"] == "op1" and s["u"][0] <= u < s["u"][1]:
                x, y, _, _ = ppos(sc, "me1", u); px, py = P(x, y)
                p.rect(px - 40, py - 84, 80, 34, fill=WHITE, outline=INK, width=2, r=14); p.text(px, py - 67, "J'ai !", FT["lab"], INK, "mm")
    # balls in flight
    for s in sc["shots"]:
        a, b = s["u"]
        if a <= u < b:
            col = RED if s["c"] == "red" or (sc.get("feed_red") and s["who"] == "op1") else BALL
            ball_at(p, *s["f"], *s["t"], (u - a) / (b - a), s["h"], True, col)
    for a, b, x, y, txt, kind in sc.get("tags", []):
        al = seg(u, a, a + .03) * (1 - seg(u, b - .02, b)) if b < 1 else seg(u, a, a + .03)
        bg = {"red": (160, 40, 30), "lime": (40, 70, 10), "normal": (10, 20, 40)}[kind]
        tag(p, *P(x, y), txt, al, WHITE, bg)
    R.panel(p, *sc["panel"], u)
    if "counter" in sc:
        lab, tot, goal = sc["counter"]
        p.rect(R.PX, 440, 300, 104, fill=WHITE, outline=(225, 231, 240), width=2, r=16)
        p.text(R.PX + 20, 452, lab, FT["small"], (85, 101, 124))
        p.text(R.PX + 20, 476, f"{n} / {tot}", FT["big"], COURT)
        p.text(R.PX + 280, 496, goal, FT["lab"], (85, 101, 124), "ra")


def header(p, ses):
    lab, col = LEVELS[ses["level"]]
    R.header(p, "")
    p.rect(0, 0, W, 64, fill=WHITE)
    p.rect(24, 14, 36, 36, fill=COURT, r=9); p.circle(42, 34, 9, fill=BALL); p.rect(30, 38, 24, 5, fill=WHITE, r=2)
    p.text(72, 20, "Pickleball", FT["chip"], INK); p.text(72 + p.tw("Pickleball ", FT["chip"]), 20, "du Jour", FT["chip"], COURT)
    w = p.tw(lab, FT["small"]) + 24
    p.rect(W - 24 - w, 18, w, 28, fill=col, r=14); p.text(W - 24 - w / 2, 32, lab, FT["small"], WHITE, "mm")
    p.text(W - 36 - w, 21, ses["title"], FT["small"], (85, 101, 124), "ra")


def card(p, ses, t, D, outro=False):
    lab, col = LEVELS[ses["level"]]
    p.rect(0, 0, W, H, fill=col if not outro else DEEP)
    for i in range(6): p.line([(0, 140 + i * 90), (W, 140 + i * 90)], (255, 255, 255, 16), 2)
    if not outro:
        a, b = seg(t, 0.05, 0.6), seg(t, 0.3, 0.9)
        p.text(96, 200 + 16 * (1 - a), f"NIVEAU {lab.upper()}", FT["chip"], BALL + (int(255 * a),))
        words = ses["title"].split(); l1, l2 = [], []
        for w_ in words: (l1 if p.tw(" ".join(l1 + [w_]), FT["h1"]) < 700 and not l2 else l2).append(w_)
        p.text(96, 250 + 16 * (1 - b), " ".join(l1), FT["h1"], WHITE + (int(255 * b),))
        if l2: p.text(96, 318 + 16 * (1 - b), " ".join(l2), FT["h1"], WHITE + (int(255 * b),))
        thumb_court(p, 860, 220, 340, ses, t)
    else:
        a = seg(t, 0.1, 0.6)
        p.text(96, 230, "À retenir", FT["h1"], BALL + (int(255 * a),))
        p.text(96, 320, ses["outro"].replace("Retenez : ", "").capitalize(), FT["h2"], WHITE + (int(255 * a),))
        p.text(96, 420, "pickleballdujour.fr/progresser", FT["chip"], SOFT + (int(255 * seg(t, 0.8, 1.3)),))


def thumb_court(p, x, y, w, ses, t=None):
    h = w * 0.62
    p.rect(x - 14, y - 14, w + 28, h + 28, fill=GRASS, r=18)
    p.rect(x, y, w, h, fill=COURT)
    k = w / CL
    p.rect(x + K1 * k, y, (K2 - K1) * k, h, fill=KIT)
    p.rect(x, y, w, h, outline=WHITE, width=3)
    for xx in (K1, K2): p.line([(x + xx * k, y), (x + xx * k, y + h)], WHITE, 2)
    p.line([(x + NET * k, y - 8), (x + NET * k, y + h + 8)], (235, 240, 248), 5)
    u = 0.5 if t is None else (t * 0.45) % 1
    x0, x1 = x + 1.0 * k, x + 7.8 * k; yy = y + h * 0.55
    for i in range(16):
        v = u * i / 16
        p.circle(lerp(x0, x1, v), yy - 4 * h * 0.55 * v * (1 - v), 2.4, fill=BALL + (170,))
    p.circle(lerp(x0, x1, u), yy - 4 * h * 0.55 * u * (1 - u), 11, fill=BALL, outline=INK, width=2)
    p.circle(x0 - 6, yy + 6, 12, fill=BALL, outline=INK, width=2); p.circle(x + 11.6 * k, y + h * 0.35, 12, fill=WHITE, outline=INK, width=2)


def thumbnail(ses, dur, path):
    lab, col = LEVELS[ses["level"]]
    img = Image.new("RGB", (W * S, H * S), col); p = Pen(img)
    for i in range(7): p.line([(0, 90 + i * 100), (W, 90 + i * 100)], (255, 255, 255, 14), 2)
    # big decorative ball, top right
    bx, by, br = 1170, 70, 190
    p.circle(bx, by, br, fill=BALL)
    for dx, dy in [(-.45, .2), (-.1, .55), (.3, .35), (-.55, .62), (.05, .15), (.45, .7)]:
        p.circle(bx + dx * br, by + dy * br, br * .09, fill=(180, 205, 30))
    p.rect(718, 246, 494, 316, fill=(0, 0, 0, 55), r=22)
    p.rect(56, 56, 52, 52, fill=WHITE, r=13); p.circle(82, 84, 13, fill=BALL); p.rect(66, 90, 32, 6, fill=COURT, r=3)
    p.text(124, 66, "Pickleball du Jour", FT["chip"], WHITE)
    w = p.tw(f"NIVEAU {lab.upper()}", FT["chip"]) + 36
    p.rect(56, 170, w, 48, fill=BALL, r=24); p.text(56 + w / 2, 194, f"NIVEAU {lab.upper()}", FT["chip"], INK, "mm")
    words = ses["title"].split()
    for size in (76, 66, 58):
        big = R.F("Archivo-800.ttf", size); lines = [""]
        for w_ in words:
            tt = (lines[-1] + " " + w_).strip()
            if p.tw(tt, big) > 600 and lines[-1]: lines.append(w_)
            else: lines[-1] = tt
        if len(lines) <= 3: break
    for i, l in enumerate(lines[:3]): p.text(56, 250 + i * int(size * 1.13), l, big, WHITE)
    p.rect(56, H - 110, 224, 54, fill=(0, 0, 0, 70), r=27)
    p.poly([(82, H - 96), (82, H - 70), (104, H - 83)], WHITE)
    p.text(118, H - 83, f"{int(round(dur))} secondes", FT["chip"], WHITE, "lm")
    thumb_court(p, 730, 230, 470, ses, None)
    img.resize((W, H), Image.LANCZOS).save(path, quality=90)


# ---------- audio + build ----------
VOICE_FIX = [(r"\bresets\b", "rissètes"), (r"\breset\b", "rissète"), (r"\bsmash\b", "smatch"), (r"\bdinker\b", "dinnké"), (r"\bdinke\b", "dinnk"), (r"\bdinkent\b", "dinnk"), (r"\bdinkez\b", "dinnké"),
             (r"\bdinks\b", "dinnk"), (r"\bdink\b", "dinnk"), (r"\bdrops\b", "drop"), (r"\bdrive\b", "draïve"), (r"\bstacking\b", "stakinng"), (r"\berne\b", "eurne"),
             (r"\blob\b", "lobe"), (r"\blobs\b", "lobes"), (r"0-0-2", "zéro, zéro, deux"), (r"\s*:\s*", ", ")]
_KK = None
def voice_text(t):
    import re
    for a, b in VOICE_FIX: t = re.sub(a, b, t, flags=re.I)
    return t

def sentences(text):
    import re
    return [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]

PAUSE = 0.32
def tts(text, path):
    """Synthèse phrase par phrase (Kokoro, voix ff_siwis) ; renvoie la durée et le minutage de chaque phrase."""
    import json, soundfile as sf
    meta = path + ".json"
    if not (os.path.exists(path) and os.path.exists(meta)):
        global _KK
        if _KK is None:
            sys.path.insert(0, ROOT); import tts_kk as _m; _KK = _m
        rate = None; buf = []; t = 0.0; timing = []
        for sen in sentences(text):
            a = _KK.tts.generate(voice_text(sen), sid=30, speed=1.0)
            rate = a.sample_rate; x = np.asarray(a.samples, np.float32)
            nz = np.where(np.abs(x) > 0.01)[0]
            if len(nz): x = x[max(0, nz[0] - int(.03 * rate)): nz[-1] + int(.06 * rate)]
            timing.append((t, t + len(x) / rate, sen)); buf += [x, np.zeros(int(PAUSE * rate), np.float32)]; t += len(x) / rate + PAUSE
        y = np.concatenate(buf[:-1]); y = y / max(1e-6, np.abs(y).max()) * 0.89
        sf.write(path, y, rate, subtype="PCM_16")
        json.dump(timing, open(meta, "w"), ensure_ascii=False)
    import json
    with wave.open(path) as w: dur = w.getnframes() / w.getframerate()
    return dur, json.load(open(meta))


def plan(ses):
    d = os.path.join(OUT, ses["slug"]); os.makedirs(d, exist_ok=True)
    parts = [("intro", ses["intro"]), ("demo", ses["demo"]["text"]), ("exo", ses["exo"]["text"]), ("outro", ses["outro"])]
    scenes = []
    for k, (kind, text) in enumerate(parts):
        wav = os.path.join(d, f"{k}-{kind}.kk.wav"); dur, timing = tts(text, wav)
        extra = {"intro": 1.0, "demo": 1.9, "exo": 2.6, "outro": 1.4}[kind]
        D = math.ceil((LEAD + dur + extra) * FPS) / FPS
        subs = []
        for a, b, sen in timing:
            cs = chunks(sen); tot = sum(len(c) for c in cs); t0 = LEAD + a
            for c in cs: dd = (b - a) * len(c) / tot; subs.append((t0, t0 + dd + (PAUSE * .8 if c == cs[-1] else 0), c)); t0 += dd
        scenes.append(dict(kind=kind, D=D, wav=wav, subs=subs))
    return d, scenes


def vtt(scenes, path):
    def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); return f"{h:02d}:{m:02d}:{x % 60:06.3f}"
    off = 0.0; out = ["WEBVTT", ""]; i = 0
    for sc in scenes:
        for a, b, c in sc["subs"]:
            i += 1; out += [str(i), f"{ts(off + a)} --> {ts(off + min(b, sc['D']))}", c[:1].upper() + c[1:], ""]
        off += sc["D"]
    open(path, "w").write("\n".join(out))


def frame(ses, sc, t):
    img = Image.new("RGB", (W * S, H * S), (236, 243, 252)); p = Pen(img)
    if sc["kind"] == "intro": card(p, ses, t, sc["D"])
    elif sc["kind"] == "outro": card(p, ses, t, sc["D"], True)
    else:
        header(p, ses); draw_court_scene(p, ses[sc["kind"]], t, sc["D"], sc["kind"] == "exo")
    cur = next((s for (a, b, s) in sc["subs"] if a <= t < b), "")
    subtitle(p, cur[:1].upper() + cur[1:])
    return img.resize((W, H), Image.LANCZOS)


def build(ses):
    d, scenes = plan(ses)
    files = []
    for k, sc in enumerate(scenes):
        tmp, fin = os.path.join(d, f"s{k}.tmp.mp4"), os.path.join(d, f"s{k}.mp4")
        n = int(round(sc["D"] * FPS))
        pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for i in range(n): pr.stdin.write(frame(ses, sc, i / FPS).tobytes())
        pr.stdin.close()
        if pr.wait() == 0: os.replace(tmp, fin)
        files.append(fin)
    with open(os.path.join(d, "list.txt"), "w") as f: f.write("".join(f"file '{x}'\n" for x in files))
    rate = 22050; parts = []
    for sc in scenes:
        with wave.open(sc["wav"]) as w: rate = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        lead = np.zeros(int(LEAD * rate), np.int16); tail = np.zeros(int(round(sc["D"] * rate)) - len(lead) - len(a), np.int16)
        parts += [lead, a, tail]
    with wave.open(os.path.join(d, "voice.wav"), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(np.concatenate(parts).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(d, "list.txt"), "-c", "copy", os.path.join(d, "video.mp4")], check=True)
    final = os.path.join(OUT, ses["slug"] + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(d, "video.mp4"), "-i", os.path.join(d, "voice.wav"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", final], check=True)
    total = sum(s["D"] for s in scenes)
    vtt(scenes, os.path.join(OUT, ses["slug"] + ".vtt"))
    thumbnail(ses, total, os.path.join(OUT, ses["slug"] + ".jpg"))
    return total


if __name__ == "__main__":
    mode = sys.argv[1]; pick = sys.argv[2:]
    todo = [s for s in S_ if not pick or s["slug"] in pick]
    os.makedirs(OUT, exist_ok=True)
    if mode == "plan":
        for s in todo:
            d, scs = plan(s); print(s["slug"], round(sum(x["D"] for x in scs), 1))
    elif mode == "frames":
        for s in todo:
            d, scs = plan(s)
            for sc in scs[1:3]:
                for f in (0.3, 0.75): frame(s, sc, sc["D"] * f).save(os.path.join(OUT, f"k_{s['slug']}_{sc['kind']}_{int(f*100)}.png"))
            thumbnail(s, sum(x["D"] for x in scs), os.path.join(OUT, s["slug"] + ".jpg"))
        print("ok")
    elif mode == "render":
        for s in todo: print(s["slug"], round(build(s), 1), flush=True)
