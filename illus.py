"""Original SVG illustrations for Pickleball du Jour (no third-party images)."""

L = {
 "fr": {"kitchen": "Cuisine (zone de non-volée)", "net": "Filet", "base": "Ligne de fond", "side": "Ligne de côté",
        "svc_r": "Zone de service droite", "svc_l": "Zone de service gauche", "center": "Ligne centrale",
        "face": "Tamis", "core": "Noyau", "edge": "Protection de bord", "grip": "Manche (grip)", "sweet": "Zone idéale de frappe",
        "server": "Serveur", "target": "Zone visée", "nvz": "Cuisine interdite au service"},
 "en": {"kitchen": "Kitchen (non-volley zone)", "net": "Net", "base": "Baseline", "side": "Sideline",
        "svc_r": "Right service court", "svc_l": "Left service court", "center": "Centerline",
        "face": "Face", "core": "Core", "edge": "Edge guard", "grip": "Handle (grip)", "sweet": "Sweet spot",
        "server": "Server", "target": "Target court", "nvz": "Kitchen is out on the serve"},
}

FONT = "font-family:Inter,system-ui,sans-serif"


def court_svg(lang="fr"):
    t = L[lang]
    s = 60  # px per metre
    W, H = 13.41 * s, 6.10 * s
    ox, oy = 70, 60
    k = 2.13 * s
    x_net = ox + W / 2
    out = [f'<svg viewBox="0 0 {W+140:.0f} {H+150:.0f}" role="img" aria-label="{t["kitchen"]}" style="{FONT}">']
    out.append(f'<rect x="{ox-30}" y="{oy-30}" width="{W+60}" height="{H+60}" rx="10" fill="#2a8a57"/>')
    out.append(f'<rect x="{ox}" y="{oy}" width="{W}" height="{H}" fill="#1f5fbf"/>')
    out.append(f'<rect x="{x_net-k}" y="{oy}" width="{2*k}" height="{H}" fill="#2f74d6"/>')
    st = 'stroke="#fff" stroke-width="4" fill="none"'
    out.append(f'<rect x="{ox}" y="{oy}" width="{W}" height="{H}" {st}/>')
    out.append(f'<line x1="{x_net-k}" y1="{oy}" x2="{x_net-k}" y2="{oy+H}" {st}/>')
    out.append(f'<line x1="{x_net+k}" y1="{oy}" x2="{x_net+k}" y2="{oy+H}" {st}/>')
    out.append(f'<line x1="{ox}" y1="{oy+H/2}" x2="{x_net-k}" y2="{oy+H/2}" {st}/>')
    out.append(f'<line x1="{x_net+k}" y1="{oy+H/2}" x2="{ox+W}" y2="{oy+H/2}" {st}/>')
    out.append(f'<line x1="{x_net}" y1="{oy-18}" x2="{x_net}" y2="{oy+H+18}" stroke="#0f1c2e" stroke-width="6" stroke-dasharray="3 5"/>')
    tx = 'fill="#fff" font-size="17" font-weight="700" text-anchor="middle" style="paint-order:stroke;stroke:#1f5fbf;stroke-width:5px"'
    out.append(f'<text x="{x_net}" y="{oy+H/2-8}" {tx}>{t["kitchen"].split(" (")[0]}</text>')
    out.append(f'<text x="{x_net}" y="{oy+H/2+14}" fill="#e6eeff" font-size="13" text-anchor="middle">2,13 m + 2,13 m</text>' if lang == "fr" else f'<text x="{x_net}" y="{oy+H/2+14}" fill="#e6eeff" font-size="13" text-anchor="middle">7 ft + 7 ft</text>')
    q = (x_net - k - ox) / 2
    out.append(f'<text x="{ox+q}" y="{oy+H/4+6}" {tx}>{t["svc_l"] if lang=="fr" else t["svc_l"]}</text>')
    out.append(f'<text x="{ox+q}" y="{oy+3*H/4+6}" {tx}>{t["svc_r"]}</text>')
    out.append(f'<text x="{ox+W-q}" y="{oy+H/4+6}" {tx}>{t["svc_r"]}</text>')
    out.append(f'<text x="{ox+W-q}" y="{oy+3*H/4+6}" {tx}>{t["svc_l"]}</text>')
    dim = 'fill="#fff" font-size="16" font-weight="700" text-anchor="middle"'
    L1 = "13,41 m" if lang == "fr" else "44 ft (13.41 m)"
    L2 = "6,10 m" if lang == "fr" else "20 ft (6.10 m)"
    out.append(f'<line x1="{ox}" y1="{oy+H+48}" x2="{ox+W}" y2="{oy+H+48}" stroke="#fff" stroke-width="2"/>')
    out.append(f'<text x="{ox+W/2}" y="{oy+H+74}" {dim}>{L1}</text>')
    out.append(f'<line x1="{ox-48}" y1="{oy}" x2="{ox-48}" y2="{oy+H}" stroke="#fff" stroke-width="2"/>')
    out.append(f'<text x="{ox-56}" y="{oy+H/2}" {dim} transform="rotate(-90 {ox-56} {oy+H/2})">{L2}</text>')
    out.append(f'<text x="{x_net}" y="{oy-38}" fill="#fff" font-size="15" text-anchor="middle">{t["net"]} · 86 cm / 91 cm</text>' if lang == "fr" else f'<text x="{x_net}" y="{oy-38}" fill="#fff" font-size="15" text-anchor="middle">{t["net"]} · 34 in centre / 36 in posts</text>')
    out.append('</svg>')
    return "".join(out)


def hero_svg():
    """Perspective court, ball arcing over the net."""
    return '''<svg class="court" viewBox="0 0 560 420" role="img" aria-label="Terrain de pickleball vu en perspective">
<defs><linearGradient id="g1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2f74d6"/><stop offset="1" stop-color="#1a4fa3"/></linearGradient></defs>
<polygon points="150,70 410,70 540,390 20,390" fill="#2a8a57"/>
<polygon points="175,92 385,92 500,370 60,370" fill="url(#g1)"/>
<polygon points="128,205 432,205 459,270 101,270" fill="#3b82e6" opacity=".55"/>
<g stroke="#fff" stroke-width="4" fill="none" stroke-linejoin="round">
<polygon points="175,92 385,92 500,370 60,370"/>
<line x1="128" y1="205" x2="432" y2="205"/><line x1="101" y1="270" x2="459" y2="270"/>
<line x1="280" y1="92" x2="280" y2="205"/><line x1="280" y1="270" x2="280" y2="370"/>
</g>
<rect x="108" y="226" width="344" height="18" fill="#0f1c2e" opacity=".85"/>
<g stroke="#0f1c2e" stroke-width="1.5" opacity=".5">
<line x1="120" y1="226" x2="120" y2="244"/><line x1="160" y1="226" x2="160" y2="244"/><line x1="200" y1="226" x2="200" y2="244"/><line x1="240" y1="226" x2="240" y2="244"/><line x1="320" y1="226" x2="320" y2="244"/><line x1="360" y1="226" x2="360" y2="244"/><line x1="400" y1="226" x2="400" y2="244"/><line x1="440" y1="226" x2="440" y2="244"/></g>
<rect x="104" y="218" width="8" height="36" fill="#e9eef6"/><rect x="448" y="218" width="8" height="36" fill="#e9eef6"/>
<path d="M210 340 Q 300 120 360 150" stroke="#d6f03f" stroke-width="3" stroke-dasharray="2 9" fill="none" stroke-linecap="round"/>
<g class="ballarc"><circle cx="360" cy="150" r="17" fill="#d6f03f"/><circle cx="360" cy="150" r="17" fill="none" stroke="#a9c21a" stroke-width="2"/>
<g fill="#a9c21a"><circle cx="353" cy="144" r="2.6"/><circle cx="364" cy="142" r="2.6"/><circle cx="369" cy="152" r="2.6"/><circle cx="356" cy="156" r="2.6"/><circle cx="361" cy="160" r="2.2"/><circle cx="350" cy="151" r="2.2"/></g></g>
<ellipse cx="300" cy="300" rx="16" ry="5" fill="#0f1c2e" opacity=".25"/>
<g transform="translate(184 318) rotate(-28)"><rect x="-22" y="-34" width="44" height="58" rx="18" fill="#0f1c2e"/><rect x="-18" y="-30" width="36" height="50" rx="15" fill="#f4f6fb"/><rect x="-5" y="22" width="10" height="34" rx="4" fill="#0f1c2e"/></g>
</svg>'''


def paddle_svg(lang="fr"):
    t = L[lang]
    return f'''<svg viewBox="0 0 640 366" role="img" aria-label="{t['face']}" style="{FONT}">
<g transform="translate(150 30)">
<rect x="0" y="0" width="200" height="230" rx="70" fill="#0f1c2e"/>
<rect x="8" y="8" width="184" height="214" rx="64" fill="#e9eef6"/>
<ellipse cx="100" cy="100" rx="52" ry="58" fill="#d6f03f" opacity=".85"/>
<rect x="78" y="222" width="44" height="100" rx="12" fill="#0f1c2e"/>
<g stroke="#2a3a52" stroke-width="2" opacity=".6"><line x1="80" y1="245" x2="120" y2="240"/><line x1="80" y1="265" x2="120" y2="260"/><line x1="80" y1="285" x2="120" y2="280"/><line x1="80" y1="305" x2="120" y2="300"/></g>
</g>
<g fill="#fff" font-size="16" font-weight="600">
<line x1="250" y1="130" x2="420" y2="90" stroke="#fff" stroke-width="2"/><text x="428" y="95">{t['sweet']}</text>
<line x1="330" y1="70" x2="420" y2="40" stroke="#fff" stroke-width="2"/><text x="428" y="45">{t['edge']}</text>
<line x1="320" y1="200" x2="420" y2="160" stroke="#fff" stroke-width="2"/><text x="428" y="165">{t['face']}</text>
<line x1="272" y1="310" x2="420" y2="300" stroke="#fff" stroke-width="2"/><text x="428" y="305">{t['grip']}</text>
</g>
<g fill="#e6eeff" font-size="14"><text x="20" y="352">{'≈ 40 cm × 20 cm · 200 à 250 g' if lang=='fr' else '≈ 16 in × 8 in · 7 to 9 oz'}</text></g>
</svg>'''


def serve_svg(lang="fr"):
    t = L[lang]
    s = 40
    W, H = 13.41 * s, 6.10 * s
    ox, oy = 30, 30
    k = 2.13 * s
    xn = ox + W / 2
    st = 'stroke="#fff" stroke-width="3" fill="none"'
    return f'''<svg viewBox="0 0 {W+60:.0f} {H+90:.0f}" role="img" aria-label="{t['server']}" style="{FONT}">
<rect x="{ox}" y="{oy}" width="{W}" height="{H}" fill="#1f5fbf"/>
<rect x="{xn+k}" y="{oy}" width="{ox+W-xn-k}" height="{H/2}" fill="#d6f03f" opacity=".45"/>
<rect x="{xn-k}" y="{oy}" width="{2*k}" height="{H}" fill="#e2574c" opacity=".55"/>
<rect x="{ox}" y="{oy}" width="{W}" height="{H}" {st}/>
<line x1="{xn-k}" y1="{oy}" x2="{xn-k}" y2="{oy+H}" {st}/><line x1="{xn+k}" y1="{oy}" x2="{xn+k}" y2="{oy+H}" {st}/>
<line x1="{ox}" y1="{oy+H/2}" x2="{xn-k}" y2="{oy+H/2}" {st}/><line x1="{xn+k}" y1="{oy+H/2}" x2="{ox+W}" y2="{oy+H/2}" {st}/>
<line x1="{xn}" y1="{oy-10}" x2="{xn}" y2="{oy+H+10}" stroke="#0f1c2e" stroke-width="5"/>
<circle cx="{ox-8}" cy="{oy+H*0.75}" r="11" fill="#0f1c2e" stroke="#fff" stroke-width="2"/>
<path d="M{ox+4} {oy+H*0.75} Q {xn} {oy-30} {ox+W-60} {oy+H*0.25}" stroke="#d6f03f" stroke-width="3" stroke-dasharray="3 7" fill="none"/>
<circle cx="{ox+W-60}" cy="{oy+H*0.25}" r="8" fill="#d6f03f"/>
<g font-size="14" font-weight="700" fill="#fff">
<text x="{ox}" y="{oy+H+30}">● {t['server']}</text>
<text x="{ox+150}" y="{oy+H+30}" fill="#d6f03f">■ {t['target']}</text>
<text x="{ox+300}" y="{oy+H+30}" fill="#ffb3ac">■ {t['nvz']}</text>
</g></svg>'''
