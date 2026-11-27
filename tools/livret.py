"""Build the free exercise booklet (PDF, FR + EN) from the daily tips and their situation diagrams.
Output: static/livret/exercices-pickleball.pdf and static/livret/pickleball-drills.pdf
Usage: python3 tools/livret.py"""
import asyncio, html, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import scenes
from content.tips_fr import TIPS as TFR
from content.tips_en import TIPS as TEN

OUT = os.path.join(ROOT, "static", "livret")
FILES = {"fr": "exercices-pickleball.pdf", "en": "pickleball-drills.pdf"}
e = html.escape

TXT = {
    "fr": {
        "title": "{n} exercices pour progresser au pickleball",
        "sub": "Un exercice par situation de jeu, avec son schéma. À faire seul, à deux ou à quatre.",
        "intro_h": "Comment utiliser ce livret",
        "intro": [
            "Chaque fiche part d'un conseil publié sur Pickleball du Jour. Le schéma montre la situation : vous et votre partenaire en jaune, les adversaires en blanc, la balle en pointillés.",
            "Prenez-en deux par séance, pas plus. Un exercice qu'on répète dix minutes vaut mieux que cinq qu'on survole.",
            "Notez votre score quand l'exercice en donne un (par exemple, combien de services sur dix tombent au fond). La semaine suivante, refaites-le : c'est là qu'on voit les progrès.",
            "Pas besoin d'être licencié ni d'avoir un terrain parfait. Un bout de mur, un coéquipier patient et quelques balles suffisent pour la plupart.",
        ],
        "principle": "L'idée", "drill": "L'exercice", "more": "Le conseil complet",
        "end_h": "Un nouveau conseil chaque matin",
        "end": "Chaque jour, pickleballdujour.fr publie un conseil court avec son schéma, et la newsletter du dimanche récapitule la semaine. C'est gratuit.",
        "base": "/conseils/", "foot": "pickleballdujour.fr · livret gratuit, à partager librement",
    },
    "en": {
        "title": "{n} drills to improve your pickleball",
        "sub": "One drill per game situation, each with its diagram. Alone, with a partner or with four.",
        "intro_h": "How to use this booklet",
        "intro": [
            "Each card comes from a tip published on Pickleball du Jour. The diagram shows the situation: you and your partner in yellow, the opponents in white, the ball as a dotted line.",
            "Pick two per session, no more. One drill repeated for ten minutes beats five you rush through.",
            "Write down your score when the drill gives one (for example, how many serves out of ten land deep). Do it again the next week: that is where you see progress.",
            "You do not need a licence or a perfect court. A wall, a patient partner and a few balls cover most of them.",
        ],
        "principle": "The idea", "drill": "The drill", "more": "Full tip",
        "end_h": "A new tip every morning",
        "end": "Every day, pickleballdujour.fr publishes a short tip with its diagram, and the Sunday newsletter sums up the week. It is free.",
        "base": "/en/tips/", "foot": "pickleballdujour.fr · free booklet, share it freely",
    },
}

CSS = """
@page{size:A4;margin:14mm 14mm 16mm}
*{box-sizing:border-box}
body{margin:0;font:10.5pt/1.5 Inter,system-ui,sans-serif;color:#0f1c2e}
h1,h2,h3{font-family:Archivo,Inter,sans-serif;letter-spacing:-.01em;margin:0}
.cover{height:265mm;display:flex;flex-direction:column;justify-content:space-between;background:#1f5fbf;color:#fff;border-radius:8mm;padding:16mm 14mm;page-break-after:always}
.cover .brand{display:flex;align-items:center;gap:10px;font:800 15pt Archivo,Inter,sans-serif}
.cover .brand img{width:44px;height:44px;border-radius:10px}
.cover h1{font-size:34pt;line-height:1.05;font-weight:800}
.cover h1 b{color:#d6f03f}
.cover p{font-size:13pt;color:#dbe6ff;max-width:140mm}
.cover .court{align-self:center;width:62mm}
.cover .court svg{width:100%;height:auto;border-radius:6mm}
.intro{page-break-after:always;padding-top:6mm}
.intro h2{font-size:20pt;margin-bottom:6mm;color:#1f5fbf}
.intro p{font-size:11.5pt;margin:0 0 4mm}
.legend{display:flex;gap:16px;margin-top:6mm;font-size:10pt;color:#55657c}
.legend i{display:inline-block;width:11px;height:11px;border-radius:50%;border:2px solid #0f1c2e;margin-right:5px;vertical-align:-1px}
.card{display:grid;grid-template-columns:52mm 1fr;gap:7mm;align-items:start;border:1.5px solid #e1e7f0;border-radius:5mm;padding:6mm;margin-bottom:6mm;break-inside:avoid;height:124mm;overflow:hidden}
.card svg{width:100%;height:auto;border-radius:4mm}
.num{font:800 10pt Inter,sans-serif;color:#1f5fbf;text-transform:uppercase;letter-spacing:.06em}
.card h3{font-size:16pt;line-height:1.15;margin:1.5mm 0 4mm}
.lab{display:inline-block;font:800 8.5pt Inter,sans-serif;text-transform:uppercase;letter-spacing:.06em;background:#eef3fb;color:#0e3a78;border-radius:99px;padding:1mm 3mm;margin-bottom:1.5mm}
.drill{background:#f4fbd0;border-left:4px solid #b6d10f;border-radius:3mm;padding:3mm 4mm;margin-top:3mm}
.drill .lab{background:#d6f03f;color:#0f1c2e}
.card p{margin:0 0 2mm}
.more{font-size:9pt;color:#55657c;margin-top:3mm}
.end{page-break-before:always;background:#0e3a78;color:#fff;border-radius:8mm;padding:18mm 14mm;margin-top:4mm}
.end h2{font-size:24pt;color:#d6f03f;margin-bottom:5mm}
.end p{font-size:13pt;color:#dbe6ff}
.end .url{font:800 18pt Archivo,Inter,sans-serif;color:#fff;margin-top:8mm}
"""


def page(lang):
    t = TXT[lang]
    tips = TFR if lang == "fr" else TEN
    icon = open(os.path.join(ROOT, "static", "img", "icone.svg")).read()
    import base64
    icon_uri = "data:image/svg+xml;base64," + base64.b64encode(icon.encode()).decode()
    title = t["title"].format(n=len(tips))
    words = title.split(" ", 2)
    htitle = f"<b>{e(words[0])}</b> {e(' '.join(words[1:]))}"
    cards = []
    for i, tip in enumerate(tips):
        fkey = TFR[i][0]
        slug, cat, ti, summary, body, drill = tip[:6]
        cards.append(f'''<section class="card"><div>{scenes.svg(fkey, lang, cat, ti)}</div><div>
<div class="num">{"Exercice" if lang == "fr" else "Drill"} {i+1} · {e(cat)}</div><h3>{e(ti)}</h3>
<span class="lab">{t["principle"]}</span><p>{e(summary)}</p>
<div class="drill"><span class="lab">{t["drill"]}</span><p>{e(drill)}</p></div>
<p class="more">{t["more"]} : pickleballdujour.fr{t["base"]}{e(slug)}/</p></div></section>''')
    intro = "".join(f"<p>{e(p)}</p>" for p in t["intro"])
    legend = scenes.LEGEND[lang].replace('class="dash"', 'style="border-radius:0;border:0;border-top:3px dashed #9bb800;width:22px;height:0"')
    return f'''<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><title>{e(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="cover"><div class="brand"><img src="{icon_uri}" alt="">Pickleball du Jour</div>
<div><h1>{htitle}</h1><p style="margin-top:6mm">{e(t["sub"])}</p></div>
<div class="court">{scenes.svg(TFR[2][0], lang, TFR[2][1], "")}</div>
<p style="font-size:10pt">pickleballdujour.fr</p></div>
<div class="intro"><h2>{t["intro_h"]}</h2>{intro}<div class="legend">{legend}</div></div>
{"".join(cards)}
<div class="end"><h2>{t["end_h"]}</h2><p>{e(t["end"])}</p><div class="url">pickleballdujour.fr</div></div>
</body></html>'''


async def main():
    from playwright.async_api import async_playwright
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        kw = {"executable_path": "/usr/bin/google-chrome"} if os.path.exists("/usr/bin/google-chrome") else {}
        b = await p.chromium.launch(**kw)
        pg = await b.new_page()
        for lang in ("fr", "en"):
            await pg.set_content(page(lang), wait_until="networkidle")
            await pg.pdf(path=os.path.join(OUT, FILES[lang]), format="A4", print_background=True,
                         display_header_footer=True, header_template="<span></span>",
                         footer_template=f'<div style="width:100%;font:8px Inter,sans-serif;color:#8896aa;text-align:center">{TXT[lang]["foot"]} · <span class="pageNumber"></span></div>',
                         margin={"top": "14mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
        await b.close()
    print("ok")

asyncio.run(main())
