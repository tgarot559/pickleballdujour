#!/usr/bin/env python3
"""Static site generator for pickleballdujour.fr (FR + EN)."""
import json, os, shutil, html, datetime, sys
sys.path.insert(0, os.path.dirname(__file__))
from illus import court_svg, hero_svg, paddle_svg, serve_svg
from content.pages_fr import PAGES as PFR
from content.tips_fr import TIPS as TFR
from content.pages_en import PAGES as PEN
from content.tips_en import TIPS as TEN
from content.extra import EXTRA, TOURNEYS

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
SITE = "https://pickleballdujour.fr"
LAUNCH = datetime.date(2026, 11, 27)
TODAY = datetime.date.today()
AUTHOR = {"@type": "Person", "name": "Thierry Garot", "url": "https://thierrygarot.fr/", "sameAs": ["https://www.linkedin.com/in/thierry-garot"]}

T = {
 "fr": {"name": "Pickleball du Jour", "lang": "fr", "home": "/", "tips": "conseils", "tips_t": "Conseils", "tip_of_day": "Le conseil du jour",
        "nav": [("Débuter", "/debuter-au-pickleball/"), ("Règles", "/regles-du-pickleball/"), ("Raquettes", "/choisir-raquette-pickleball/"), ("Tournois", "/tournois-pickleball/"), ("Monde", "/pickleball-dans-le-monde/"), ("Conseils", "/conseils/")],
        "news": "/newsletter/", "news_t": "Newsletter", "other": "EN", "faq": "Questions fréquentes", "short": "En bref", "try": "À essayer",
        "read": "Lire le conseil", "all_tips": "Tous les conseils", "guides": "Les guides de fond", "updated": "Mis à jour le",
        "by": "Par Thierry Garot, joueur de pickleball", "tip_n": "Conseil n°", "home_crumb": "Accueil",
        "hero_h": "Un conseil de pickleball par jour.",
        "hero_p": "Simple, concret, à essayer dès votre prochaine partie. Et des guides complets sur les règles, le matériel et les tournois en France et dans le monde.",
        "cta": "Recevoir les conseils", "about": "/a-propos/", "about_t": "À propos", "legal": "/mentions-legales/", "legal_t": "Mentions légales",
        "foot_p": "Le média indépendant du pickleball en français. Un conseil chaque jour, des guides complets, le calendrier des tournois.",
        "cats": "Thèmes", "newsband_h": "La lettre de Pickleball du Jour", "newsband_p": "Les meilleurs conseils de la semaine et l'actu des tournois, gratuitement. Et une édition mensuelle enrichie pour ceux qui soutiennent le projet.",
        "date_fmt": lambda d: f"{d.day} {['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'][d.month-1]} {d.year}",
        "events": "Les prochains grands rendez-vous", "see_cal": "Voir tout le calendrier", "world": "Dans le monde"},
 "en": {"name": "Pickleball du Jour", "lang": "en", "home": "/en/", "tips": "tips", "tips_t": "Tips", "tip_of_day": "Tip of the day",
        "nav": [("Get started", "/en/how-to-start-pickleball/"), ("Rules", "/en/pickleball-rules/"), ("Paddles", "/en/choosing-a-pickleball-paddle/"), ("Tournaments", "/en/pickleball-tournaments/"), ("World", "/en/pickleball-around-the-world/"), ("Tips", "/en/tips/")],
        "news": "/en/newsletter/", "news_t": "Newsletter", "other": "FR", "faq": "Frequently asked questions", "short": "In short", "try": "Try this",
        "read": "Read the tip", "all_tips": "All tips", "guides": "In-depth guides", "updated": "Updated",
        "by": "By Thierry Garot, pickleball player", "tip_n": "Tip #", "home_crumb": "Home",
        "hero_h": "One pickleball tip a day.",
        "hero_p": "Simple, practical, ready for your next game. Plus complete guides to the rules, gear and tournaments in France and worldwide.",
        "cta": "Get the tips", "about": "/en/about/", "about_t": "About", "legal": "/en/legal/", "legal_t": "Legal notice",
        "foot_p": "An independent pickleball site from France. A tip every day, complete guides, the tournament calendar.",
        "cats": "Topics", "newsband_h": "The Pickleball du Jour letter", "newsband_p": "The week's best tips and tournament news, free. Plus a richer monthly edition for those who support the project.",
        "date_fmt": lambda d: d.strftime("%B %-d, %Y"),
        "events": "Coming up", "see_cal": "Full calendar", "world": "Worldwide"},
}

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">'
ICON = '<svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><circle cx="15" cy="15" r="14" fill="#d6f03f"/><g fill="#1f5fbf"><circle cx="10" cy="10" r="2.2"/><circle cx="18" cy="9" r="2.2"/><circle cx="21" cy="16" r="2.2"/><circle cx="14" cy="16" r="2.2"/><circle cx="9" cy="19" r="2.2"/><circle cx="16" cy="22" r="2.2"/></g></svg>'


def esc(s):
    return html.escape(s, quote=True)


def write(path, content):
    full = os.path.join(OUT, path.lstrip("/"))
    if full.endswith("/"):
        full += "index.html"
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def layout(lang, path, title, desc, body, alt_path, ld=None, og_type="website"):
    t = T[lang]
    url = SITE + path
    alt_url = SITE + alt_path
    nav = "".join(f'<a href="{h}">{esc(n)}</a>' for n, h in t["nav"])
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    fr_url, en_url = (url, alt_url) if lang == "fr" else (alt_url, url)
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<meta property="og:type" content="{og_type}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}"><meta property="og:site_name" content="Pickleball du Jour"><meta property="og:locale" content="{'fr_FR' if lang=='fr' else 'en_GB'}">
<meta name="theme-color" content="#1f5fbf">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="/style.css">
{lds}
</head>
<body>
<header class="top"><div class="wrap">
<a class="logo" href="{t['home']}">{ICON}<span>Pickleball <b>du Jour</b></span></a>
<nav class="nav" aria-label="Menu">{nav}<a href="{t['news']}"><strong>{t['news_t']}</strong></a><a class="lang" href="{alt_path}" hreflang="{'en' if lang=='fr' else 'fr'}">{t['other']}</a></nav>
</div></header>
<main>{body}</main>
<footer class="foot"><div class="wrap cols">
<div><h4>Pickleball du Jour</h4><p>{t['foot_p']}</p></div>
<div><h4>{t['guides']}</h4><ul>{''.join(f'<li><a href="{h}">{esc(n)}</a></li>' for n,h in t['nav'][:5])}</ul></div>
<div><h4>{t['name']}</h4><ul><li><a href="{t['news']}">{t['news_t']}</a></li><li><a href="{t['about']}">{t['about_t']}</a></li><li><a href="{t['legal']}">{t['legal_t']}</a></li><li><a href="{alt_path}">{'English version' if lang=='fr' else 'Version française'}</a></li></ul></div>
</div><div class="wrap"><p class="note" style="color:#a9bcd8;margin-top:24px">© {TODAY.year} Pickleball du Jour</p></div></footer>
</body></html>'''


def crumbs(lang, items):
    t = T[lang]
    parts = [f'<a href="{t["home"]}">{t["home_crumb"]}</a>'] + [f'<a href="{h}">{esc(n)}</a>' if h else esc(n) for n, h in items]
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": t["home_crumb"], "item": SITE + t["home"]}] + [
        {"@type": "ListItem", "position": i + 2, "name": n, **({"item": SITE + h} if h else {})} for i, (n, h) in enumerate(items)]}
    return f'<p class="crumbs">{" › ".join(parts)}</p>', ld


def fill(body, lang):
    return body.replace("{{COURT}}", court_svg(lang)).replace("{{PADDLE}}", paddle_svg(lang)).replace("{{SERVE}}", serve_svg(lang))


def faq_html(lang, faq):
    t = T[lang]
    items = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    return f"<h2>{t['faq']}</h2>{items}", ld


def pillar(lang, p, other_slug):
    t = T[lang]
    pre = "" if lang == "fr" else "/en"
    path = f"{pre}/{p['slug']}/"
    alt = (f"/en/{other_slug}/" if lang == "fr" else f"/{other_slug}/")
    cr, crld = crumbs(lang, [(p["h1"], None)])
    fq, fqld = faq_html(lang, p["faq"])
    art = {"@context": "https://schema.org", "@type": "Article", "headline": p["h1"], "description": p["desc"], "inLanguage": lang,
           "datePublished": LAUNCH.isoformat(), "dateModified": TODAY.isoformat(), "author": AUTHOR,
           "publisher": {"@type": "Organization", "name": "Pickleball du Jour", "url": SITE}, "mainEntityOfPage": SITE + path}
    lds = [art, crld, fqld]
    if p["slug"] in ("tournois-pickleball", "pickleball-tournaments"):
        for e in TOURNEYS:
            lds.append({"@context": "https://schema.org", "@type": "Event", "name": e["name"][lang], "startDate": e["start"], "endDate": e["end"],
                        "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                        "location": {"@type": "Place", "name": e["place"], "address": e["addr"]}, "organizer": {"@type": "Organization", "name": e["org"]}})
    related = [x for x in (PFR if lang == "fr" else PEN) if x["slug"] != p["slug"]][:6]
    rel = "".join(f'<a class="card" href="{pre}/{x["slug"]}/"><span class="k">{esc(x["kicker"])}</span><h3>{esc(x["h1"])}</h3></a>' for x in related)
    body = f'''<div class="wrap page">{cr}<div class="read">
<p class="meta">{esc(p["kicker"])} · {t["updated"]} {t["date_fmt"](TODAY)} · {t["by"]}</p>
<h1>{esc(p["h1"])}</h1>
<div class="answer"><strong>{t["short"]}</strong>{esc(p["answer"])}</div>
{fill(p["body"], lang)}
{fq}
<div class="drill"><b>{t["tip_of_day"]}{" :" if lang=="fr" else ":"}</b> <a href="{pre}/{t["tips"]}/">{t["all_tips"]} →</a></div>
</div>
<h2>{t["guides"]}</h2><div class="grid">{rel}</div></div>'''
    write(path, layout(lang, path, p["title"], p["desc"], body, alt, lds, "article"))
    return path


def tip_pages(lang, tips, other):
    t = T[lang]
    pre = "" if lang == "fr" else "/en"
    base = f"{pre}/{t['tips']}/"
    alt_base = "/en/tips/" if lang == "fr" else "/conseils/"
    paths = []
    for i, tip in enumerate(tips):
        slug, cat, title, summary, body, drill = tip
        path = f"{base}{slug}/"
        alt = f"{alt_base}{other[i][0]}/"
        cr, crld = crumbs(lang, [(t["tips_t"], base), (title, None)])
        prev_l = f'<a href="{base}{tips[i-1][0]}/">← {esc(tips[i-1][2])}</a>' if i > 0 else ""
        next_l = f'<a href="{base}{tips[(i+1)%len(tips)][0]}/">{esc(tips[(i+1)%len(tips)][2])} →</a>'
        art = {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": summary, "inLanguage": lang, "articleSection": cat,
               "datePublished": LAUNCH.isoformat(), "dateModified": TODAY.isoformat(), "author": AUTHOR, "publisher": {"@type": "Organization", "name": "Pickleball du Jour", "url": SITE}}
        b = f'''<div class="wrap page">{cr}<div class="read">
<p class="meta">{t["tip_n"]}{i+1} · {esc(cat)} · {t["by"]}</p>
<h1>{esc(title)}</h1>
<div class="answer"><strong>{t["short"]}</strong>{esc(summary)}</div>
{body}
<div class="drill"><b>{t["try"]}{" :" if lang=="fr" else ":"}</b> {esc(drill)}</div>
<p style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">{prev_l}{next_l}</p>
</div></div>'''
        write(path, layout(lang, path, f"{title} · {t['tip_n']}{i+1}", summary, b, alt, [art, crld], "article"))
        paths.append(path)
    cats = sorted({x[1] for x in tips})
    chips = '<a class="on" href="#" data-c="">' + ("Tous" if lang == "fr" else "All") + "</a>" + "".join(f'<a href="#" data-c="{esc(c)}">{esc(c)}</a>' for c in cats)
    cards = "".join(f'<a class="card" data-c="{esc(x[1])}" href="{base}{x[0]}/"><span class="k">{t["tip_n"]}{i+1} · {esc(x[1])}</span><h3>{esc(x[2])}</h3><p>{esc(x[3])}</p></a>' for i, x in enumerate(tips))
    h1 = "Tous les conseils de pickleball" if lang == "fr" else "All pickleball tips"
    intro = "Un nouveau conseil chaque jour, à essayer dès votre prochaine partie. Filtrez par thème." if lang == "fr" else "A new tip every day, ready for your next game. Filter by topic."
    cr, crld = crumbs(lang, [(t["tips_t"], None)])
    b = f'''<div class="wrap page">{cr}<h1>{h1}</h1><p>{intro}</p><div class="chips" id="chips">{chips}</div><div class="grid" id="tips">{cards}</div></div>
<script>{{const ch=document.getElementById('chips');ch.addEventListener('click',e=>{{const a=e.target.closest('a');if(!a)return;e.preventDefault();ch.querySelectorAll('a').forEach(x=>x.classList.toggle('on',x===a));const c=a.dataset.c;document.querySelectorAll('#tips .card').forEach(k=>k.style.display=!c||k.dataset.c===c?'':'none')}})}}</script>'''
    write(base, layout(lang, base, h1 + " · Pickleball du Jour", intro, b, alt_base, [crld]))
    paths.append(base)
    return paths


def home(lang, pages, tips):
    t = T[lang]
    pre = "" if lang == "fr" else "/en"
    base = f"{pre}/{t['tips']}/"
    idx = (TODAY - LAUNCH).days % len(tips)
    tip = tips[idx]
    data = json.dumps([[f"{base}{x[0]}/", x[1], x[2], x[3]] for x in tips], ensure_ascii=False)
    guides = "".join(f'<a class="card" href="{pre}/{p["slug"]}/"><span class="k">{esc(p["kicker"])}</span><h3>{esc(p["h1"])}</h3><p>{esc(p["desc"])}</p></a>' for p in pages)
    latest = "".join(f'<a class="card" href="{base}{x[0]}/"><span class="k">{esc(x[1])}</span><h3>{esc(x[2])}</h3><p>{esc(x[3])}</p></a>' for x in tips[:6])
    ev = "".join(f'<tr><td class="n">{esc(e["label"][lang])}</td><td>{esc(e["name"][lang])}</td><td>{esc(e["place"])}</td></tr>' for e in TOURNEYS[:5])
    cal = "/tournois-pickleball/" if lang == "fr" else "/en/pickleball-tournaments/"
    body = f'''<section class="hero"><div class="wrap">
<div><h1>{t["hero_h"]}</h1><p>{t["hero_p"]}</p>
<div class="tipcard" id="tod"><span class="k">{t["tip_of_day"]} · {esc(tip[1])}</span><h2 id="tod-t">{esc(tip[2])}</h2><p id="tod-s">{esc(tip[3])}</p><a id="tod-a" href="{base}{tip[0]}/">{t["read"]} →</a></div>
<p style="margin-top:22px"><a class="btn" href="{t["news"]}">{t["cta"]}</a></p></div>
<div>{hero_svg()}</div>
</div></section>
<section class="band"><div class="wrap"><h2 style="margin-top:0">{t["guides"]}</h2><div class="grid">{guides}</div></div></section>
<section class="band tint"><div class="wrap"><h2 style="margin-top:0">{t["all_tips"]}</h2><div class="grid">{latest}</div><p><a href="{base}">{t["all_tips"]} →</a></p></div></section>
<section class="band"><div class="wrap two"><div><h2 style="margin-top:0">{t["events"]}</h2><div class="tbl"><table><tbody>{ev}</tbody></table></div><p><a href="{cal}">{t["see_cal"]} →</a></p></div>
<div class="price best"><h2 style="margin-top:0">{t["newsband_h"]}</h2><p>{t["newsband_p"]}</p><a class="btn" href="{t["news"]}">{t["cta"]}</a></div></div></section>
<script>{{const D={data};const L=new Date(2026,10,27);const n=Math.floor((new Date().setHours(0,0,0,0)-L.getTime())/864e5);const i=((n%D.length)+D.length)%D.length;const x=D[i];
document.getElementById('tod-t').textContent=x[2];document.getElementById('tod-s').textContent=x[3];document.getElementById('tod-a').href=x[0];}}</script>'''
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Pickleball du Jour", "url": SITE + t["home"], "inLanguage": lang,
           "description": t["hero_p"], "publisher": {"@type": "Organization", "name": "Pickleball du Jour", "url": SITE, "founder": AUTHOR}}]
    title = "Pickleball du Jour · Un conseil de pickleball par jour" if lang == "fr" else "Pickleball du Jour · One pickleball tip a day"
    write(t["home"], layout(lang, t["home"], title, t["hero_p"], body, "/en/" if lang == "fr" else "/", ld))
    return t["home"]


def extra_pages(lang):
    out = []
    for e in EXTRA[lang]:
        cr, crld = crumbs(lang, [(e["h1"], None)])
        body = f'<div class="wrap page">{cr}<div class="read"><h1>{esc(e["h1"])}</h1>{e["body"]}</div></div>'
        write(e["path"], layout(lang, e["path"], e["title"], e["desc"], body, e["alt"], [crld]))
        out.append(e["path"])
    return out


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    assert len(PFR) == len(PEN) and len(TFR) == len(TEN), "FR/EN content must match"
    urls = []
    for lang, pages, other, tips, otips in (("fr", PFR, PEN, TFR, TEN), ("en", PEN, PFR, TEN, TFR)):
        urls.append(home(lang, pages, tips))
        for p, o in zip(pages, other):
            urls.append(pillar(lang, p, o["slug"]))
        urls += tip_pages(lang, tips, otips)
        urls += extra_pages(lang)
    shutil.copy(os.path.join(ROOT, "static", "style.css"), os.path.join(OUT, "style.css"))
    with open(os.path.join(OUT, "favicon.svg"), "w") as f:
        f.write(ICON.replace('width="30" height="30" ', 'xmlns="http://www.w3.org/2000/svg" '))
    with open(os.path.join(OUT, "CNAME"), "w") as f:
        f.write("pickleballdujour.fr\n")
    sm = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>" for u in urls)
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    llms = ["# Pickleball du Jour", "", "> Site indépendant du pickleball en français (et en anglais) créé par Thierry Garot, joueur de pickleball en France. Un conseil pratique chaque jour, des guides complets (règles FFT 2026, terrain, raquettes, débuter, pickleball ou padel), le calendrier des tournois en France et dans le monde.", "", "## Guides (FR)"]
    llms += [f"- [{p['h1']}]({SITE}/{p['slug']}/): {p['answer']}" for p in PFR]
    llms += ["", "## Guides (EN)"] + [f"- [{p['h1']}]({SITE}/en/{p['slug']}/): {p['answer']}" for p in PEN]
    llms += ["", "## Conseils du jour", f"- [Tous les conseils]({SITE}/conseils/)", f"- [All tips]({SITE}/en/tips/)"]
    with open(os.path.join(OUT, "llms.txt"), "w") as f:
        f.write("\n".join(llms) + "\n")
    nf = layout("fr", "/404.html", "Page introuvable · Pickleball du Jour", "Page introuvable", '<div class="wrap page"><h1>Balle dehors !</h1><p>Cette page n\'existe pas. <a href="/">Retour à l\'accueil</a> · <a href="/en/">English</a></p></div>', "/en/")
    write("/404.html", nf)
    print(f"{len(urls)} pages built")


if __name__ == "__main__":
    main()
