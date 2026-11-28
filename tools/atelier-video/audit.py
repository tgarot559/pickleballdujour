"""Contrôle automatique des séances : règles du pickleball et cohérence des animations.
Usage : python3 audit.py [slug ...]  -> liste des problèmes par séance."""
import sys, math
import sessions as S
from render import CL, CWD, NET, K1, K2

MID = CWD / 2
FLIPPED = {"d1-service-profond", "d2-deux-rebonds", "d4-annoncer-le-score", "d5-rester-au-fond", "a1-stacking"}
SERVES = {"d1-service-profond", "d2-deux-rebonds", "d4-annoncer-le-score", "d5-rester-au-fond", "a1-stacking", "i1-retour-et-monter"}


def side(x):
    return "me" if x < NET else "op"


def in_court(x, y, tol=0.0):
    return -tol <= x <= CL + tol and -tol <= y <= CWD + tol


def in_kitchen(x, y):
    return 0 <= y <= CWD and K1 < x < K2


def ppos(sc, name, u):
    x, y, me, lab = sc["players"][name]
    for m in sc.get("moves", []):
        if m["who"] != name:
            continue
        a, b = m["u"]
        if u >= b:
            x, y = m["to"]
        elif u > a:
            k = (u - a) / (b - a)
            x, y = x + (m["to"][0] - x) * k, y + (m["to"][1] - y) * k
    return x, y


def audit_scene(ses, kind, sc):
    out = []
    shots = sorted(sc["shots"], key=lambda s: s["u"][0])
    for i, s in enumerate(shots):
        (fx, fy), (tx, ty), who = s["f"], s["t"], s["who"]
        tag = f"{kind} coup {i + 1} ({who or 'rebond'})"
        if who is None:
            continue  # trajectoire après rebond
        # 1. le coup doit traverser le filet
        if side(fx) == side(tx) and not (s["mark"] == "bad" and abs(tx - NET) < 0.35):
            out.append(f"{tag} : la balle ne passe pas le filet ({fx:.1f} → {tx:.1f})")
        # 2. le joueur doit être là où part la balle
        if who in sc["players"]:
            px, py = ppos(sc, who, s["u"][0])
            d = math.hypot(px - fx, py - fy)
            if d > 0.8:
                out.append(f"{tag} : le joueur est à {d:.1f} m du point de frappe (joueur {px:.1f},{py:.1f} / frappe {fx:.1f},{fy:.1f})")
            # 3. le joueur doit être de son côté
            me = sc["players"][who][2]
            if (me and px > NET) or (not me and px < NET):
                out.append(f"{tag} : le joueur frappe depuis le camp adverse")
            # 4. volée dans la cuisine (à revoir : autorisée seulement après rebond)
            if in_kitchen(px, py):
                prev = shots[i - 1] if i else None
                bounced = prev is not None and (prev["mark"] or prev["who"] is None)
                if not bounced:
                    out.append(f"{tag} : frappe depuis la cuisine sans rebond visible avant (faute si c'est une volée)")
        # 5. marques bonne / mauvaise cohérentes avec la zone d'arrivée
        mine = who in sc["players"] and sc["players"][who][2]
        if kind == "exo" and mine and s["mark"]:
            pred = S.OBJ.get(ses["slug"], lambda x, y: S._court(x, y) and x > NET)
            yy = CWD - ty if ses["slug"] in FLIPPED else ty
            if s["mark"] == "good" and not pred(tx, yy):
                out.append(f"{tag} : comptée réussie mais tombe hors de la zone visée ({tx:.1f},{ty:.1f})")
            if s["mark"] == "bad" and pred(tx, yy):
                out.append(f"{tag} : comptée ratée alors qu'elle tombe dans la zone visée ({tx:.1f},{ty:.1f})")
        elif s["mark"] == "good" and not in_court(tx, ty):
            out.append(f"{tag} : marquée bonne mais tombe hors du terrain ({tx:.1f},{ty:.1f})")
        # 6. arrivée hors du terrain sans marque = balle qui sort et qu'on joue quand même
        if not s["mark"] and not in_court(tx, ty, 0.15):
            nxt = shots[i + 1] if i + 1 < len(shots) else None
            if nxt and nxt["who"] and math.hypot(nxt["f"][0] - tx, nxt["f"][1] - ty) < 0.8 and not ses["slug"].startswith("a2"):
                out.append(f"{tag} : la balle va hors du terrain et est rejouée (volée hors du terrain ? à confirmer)")
    # 7. service : derrière la ligne, en diagonale, au-delà de la cuisine
    for i, s in enumerate(shots):
        if s["who"] is None:
            continue
        fx, fy = s["f"]
        if (fx < 0.0 or fx > CL) and i == 0 and ses["slug"] in SERVES:
            tx, ty = s["t"]
            if (fy - MID) * (ty - MID) > 0:
                out.append(f"{kind} service : pas en diagonale")
            beyond = tx > K2 if fx < NET else tx < K1
            if s["mark"] == "good" and not beyond:
                out.append(f"{kind} service : marqué bon mais tombe dans la cuisine")
    # 8. joueurs placés loin du terrain
    for name, (x, y, me, lab) in sc["players"].items():
        if not in_court(x, y, 1.2):
            out.append(f"{kind} : joueur {name} très loin du terrain ({x:.1f},{y:.1f})")
        if (me and x > NET) or (not me and x < NET):
            out.append(f"{kind} : joueur {name} placé dans le mauvais camp")
    # 9. déplacements qui traversent la cuisine dans une séance où on n'a pas le droit d'y entrer
    if ses["slug"].startswith("a2"):
        for m in sc.get("moves", []):
            pass
    return out


def audit(ses):
    probs = []
    for kind in ("demo", "exo"):
        probs += audit_scene(ses, kind, ses[kind])
    return probs


if __name__ == "__main__":
    pick = sys.argv[1:]
    tot = 0
    for s in S.S_:
        if pick and s["slug"] not in pick:
            continue
        p = audit(s)
        tot += len(p)
        print(f"\n## {s['slug']} — {len(p)} point(s)")
        for x in p:
            print(" -", x)
    print(f"\nTotal : {tot}")
