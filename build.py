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
from content.seances import SESSIONS
from finder import finder_html, data as tdata
from content.profs import profs_html
import scenes

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
SITE = "https://pickleballdujour.fr"
LAUNCH = datetime.date(2026, 11, 27)
TODAY = datetime.date.today()
import hashlib as _h
PUSH_READY = True
CSSV = _h.md5(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "style.css"), "rb").read()).hexdigest()[:8]
AUTHOR = {"@type": "Person", "@id": "https://thierrygarot.fr/#person", "name": "Thierry Garot", "url": "https://thierrygarot.fr/", "sameAs": ["https://thierrygarot.fr/", "https://www.linkedin.com/in/thierry-garot"]}

T = {
 "fr": {"name": "Pickleball du Jour", "lang": "fr", "home": "/", "tips": "conseils", "tips_t": "Conseils", "tip_of_day": "Le conseil du jour",
        "nav": [("Progresser", "/progresser/"), ("Séances", "/seances/"), ("Débuter", "/debuter-au-pickleball/"), ("Règles", "/regles-du-pickleball/"), ("Raquettes", "/choisir-raquette-pickleball/"), ("Tournois", "/tournois-pickleball/"), ("Trouver un prof", "/prof-de-pickleball/"), ("Monde", "/pickleball-dans-le-monde/"), ("Conseils", "/conseils/"), ("Avis", "/avis/")],
        "news": "/newsletter/", "news_t": "Newsletter", "other": "EN", "faq": "Questions fréquentes", "short": "En bref", "try": "À essayer",
        "read": "Lire le conseil", "all_tips": "Tous les conseils", "guides": "Les guides de fond", "updated": "Mis à jour le",
        "by": "Par <a href=\"https://thierrygarot.fr/\" rel=\"author\">Thierry Garot</a>, joueur de pickleball", "tip_n": "Conseil n°", "home_crumb": "Accueil",
        "hero_h": "Un conseil de pickleball par jour.",
        "hero_p": "Simple, concret, à essayer dès votre prochaine partie. Et des guides complets sur les règles, le matériel et les tournois en France et dans le monde.",
        "cta": "Recevoir les conseils", "about": "/a-propos/", "about_t": "À propos", "legal": "/mentions-legales/", "legal_t": "Mentions légales",
        "foot_p": "Le média indépendant du pickleball en français. Un conseil chaque jour, des guides complets, le calendrier des tournois.",
        "cats": "Thèmes", "newsband_h": "La lettre de Pickleball du Jour", "newsband_p": "Les conseils de la semaine et les tournois près de chez vous, gratuitement, une fois par semaine.",
        "date_fmt": lambda d: f"{d.day} {['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'][d.month-1]} {d.year}",
        "events": "Les prochains grands rendez-vous", "see_cal": "Voir tout le calendrier", "world": "Dans le monde"},
 "en": {"name": "Pickleball du Jour", "lang": "en", "home": "/en/", "tips": "tips", "tips_t": "Tips", "tip_of_day": "Tip of the day",
        "nav": [("Get started", "/en/how-to-start-pickleball/"), ("Rules", "/en/pickleball-rules/"), ("Paddles", "/en/choosing-a-pickleball-paddle/"), ("Tournaments", "/en/pickleball-tournaments/"), ("Coaches", "/en/find-a-pickleball-coach/"), ("World", "/en/pickleball-around-the-world/"), ("Tips", "/en/tips/")],
        "news": "/en/newsletter/", "news_t": "Newsletter", "other": "FR", "faq": "Frequently asked questions", "short": "In short", "try": "Try this",
        "read": "Read the tip", "all_tips": "All tips", "guides": "In-depth guides", "updated": "Updated",
        "by": "By <a href=\"https://thierrygarot.fr/\" rel=\"author\">Thierry Garot</a>, pickleball player", "tip_n": "Tip #", "home_crumb": "Home",
        "hero_h": "One pickleball tip a day.",
        "hero_p": "Simple, practical, ready for your next game. Plus complete guides to the rules, gear and tournaments in France and worldwide.",
        "cta": "Get the tips", "about": "/en/about/", "about_t": "About", "legal": "/en/legal/", "legal_t": "Legal notice",
        "foot_p": "An independent pickleball site from France. A tip every day, complete guides, the tournament calendar.",
        "cats": "Topics", "newsband_h": "The Pickleball du Jour letter", "newsband_p": "The week's tips and upcoming tournaments, free, once a week.",
        "date_fmt": lambda d: d.strftime("%B %-d, %Y"),
        "events": "Coming up", "see_cal": "Full calendar", "world": "Worldwide"},
}

FONTS = '<link rel="preload" href="/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="/fonts/archivo-latin-800-normal.woff2" as="font" type="font/woff2" crossorigin>'
ICON = '<svg viewBox="0 0 512 512" width="36" height="36" aria-hidden="true"><rect x="0" y="0" width="512" height="512" rx="122.88" fill="#1f5fbf"/><clipPath id="lg"><rect x="0" y="0" width="512" height="327.68"/></clipPath><line x1="85.7" y1="206.3" x2="45.8" y2="183.3" stroke="#d6f03f" stroke-width="28.2" stroke-linecap="round"/><line x1="157.7" y1="134.4" x2="134.7" y2="94.5" stroke="#d6f03f" stroke-width="28.2" stroke-linecap="round"/><line x1="256.0" y1="108.0" x2="256.0" y2="62.0" stroke="#d6f03f" stroke-width="28.2" stroke-linecap="round"/><line x1="354.3" y1="134.4" x2="377.3" y2="94.5" stroke="#d6f03f" stroke-width="28.2" stroke-linecap="round"/><line x1="426.3" y1="206.3" x2="466.2" y2="183.3" stroke="#d6f03f" stroke-width="28.2" stroke-linecap="round"/><g clip-path="url(#lg)"><circle cx="256.0" cy="304.64" r="153.6" fill="#d6f03f"/><circle cx="191.5" cy="258.6" r="18.4" fill="#a9c21a"/><circle cx="263.7" cy="230.9" r="18.4" fill="#a9c21a"/><circle cx="325.1" cy="277.0" r="18.4" fill="#a9c21a"/><circle cx="240.6" cy="307.7" r="18.4" fill="#a9c21a"/><circle cx="305.2" cy="350.7" r="18.4" fill="#a9c21a"/><circle cx="194.6" cy="350.7" r="18.4" fill="#a9c21a"/><circle cx="259.1" cy="389.1" r="18.4" fill="#a9c21a"/></g><rect x="51.2" y="327.68" width="409.6" height="56.32" rx="14.08" fill="#ffffff"/><line x1="102.4" y1="338.9" x2="102.4" y2="372.7" stroke="#1f5fbf" stroke-width="6.1"/><line x1="153.6" y1="338.9" x2="153.6" y2="372.7" stroke="#1f5fbf" stroke-width="6.1"/><line x1="204.8" y1="338.9" x2="204.8" y2="372.7" stroke="#1f5fbf" stroke-width="6.1"/><line x1="256.0" y1="338.9" x2="256.0" y2="372.7" stroke="#1f5fbf" stroke-width="6.1"/><line x1="307.2" y1="338.9" x2="307.2" y2="372.7" stroke="#1f5fbf" stroke-width="6.1"/><line x1="358.4" y1="338.9" x2="358.4" y2="372.7" stroke="#1f5fbf" stroke-width="6.1"/><line x1="409.6" y1="338.9" x2="409.6" y2="372.7" stroke="#1f5fbf" stroke-width="6.1"/><rect x="112.64" y="419.84000000000003" width="286.72" height="17.92" rx="8.704" fill="#ffffff" opacity=".55"/></svg>'


def esc(s):
    return html.escape(s, quote=True)


def write(path, content):
    full = os.path.join(OUT, path.lstrip("/"))
    if full.endswith("/"):
        full += "index.html"
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def tabbar(lang, path):
    pre = "" if lang == "fr" else "/en"
    items = [(pre + "/", "Accueil" if lang == "fr" else "Home", '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>'),
             (pre + ("/conseils/" if lang == "fr" else "/tips/"), "Conseils" if lang == "fr" else "Tips", '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>'),
             ("/tournois-pickleball/" if lang == "fr" else "/en/pickleball-tournaments/", "Tournois" if lang == "fr" else "Events", '<path d="M8 4h8v4a4 4 0 0 1-8 0zM6 5H4v2a3 3 0 0 0 3 3M18 5h2v2a3 3 0 0 1-3 3M12 12v4M8 20h8M10 16h4v4h-4z"/>'),
             *([("/progresser/", "Progresser", '<path d="M4 20V14M10 20V9M16 20V4M22 20H2"/>')] if lang == "fr" else []),
             (pre + "/newsletter/", "Newsletter", '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>')]
    out = []
    for href, lab, ic in items:
        on = (path == href) if href in ("/", "/en/") else path.startswith(href)
        out.append(f'<a href="{href}"{' class="on" aria-current="page"' if on else ''}><svg viewBox="0 0 24 24" aria-hidden="true">{ic}</svg><span>{lab}</span></a>')
    return '<nav class="tabbar" aria-label="' + ("Navigation rapide" if lang == "fr" else "Quick navigation") + '">' + "".join(out) + "</nav>"


def layout(lang, path, title, desc, body, alt_path, ld=None, og_type="website", og_img="/img/og.png"):
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
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/img/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">
<meta property="og:image" content="{SITE}{og_img}"><meta name="twitter:card" content="summary_large_image">
{FONTS}
<link rel="stylesheet" href="/style.css?v={CSSV}">
<link rel="alternate" type="application/rss+xml" title="Pickleball du Jour" href="{t['home'].rstrip('/')}/{t['tips']}/feed.xml">
{lds}
</head>
<body>
<header class="top"><div class="wrap">
<a class="logo" href="{t['home']}">{ICON}<span>Pickleball <b>du Jour</b></span></a>
<a class="langtop" href="{alt_path}" hreflang="{'en' if lang=='fr' else 'fr'}" aria-label="{'English version' if lang=='fr' else 'Version française'}">{t['other']}</a>
<button class="menubtn" id="mb" aria-expanded="false" aria-controls="nv"><span></span><span></span><span></span><b>Menu</b></button>
<nav class="nav" id="nv" aria-label="Menu">{nav}<a href="{t['news']}"><strong>{t['news_t']}</strong></a><a class="lang" href="{alt_path}" hreflang="{'en' if lang=='fr' else 'fr'}">{t['other']}</a></nav>
</div></header>
<main>{body}</main>
<footer class="foot"><div class="wrap cols">
<div><h4>Pickleball du Jour</h4><p>{t['foot_p']}</p></div>
<div><h4>{t['guides']}</h4><ul>{''.join(f'<li><a href="{h}">{esc(n)}</a></li>' for n,h in [x for x in t['nav'] if x[1] not in ('/progresser/', '/seances/')][:5])}</ul></div>
<div><h4>{t['name']}</h4><ul><li><a href="{t['news']}">{t['news_t']}</a></li><li><a href="{t['about']}">{t['about_t']}</a></li>{'<li><a href="/avis/">Avis des joueurs</a></li>' if lang == "fr" else ""}<li><a href="{t['legal']}">{t['legal_t']}</a></li><li><a href="{alt_path}">{'English version' if lang=='fr' else 'Version française'}</a></li></ul></div>
</div><div class="wrap"><p class="note" style="color:#a9bcd8;margin-top:24px">© {TODAY.year} Pickleball du Jour</p></div></footer>
{tabbar(lang, path)}
<script>{{const b=document.getElementById('mb'),n=document.getElementById('nv');b.addEventListener('click',()=>{{const o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}})}}</script>
<script>{{const A='https://pickleballdujour-stats.thierry-garot-17.workers.dev/hit';window.pbj=function(e,v){{try{{if(localStorage.getItem('pbj_optout'))return;const q=new URLSearchParams(location.search);const d=JSON.stringify({{p:location.pathname,r:e?'':document.referrer,l:navigator.language,w:innerWidth,u:q.get('utm_source')||'',e:e||'',v:v||''}});if(navigator.sendBeacon)navigator.sendBeacon(A,d);else fetch(A,{{method:'POST',body:d,keepalive:true}})}}catch(x){{}}}};pbj();{{const t0=Date.now();let mx=0,sent=0;const sc=()=>{{const h=document.documentElement;mx=Math.max(mx,Math.min(100,Math.round((scrollY+innerHeight)/Math.max(1,h.scrollHeight)*100)))}};sc();addEventListener('scroll',sc,{{passive:true}});const fin=()=>{{if(sent)return;sent=1;pbj('_fin',Math.round((Date.now()-t0)/1000)+'|'+mx)}};addEventListener('pagehide',fin);document.addEventListener('visibilitychange',()=>{{if(document.visibilityState==='hidden')fin()}})}}document.querySelectorAll('video[src*="/seances/"]').forEach(v=>{{const n=(v.getAttribute('src')||'').split('/').pop().replace('.mp4','');let h=0,e=0;v.addEventListener('timeupdate',()=>{{if(!h&&v.duration&&v.currentTime/v.duration>=.5){{h=1;pbj('mi_seance',n)}}}});v.addEventListener('ended',()=>{{if(!e){{e=1;pbj('fin_seance',n)}}}})}});document.addEventListener('click',ev=>{{const a=ev.target.closest('a');if(!a)return;if(a.pathname&&/newsletter/.test(a.pathname)&&a.host===location.host)pbj('clic_newsletter',location.pathname)}})}}</script>
<script>{{(function(){{const FR=document.documentElement.lang==='fr',VK='BAvVVsT0goxYtefwBLiCWDmNAXtPdmNKLj8IEi0DQSyJ2_miJbCINtOwXgXoSr_-kzuo5Q_jHNI0x1qW3XhHEBA',API='https://pickleballdujour-stats.thierry-garot-17.workers.dev';
if(!('serviceWorker' in navigator))return;navigator.serviceWorker.register('/sw.js').catch(()=>{{}});
const LS=(k,v)=>{{try{{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}}catch(e){{}}}};
const standalone=matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
const ios=/iphone|ipad|ipod/i.test(navigator.userAgent)&&!window.MSStream;
let vis=+(LS('pbj_visits')||0);if(!sessionStorage.getItem('pbj_v')){{try{{sessionStorage.setItem('pbj_v','1')}}catch(e){{}}vis++;LS('pbj_visits',vis)}}
// Notifications
const nb=document.getElementById('nfb'),nm=document.getElementById('nfm');
const u8=s=>{{const p='='.repeat((4-s.length%4)%4),b=atob((s+p).replace(/-/g,'+').replace(/_/g,'/'));return Uint8Array.from([...b].map(c=>c.charCodeAt(0)))}};
async function sub(){{try{{const perm=await Notification.requestPermission();if(perm!=='granted'){{nm.textContent=FR?'Notifications refusées. Vous pourrez les activer dans les réglages du navigateur.':'Notifications blocked. You can enable them in your browser settings.';return}}
const reg=await navigator.serviceWorker.ready;const s=await reg.pushManager.subscribe({{userVisibleOnly:true,applicationServerKey:u8(VK)}});
await fetch(API+'/push/sub',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{endpoint:s.endpoint,lang:FR?'fr':'en'}})}});
LS('pbj_push','1');nb.hidden=true;nm.textContent=FR?'C’est fait : le conseil arrivera chaque matin.':'Done: the tip will arrive every morning.';window.pbj&&pbj('notif_abonne','')}}catch(e){{nm.textContent=FR?'L’activation n’a pas fonctionné. Réessayez plus tard.':'It did not work. Please try again later.'}}}}
if(nb){{const canPush='PushManager' in window&&'Notification' in window;
if(canPush&&Notification.permission!=='denied'){{navigator.serviceWorker.ready.then(r=>r.pushManager.getSubscription()).then(s=>{{if(!s){{nb.hidden=false;nb.onclick=sub}}}}).catch(()=>{{}})}}
else if(ios&&!standalone&&FR){{nb.hidden=false;nb.onclick=()=>{{nm.textContent='Sur iPhone, installez d’abord l’appli : touchez Partager, puis « Sur l’écran d’accueil ». Ouvrez-la et touchez ce bouton.'}}}}}}
// Invitation à installer (mobile, 2e visite ou plus, une fois tous les 60 jours)
if(standalone||!matchMedia('(max-width:820px)').matches)return;
const last=+(LS('pbj_inst')||0);if(Date.now()-last<60*864e5||vis<2)return;
let deferred=null;window.addEventListener('beforeinstallprompt',e=>{{e.preventDefault();deferred=e;setTimeout(show,4000)}});
if(ios)setTimeout(show,8000);
function show(){{if(document.querySelector('.avtoast,.insttoast'))return;LS('pbj_inst',Date.now());
const d=document.createElement('div');d.className='insttoast';d.setAttribute('role','dialog');d.setAttribute('aria-label',FR?'Installer l’appli':'Install the app');
d.innerHTML='<button class="avx" aria-label="'+(FR?'Fermer':'Close')+'">×</button><img src="/img/icon-192.png" alt="" width="44" height="44"><div><b>'+(FR?'Pickleball du Jour en appli':'Pickleball du Jour as an app')+'</b><span>'+(ios?(FR?'Touchez Partager, puis « Sur l’écran d’accueil ».':'Tap Share, then “Add to Home Screen”.'):(FR?'Le conseil du jour en un geste, même hors connexion.':'Today’s tip in one tap, even offline.'))+'</span></div>'+(ios?'':'<button class="btn instgo">'+(FR?'Installer':'Install')+'</button>');
document.body.appendChild(d);requestAnimationFrame(()=>d.classList.add('in'));window.pbj&&pbj('appli_invite','vu');
d.querySelector('.avx').onclick=()=>d.remove();const g=d.querySelector('.instgo');if(g)g.onclick=async()=>{{if(!deferred)return;deferred.prompt();const c=await deferred.userChoice;window.pbj&&pbj('appli_invite',c.outcome);d.remove()}}}}
}})()}}</script>
<script>{{const o=document.getElementById('optout');if(o){{const done=()=>{{o.outerHTML='<b>'+(document.documentElement.lang==='fr'?'C’est noté : vos visites ne sont plus comptées sur cet appareil.':'Done: your visits are no longer counted on this device.')+'</b>'}};try{{if(localStorage.getItem('pbj_optout'))done()}}catch(e){{}}o.addEventListener('click',ev=>{{ev.preventDefault();try{{localStorage.setItem('pbj_optout','1')}}catch(e){{}}done()}})}}}}</script>
<script>{{(function(){{if(document.documentElement.lang!=='fr')return;const K='pbj_avis',P=location.pathname;let st={{}};try{{st=JSON.parse(localStorage.getItem(K)||'{{}}')}}catch(e){{}}
const save=()=>{{try{{localStorage.setItem(K,JSON.stringify(st))}}catch(e){{}}}};
if(P.startsWith('/avis')){{const n=new URLSearchParams(location.search).get('note');if(n){{const r=document.getElementById('n'+n);if(r)r.checked=true;const f=document.getElementById('avf');if(f)setTimeout(()=>f.scrollIntoView({{behavior:'smooth',block:'start'}}),400)}}}}
let pv=0;try{{pv=+(sessionStorage.getItem('pbj_pv')||0)+1;sessionStorage.setItem('pbj_pv',pv)}}catch(e){{}}
let ok=pv>=2;const o=window.pbj;window.pbj=function(e,v){{if(e==='avis_envoye'){{st.done=1;save()}}if(e&&/^(lecture_seance|quiz_resultat)$/.test(e))ok=true;return o&&o(e,v)}};
const blocked=()=>st.done||(st.t&&Date.now()-st.t<30*864e5)||P.startsWith('/avis')||P.startsWith('/admin');
if(blocked())return;let shown=false;
function show(){{if(shown||!ok||blocked())return;shown=true;st.t=Date.now();save();pbj('avis_toast','vu');
const d=document.createElement('div');d.className='avtoast';d.setAttribute('role','dialog');d.setAttribute('aria-label','Donner votre avis');
d.innerHTML='<button class="avx" aria-label="Fermer">×</button><b>Le site vous est utile ?</b><span>Dites-le en 30 secondes, ça aide les autres joueurs.</span><div class="avst">'+[1,2,3,4,5].map(i=>'<a href="/avis/?note='+i+'#avis" aria-label="'+i+' sur 5"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 2.6l2.85 6.05 6.65.82-4.9 4.58 1.28 6.6L12 17.4l-5.88 3.25 1.28-6.6-4.9-4.58 6.65-.82z"/></svg></a>').join('')+'</div>';
document.body.appendChild(d);requestAnimationFrame(()=>d.classList.add('in'));
d.querySelector('.avx').onclick=()=>{{d.remove();pbj('avis_toast','ferme')}};d.querySelectorAll('.avst a').forEach(a=>a.onclick=()=>pbj('avis_toast','clic'))}}
const mobile=matchMedia('(hover:none)').matches;
if(!mobile)document.addEventListener('mouseout',e=>{{if(!e.relatedTarget&&e.clientY<=0)show()}});
setTimeout(function tick(){{if(ok)show();else setTimeout(tick,5000)}},mobile?25000:60000);
}})()}}</script>
</body></html>'''


def crumbs(lang, items):
    t = T[lang]
    parts = [f'<a href="{t["home"]}">{t["home_crumb"]}</a>'] + [f'<a href="{h}">{esc(n)}</a>' if h else esc(n) for n, h in items]
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": t["home_crumb"], "item": SITE + t["home"]}] + [
        {"@type": "ListItem", "position": i + 2, "name": n, **({"item": SITE + h} if h else {})} for i, (n, h) in enumerate(items)]}
    return f'<p class="crumbs">{" › ".join(parts)}</p>', ld


def fill(body, lang):
    body = body.replace("{{FINDER}}", finder_html(lang)).replace("{{PROFS}}", profs_html(lang, STATS_API))
    return body.replace("{{COURT}}", court_svg(lang)).replace("{{PADDLE}}", paddle_svg(lang)).replace("{{SERVE}}", serve_svg(lang))


NL_URL = "https://thierry-garot.tinypages.co/newsletter-pickleball-du-jour"


def signup(lang, where):
    if lang == "fr":
        h, txt, btn = "Recevez les conseils chaque dimanche", "Les conseils de la semaine avec leurs schémas, les tournois à venir, et le livret d'exercices offert dès l'inscription. Gratuit.", "Je m'inscris gratuitement"
    else:
        h, txt, btn = "Get the tips every Sunday", "The week's tips with their diagrams, upcoming tournaments, and the drill booklet free when you sign up. Written in French for now.", "Sign up for free"
    return (f'<aside class="signup"><div><b>{h}</b><p>{txt}</p></div>'
            f'<a class="btn" href="{NL_URL}" onclick="window.pbj&&pbj(\'clic_inscription\',\'{where}\')">{btn} →</a></aside>')


def quizlink(lang):
    if lang != "fr":
        return ""
    return '<a class="quizlink" href="/progresser/" onclick="window.pbj&&pbj(\'clic_quiz\',\'conseil\')"><b>Quel conseil pour vous ?</b> Faites votre bilan en 2 minutes : niveau, axes de progrès et les conseils à travailler en premier →</a>'


def quiz_page():
    path = "/progresser/"
    cr, crld = crumbs("fr", [("Progresser", None)])
    frag = open(os.path.join(ROOT, "static", "quiz.html"), encoding="utf-8").read()
    body = frag.replace('<div class="wrap page qz">', '<div class="wrap page qz">' + cr, 1)
    write(path, layout("fr", path, "Progresser au pickleball : votre bilan en 2 minutes", "8 questions, 2 minutes, sans inscription : votre niveau estimé, vos points forts, vos axes de progrès et les conseils à travailler en premier.", body, "/en/", [crld]))
    return path


LEVEL_NAMES = [("avance", "Avancé", "#c8371e", "Pour les joueurs de tournoi qui gagnent sur les détails."),
               ("confirme", "Confirmé", "#0e3a78", "On construit le point : patience, reset, accélérations."),
               ("initie", "Initié", "#1f5fbf", "On joue des matchs : monter au filet et s'organiser en double."),
               ("decouverte", "Découverte", "#2a8a57", "Les bases pour bien commencer : service et règles.")]


def ucf(s): return s[:1].upper() + s[1:]

LEVEL_LABEL = {k: n for k, n, c, b in LEVEL_NAMES}
LEVEL_COL = {k: c for k, n, c, b in LEVEL_NAMES}
VIDEO_SM = {}


def seance_pages():
    out = []
    for i, x in enumerate(SESSIONS):
        path = f"/seances/{x['slug']}/"
        lab, col = LEVEL_LABEL[x["level"]], LEVEL_COL[x["level"]]
        cr, crld = crumbs("fr", [("Séances", "/seances/"), (x["title"], None)])
        same = [y for y in SESSIONS if y["level"] == x["level"] and y["slug"] != x["slug"]]
        others = "".join(f'<a class="card svc" href="/seances/{y["slug"]}/"><img src="/seances/{y["slug"]}.jpg" alt="" loading="lazy" width="640" height="360"><h3>{esc(y["title"])}</h3><p>{y["dur"]} s · {esc(y["goal"])}</p></a>' for y in same)
        transcript = " ".join([x["intro"], x["desc"], x["exo"], x["outro"]])
        prev_, next_ = SESSIONS[i - 1] if i else None, SESSIONS[i + 1] if i + 1 < len(SESSIONS) else None
        nav = (f'<a href="/seances/{prev_["slug"]}/">← {esc(prev_["title"])}</a>' if prev_ else "<span></span>") + (f'<a href="/seances/{next_["slug"]}/">{esc(next_["title"])} →</a>' if next_ else "")
        body = f'''<div class="wrap page sp">{cr}
<p><span class="svb" style="background:{col}">Niveau {lab}</span></p>
<h1>{esc(x["title"])}</h1>
<p class="lead">Une séance vidéo de {x["dur"]} secondes : le principe animé sur le terrain, puis un exercice avec son objectif.</p>
<video class="spv" src="/seances/{x["slug"]}.mp4" poster="/seances/{x["slug"]}.jpg" controls playsinline preload="metadata" crossorigin="anonymous" width="1280" height="720" onplay="if(!this.dataset.p){{this.dataset.p=1;window.pbj&&pbj('lecture_seance','{x["slug"]}')}}"><track kind="subtitles" srclang="fr" label="Français" src="/seances/{x["slug"]}.vtt"></video>
<h2>Le principe</h2><p>{esc(x["desc"])}</p>
<h2>L'exercice</h2><p>{esc(ucf(x["exo"].replace("Exercice : ", "", 1)))}</p><p class="spgoal"><b>{esc(x["goal"])}</b></p>
<h2>À retenir</h2><p>{esc(ucf(x["outro"].replace("Retenez : ", "", 1)))}</p>
<details class="sptr"><summary>Transcription de la vidéo</summary><p>{esc(transcript)}</p></details>
<a class="quizlink" href="/progresser/"><b>Pas sûr de votre niveau ?</b> Le bilan en 2 minutes vous indique la séance à suivre en premier →</a>
<h2>Autres séances niveau {lab}</h2><div class="grid">{others}</div>
<p class="spnav">{nav}</p>
<p><a href="/seances/">Toutes les séances vidéo →</a></p>
<p class="note">Ces séances donnent des conseils de joueur ; elles ne remplacent pas un entraîneur diplômé.</p></div>'''
        ld = {"@context": "https://schema.org", "@type": "VideoObject", "name": x["title"], "description": x["desc"], "thumbnailUrl": SITE + "/seances/" + x["slug"] + ".jpg",
              "contentUrl": SITE + "/seances/" + x["slug"] + ".mp4", "uploadDate": x.get("date", "2026-11-27"), "duration": f"PT{x['dur']}S", "inLanguage": "fr",
              "transcript": transcript, "educationalLevel": lab, "publisher": {"@type": "Organization", "name": "Pickleball du Jour", "url": SITE}}
        title = f"{x['title']} : séance vidéo de pickleball ({lab})"
        desc = f"Séance vidéo de {x['dur']} s, niveau {lab}. {x['desc']}"[:158]
        write(path, layout("fr", path, title, desc, body, "/en/", [crld, ld], "video.other", f"/seances/{x['slug']}.jpg"))
        VIDEO_SM[path] = x
        out.append(path)
    return out


def seances_page():
    path = "/seances/"
    cr, crld = crumbs("fr", [("Séances", None)])
    secs, lds = [], []
    for key, name, col, blurb in LEVEL_NAMES:
        cards = "".join(f'''<article class="sv" id="{x["slug"]}"><video src="/seances/{x["slug"]}.mp4" poster="/seances/{x["slug"]}.jpg" controls playsinline preload="none" crossorigin="anonymous" onplay="if(!this.dataset.p){{this.dataset.p=1;window.pbj&&pbj('lecture_seance','{x["slug"]}')}}"><track kind="subtitles" srclang="fr" label="Français" src="/seances/{x["slug"]}.vtt"></video><div class="svm"><h3><a href="/seances/{x["slug"]}/">{esc(x["title"])}</a></h3><p>{x["dur"]} s · {esc(x["goal"])}</p></div></article>''' for x in SESSIONS if x["level"] == key)
        secs.append(f'<section class="svl"><h2><span class="svb" style="background:{col}">{name}</span></h2><p class="note">{esc(blurb)}</p><div class="svg">{cards}</div></section>')
    lds.append({"@context": "https://schema.org", "@type": "ItemList", "name": "Séances vidéo de pickleball", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + "/seances/" + x["slug"] + "/", "name": x["title"]} for i, x in enumerate(SESSIONS)]})
    body = f'''<div class="wrap page">{cr}<h1>Séances vidéo&nbsp;: 30 secondes pour progresser</h1>
<p class="lead">{len(SESSIONS)} séances courtes, du joueur de tournoi au débutant. Le principe animé sur le terrain, un exercice avec son objectif, une voix qui vous guide et les sous-titres.</p>
<a class="quizlink" href="/progresser/"><b>Quelle séance pour vous ?</b> Faites votre bilan en 2 minutes : il vous indique la séance à suivre en premier →</a>
{"".join(secs)}
<p class="note">Ces séances donnent des conseils de joueur ; elles ne remplacent pas un entraîneur diplômé.</p></div>''' + avis_block("seances")
    write(path, layout("fr", path, "Séances vidéo de pickleball : 30 secondes pour progresser", f"{len(SESSIONS)} séances vidéo de pickleball de 30 secondes, du débutant au joueur de tournoi : service, score, dink, drop, reset, lob, stacking, erne, interception. Avec exercice et objectif chiffré.", body, "/en/", [crld] + lds))
    return path


STATS_API = "https://pickleballdujour-stats.thierry-garot-17.workers.dev"
AVIS_NOTE = "Avis déposés par des joueurs et relus avant publication. Nous publions les avis positifs comme négatifs, sans contrepartie et sans les modifier. Ne sont écartés que les avis injurieux, hors sujet ou publicitaires."


def avis_block(where, full=False):
    """Bloc avis : liste des avis publiés + formulaire. Reste caché tant que le service des avis ne répond pas."""
    return f'''<section class="band avisband" id="avis" hidden><div class="wrap">
<h2 style="margin-top:0">Ce qu'en disent les joueurs</h2>
<div class="avisstat" id="avstat"></div><div class="avisgrid" id="avlist"></div>
<details class="avisform"{' open' if full else ''}><summary>Donner mon avis</summary>
<form id="avf" novalidate>
<div class="avrow"><label>Prénom <input name="nom" maxlength="40" autocomplete="given-name" required></label><label>Ville <input name="ville" maxlength="40" autocomplete="address-level2"></label></div>
<label>E-mail <span class="opt">facultatif, jamais publié : seulement pour pouvoir vous répondre</span><input type="email" name="email" maxlength="120" autocomplete="email" inputmode="email"></label>
<label>Votre niveau <select name="niveau"><option value="">Je préfère ne pas dire</option><option>Découverte</option><option>Initié</option><option>Confirmé</option><option>Avancé</option></select></label>
<fieldset class="stars"><legend>Votre note <span class="stxt" id="stxt">5 sur 5, excellent</span></legend><div class="srow">{"".join(f'<input type="radio" name="note" id="n{i}" value="{i}"{" checked" if i == 5 else ""}><label for="n{i}" title="{i} sur 5"><span class="sv">{i} sur 5</span><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 2.6l2.85 6.05 6.65.82-4.9 4.58 1.28 6.6L12 17.4l-5.88 3.25 1.28-6.6-4.9-4.58 6.65-.82z"/></svg></label>' for i in range(5, 0, -1))}</div></fieldset>
<label>Votre avis <textarea name="texte" rows="4" minlength="20" maxlength="600" required placeholder="Ce qui vous a été utile, ce qui manque…"></textarea></label>
<input name="site" tabindex="-1" autocomplete="off" class="hp" aria-hidden="true">
<label class="chk"><input type="checkbox" name="accord" required> J'accepte que mon avis soit publié sur le site avec mon prénom et ma ville.</label>
<button class="btn" type="submit">Envoyer mon avis</button><p class="avmsg" id="avmsg" aria-live="polite"></p>
</form></details>
<p class="note">{AVIS_NOTE}{'' if full else ' <a href="/avis/">Tous les avis</a>'}</p>
</div></section>
<script>{{const A='{STATS_API}',S=document.getElementById('avis'),F=document.getElementById('avf'),M=document.getElementById('avmsg'),ST='<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 2.6l2.85 6.05 6.65.82-4.9 4.58 1.28 6.6L12 17.4l-5.88 3.25 1.28-6.6-4.9-4.58 6.65-.82z"/></svg>';
{{const W=['','1 sur 5, décevant','2 sur 5, moyen','3 sur 5, correct','4 sur 5, très bien','5 sur 5, excellent'],T=document.getElementById('stxt');F.addEventListener('change',e=>{{if(e.target.name==='note'&&T)T.textContent=W[+e.target.value]}})}}
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
fetch(A+'/avis/publics').then(r=>{{if(!r.ok)throw 0;return r.json()}}).then(d=>{{S.hidden=false;const a=d.avis||[];
if(a.length){{const m=a.reduce((x,y)=>x+y.note,0)/a.length;document.getElementById('avstat').innerHTML='<b>'+m.toFixed(1).replace('.',',')+' / 5</b> · '+a.length+' avis';}}
else document.getElementById('avstat').textContent='Soyez le premier à donner votre avis.';
document.getElementById('avlist').innerHTML=a.slice(0,{60 if full else 6}).map(x=>'<figure class="avis"><div class="st" role="img" aria-label="'+x.note+' sur 5">'+ST.repeat(x.note)+'<span>'+ST.repeat(5-x.note)+'</span></div><blockquote>'+esc(x.texte)+'</blockquote><figcaption>'+esc(x.nom)+(x.ville?', '+esc(x.ville):'')+(x.niveau?' · '+esc(x.niveau):'')+'</figcaption></figure>').join('')}}).catch(()=>{{}});
F.addEventListener('submit',async e=>{{e.preventDefault();const f=new FormData(F);const d={{nom:f.get('nom'),email:(f.get('email')||'').trim(),ville:f.get('ville'),niveau:f.get('niveau'),note:+f.get('note'),texte:f.get('texte'),site:f.get('site'),accord:!!f.get('accord'),page:location.pathname}};
if((d.nom||'').trim().length<2){{M.textContent='Indiquez votre prénom.';return}}if((d.texte||'').trim().length<20){{M.textContent='Votre avis doit faire au moins 20 caractères.';return}}if(d.email&&!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(d.email)){{M.textContent='L’adresse e-mail semble incomplète (ou laissez le champ vide).';return}}if(!d.accord){{M.textContent='Cochez la case d’accord pour la publication.';return}}
M.textContent='Envoi…';try{{const r=await fetch(A+'/avis',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}});
if(r.status===429){{M.textContent='Vous avez déjà envoyé plusieurs avis aujourd’hui. Merci !';return}}if(!r.ok)throw 0;F.reset();M.textContent='Merci ! Votre avis sera publié après relecture.';window.pbj&&pbj('avis_envoye','{where}')}}catch(x){{M.textContent='L’envoi n’a pas fonctionné. Réessayez dans un instant.'}}}})}}</script>'''


def avis_page():
    path = "/avis/"
    cr, crld = crumbs("fr", [("Avis", None)])
    body = f'<div class="wrap page">{cr}<h1>Les avis des joueurs</h1><p class="lead">Ce que les joueurs pensent de Pickleball du Jour : conseils, séances, bilan, tournois. Vous aussi, dites-nous ce qui vous aide et ce qui manque.</p></div>' + avis_block("page-avis", True)
    write(path, layout("fr", path, "Avis des joueurs sur Pickleball du Jour", "Les avis des joueurs sur Pickleball du Jour, relus avant publication, et le formulaire pour donner le vôtre.", body, "/en/", [crld]))
    return path


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
<h1>{esc(p["h1"])}</h1>
<div class="answer"><strong>{t["short"]}</strong>{esc(p["answer"])}</div>
{fill(p["body"], lang)}
{signup(lang, "guide")}
{fq}
<p class="meta byline">{esc(p["kicker"])} · {t["updated"]} <time datetime="{TODAY.isoformat()}">{t["date_fmt"](TODAY)}</time> · {t["by"]}</p>
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
        slug, cat, title, summary, body, drill = tip[:6]
        tdate = tip[6] if len(tip) > 6 else LAUNCH.isoformat()
        fkey = slug if lang == "fr" else other[i][0]
        png = f"/img/scenes/{fkey}-{lang}.png"
        has_png = os.path.exists(os.path.join(ROOT, "static", png.lstrip("/")))
        path = f"{base}{slug}/"
        alt = f"{alt_base}{other[i][0]}/"
        cr, crld = crumbs(lang, [(t["tips_t"], base), (title, None)])
        prev_l = f'<a href="{base}{tips[i-1][0]}/">← {esc(tips[i-1][2])}</a>' if i > 0 else ""
        next_l = f'<a href="{base}{tips[(i+1)%len(tips)][0]}/">{esc(tips[(i+1)%len(tips)][2])} →</a>'
        art = {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": summary, "inLanguage": lang, "articleSection": cat,
               "datePublished": tdate, "dateModified": TODAY.isoformat(), "author": AUTHOR, "publisher": {"@type": "Organization", "name": "Pickleball du Jour", "url": SITE}}
        b = f'''<div class="wrap page">{cr}<div class="read">
<h1>{esc(title)}</h1>
<div class="answer"><strong>{t["short"]}</strong>{esc(summary)}</div>
<figure class="scene">{scenes.svg(fkey, lang, cat, title)}<figcaption>{scenes.LEGEND[lang] if scenes.INDEX.get(fkey, -1) not in scenes.SPECIAL else ""}</figcaption></figure>
{body}
<div class="drill"><b>{t["try"]}{" :" if lang=="fr" else ":"}</b> {esc(drill)}</div>
<p class="meta byline">{t["tip_n"]}{i+1} · {esc(cat)} · {t["by"]}</p>
{quizlink(lang)}
{signup(lang, "conseil")}
<p style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">{prev_l}{next_l}</p>
</div></div>'''
        if has_png:
            art["image"] = SITE + png
        write(path, layout(lang, path, f"{title} · {t['tip_n']}{i+1}", summary, b, alt, [art, crld], "article", png if has_png else "/img/og.png"))
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


def home(lang, pages, tips, otips):
    t = T[lang]
    pre = "" if lang == "fr" else "/en"
    base = f"{pre}/{t['tips']}/"
    if lang == "fr":
        x0 = tips[0]
        with open(os.path.join(OUT, "tip-du-jour.json"), "w", encoding="utf-8") as f:
            json.dump({"date": x0[6] if len(x0) > 6 else "", "title": "Conseil du jour : " + x0[2], "summary": x0[3], "url": f"{base}{x0[0]}/?utm_source=notification"}, f, ensure_ascii=False)
    fresh = len(tips[0]) > 6 and tips[0][6] == TODAY.isoformat()
    idx = 0 if fresh else (TODAY - LAUNCH).days % len(tips)
    tip = tips[idx]
    fk = lambda j: tips[j][0] if lang == "fr" else otips[j][0]
    data = json.dumps([[f"{base}{x[0]}/", x[1], x[2], x[3], f"/img/scenes/{fk(j)}-{lang}.png", x[6] if len(x) > 6 else ""] for j, x in enumerate(tips)], ensure_ascii=False)
    guides = "".join(f'<a class="card" href="{pre}/{p["slug"]}/"><span class="k">{esc(p["kicker"])}</span><h3>{esc(p["h1"])}</h3><p>{esc(p["desc"])}</p></a>' for p in pages)
    latest = "".join(f'<a class="card" href="{base}{x[0]}/"><span class="k">{esc(x[1])}</span><h3>{esc(x[2])}</h3><p>{esc(x[3])}</p></a>' for x in tips[:6])
    ev = "".join(f'<tr><td class="n">{esc(e["label"][lang])}</td><td>{esc(e["name"][lang])}</td><td>{esc(e["place"])}</td></tr>' for e in TOURNEYS[:5])
    cal = "/tournois-pickleball/" if lang == "fr" else "/en/pickleball-tournaments/"
    body = f'''<section class="hero"><div class="wrap">
<div><h1>{t["hero_h"]}</h1><p>{t["hero_p"]}</p>
<p class="herocta"><a class="btn" href="{NL_URL}" onclick="window.pbj&&pbj('clic_inscription','accueil')">{t["cta"]}</a>{'<a class="btn ghost" href="/progresser/" onclick="window.pbj&&pbj(\'clic_quiz\',\'accueil\')">Faire mon bilan</a>' if lang == "fr" else ""}</p>
<div class="tipcard" id="tod"><span class="k">{t["tip_of_day"]} · <span id="tod-c">{esc(tip[1])}</span></span><p class="tdate" id="tod-d"></p><h2 id="tod-t">{esc(tip[2])}</h2><p id="tod-s">{esc(tip[3])}</p><a id="tod-a" href="{base}{tip[0]}/">{t["read"]} →</a>{'<button class="notifbtn" id="nfb" type="button" hidden>' if PUSH_READY else '<button class="notifbtn" id="nfb-off" type="button" hidden>'}{"🔔 Recevoir le conseil chaque matin" if lang == "fr" else "🔔 Get the tip every morning"}</button><p class="notifmsg" id="nfm" aria-live="polite"></p></div>
</div>
<div class="todimg"><a id="tod-ia" href="{base}{tip[0]}/"><img id="tod-img" src="/img/scenes/{fk(idx)}-{lang}.png" width="300" height="{scenes.H}" alt="{esc(tip[2])}"></a></div>
</div></section>
<section class="band"><div class="wrap"><h2 style="margin-top:0">{t["guides"]}</h2><div class="grid">{guides}</div></div></section>
<section class="band tint"><div class="wrap"><h2 style="margin-top:0">{t["all_tips"]}</h2><div class="grid">{latest}</div><p><a href="{base}">{t["all_tips"]} →</a></p></div></section>
{avis_block("accueil") if lang == "fr" else ""}
<section class="band"><div class="wrap two"><div><h2 style="margin-top:0">{t["events"]}</h2><div class="tbl"><table><tbody>{ev}</tbody></table></div><p><a href="{cal}">{t["see_cal"]} →</a></p></div>
<div class="price best"><h2 style="margin-top:0">{t["newsband_h"]}</h2><p>{t["newsband_p"]}</p><a class="btn" href="{NL_URL}" onclick="window.pbj&&pbj('clic_inscription','accueil-bas')">{t["cta"]}</a></div></div></section>
<script>{{const D={data};const L=new Date(2026,10,27);const T=new Date();const iso=T.getFullYear()+'-'+String(T.getMonth()+1).padStart(2,'0')+'-'+String(T.getDate()).padStart(2,'0');const n=Math.floor((new Date().setHours(0,0,0,0)-L.getTime())/864e5);const i=D[0][5]===iso?0:((n%D.length)+D.length)%D.length;const x=D[i];document.getElementById('tod-c').textContent=x[1];
document.getElementById('tod-t').textContent=x[2];document.getElementById('tod-s').textContent=x[3];document.getElementById('tod-a').href=x[0];const im=document.getElementById('tod-img');im.src=x[4];im.alt=x[2];document.getElementById('tod-ia').href=x[0];const dd=new Date().toLocaleDateString('{"fr-FR" if lang == "fr" else "en-GB"}',{{weekday:'long',day:'numeric',month:'long',year:'numeric'}});document.getElementById('tod-d').textContent=dd.charAt(0).toUpperCase()+dd.slice(1);}}</script>'''
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


def rss(lang, tips, otips):
    from email.utils import format_datetime
    t = T[lang]
    pre = "" if lang == "fr" else "/en"
    base = f"{pre}/{t['tips']}/"
    title = "Pickleball du Jour : le conseil du jour" if lang == "fr" else "Pickleball du Jour: tip of the day"
    items = []
    for i, tip in enumerate(sorted(tips, key=lambda x: (x[6] if len(x) > 6 else "", -tips.index(x)), reverse=True)[:30]):
        slug, cat, ti, summary, body, drill = tip[:6]
        d = datetime.datetime.fromisoformat((tip[6] if len(tip) > 6 else LAUNCH.isoformat()) + "T06:45:00+01:00") - datetime.timedelta(minutes=i)
        url = SITE + base + slug + "/"
        fkey = slug if lang == "fr" else otips[tips.index(tip)][0]
        png = f"/img/scenes/{fkey}-{lang}.png"
        img = f'<p><img src="{SITE}{png}" alt="{html.escape(ti, quote=True)}" width="600" style="max-width:100%;height:auto"></p>' if os.path.exists(os.path.join(ROOT, "static", png.lstrip("/"))) else ""
        desc = img + f"<p><strong>{html.escape(summary, quote=False)}</strong></p>{body}<p><em>{t['try']}{' :' if lang == 'fr' else ':'}</em> {html.escape(drill, quote=False)}</p><p><a href=\"{url}\">{t['read']}</a></p>"
        items.append(f"<item><title>{html.escape(ti, quote=False)}</title><link>{url}</link><guid isPermaLink=\"true\">{url}</guid><category>{html.escape(cat, quote=False)}</category><pubDate>{format_datetime(d)}</pubDate><description><![CDATA[{desc}]]></description></item>")
    xml = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>{title}</title><link>{SITE}{t["home"]}</link><atom:link href="{SITE}{base}feed.xml" rel="self" type="application/rss+xml"/><description>{html.escape(t["hero_p"])}</description><language>{lang}</language>{"".join(items)}</channel></rss>'
    path = os.path.join(OUT, (base + "feed.xml").lstrip("/"))
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    assert len(PFR) == len(PEN) and len(TFR) == len(TEN), "FR/EN content must match"
    urls = []
    for lang, pages, other, tips, otips in (("fr", PFR, PEN, TFR, TEN), ("en", PEN, PFR, TEN, TFR)):
        urls.append(home(lang, pages, tips, otips))
        for p, o in zip(pages, other):
            urls.append(pillar(lang, p, o["slug"]))
        urls += tip_pages(lang, tips, otips)
        urls += extra_pages(lang)
        if lang == "fr":
            urls.append(quiz_page())
            urls.append(seances_page())
            urls += seance_pages()
            urls.append(avis_page())
        rss(lang, tips, otips)
    shutil.copy(os.path.join(ROOT, "static", "style.css"), os.path.join(OUT, "style.css"))
    shutil.copy(os.path.join(ROOT, "static", "img", "icone.svg"), os.path.join(OUT, "favicon.svg"))
    os.makedirs(os.path.join(OUT, "admin"), exist_ok=True)
    with open(os.path.join(OUT, "admin", "seances.json"), "w", encoding="utf-8") as _f:
        json.dump({x["slug"]: {"t": x["title"], "l": x["level"]} for x in SESSIONS}, _f, ensure_ascii=False)
    os.makedirs(os.path.join(OUT, "admin"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "static", "admin.html"), os.path.join(OUT, "admin", "index.html"))
    for short in ("inscription", "en/signup"):
        os.makedirs(os.path.join(OUT, short), exist_ok=True)
        with open(os.path.join(OUT, short, "index.html"), "w") as f:
            f.write(f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url={NL_URL}"><link rel="canonical" href="{SITE}/newsletter/"><title>Inscription · Pickleball du Jour</title></head><body><script>location.replace("{NL_URL}")</script><p><a href="{NL_URL}">Continuer vers l\'inscription</a></p></body></html>')
    shutil.copytree(os.path.join(ROOT, "static", "img"), os.path.join(OUT, "img"))
    shutil.copytree(os.path.join(ROOT, "static", "fonts"), os.path.join(OUT, "fonts"), dirs_exist_ok=True)
    if os.path.isdir(os.path.join(ROOT, "static", "seances")):
        shutil.copytree(os.path.join(ROOT, "static", "seances"), os.path.join(OUT, "seances"), dirs_exist_ok=True)
    if os.path.isdir(os.path.join(ROOT, "static", "livret")):
        shutil.copytree(os.path.join(ROOT, "static", "livret"), os.path.join(OUT, "livret"))
    with open(os.path.join(OUT, "manifest.webmanifest"), "w") as f:
        json.dump({"id": "/", "name": "Pickleball du Jour", "short_name": "Pickleball", "description": "Un conseil de pickleball par jour, des séances vidéo de 30 secondes et les tournois près de chez vous.",
                   "lang": "fr", "start_url": "/?utm_source=app", "scope": "/", "display": "standalone", "orientation": "portrait", "background_color": "#ffffff", "theme_color": "#1f5fbf", "categories": ["sports", "education"],
                   "icons": [{"src": "/img/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"}, {"src": "/img/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}],
                   "shortcuts": [{"name": "Le conseil du jour", "url": "/?utm_source=app"}, {"name": "Séances vidéo", "url": "/seances/"}, {"name": "Trouver un tournoi", "url": "/tournois-pickleball/"}, {"name": "Mon bilan", "url": "/progresser/"}]}, f)
    with open(os.path.join(OUT, "CNAME"), "w") as f:
        f.write("pickleballdujour.fr\n")
    # Fichiers de validation moteurs (Search Console, IndexNow) servis à la racine
    rootdir = os.path.join(ROOT, "static", "root")
    if os.path.isdir(rootdir):
        for fn in os.listdir(rootdir):
            shutil.copy(os.path.join(rootdir, fn), os.path.join(OUT, fn))
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    with open(os.path.join(ROOT, "static", "sw.js"), encoding="utf-8") as f:
        swsrc = f.read().replace("__VERSION__", CSSV)
    with open(os.path.join(OUT, "sw.js"), "w", encoding="utf-8") as f:
        f.write(swsrc)
    write("/hors-ligne/", layout("fr", "/hors-ligne/", "Hors connexion · Pickleball du Jour", "Vous êtes hors connexion.", '''<div class="wrap page"><h1>Vous êtes hors connexion</h1><p class="lead">Pas de réseau pour l'instant. Les pages que vous avez déjà ouvertes restent disponibles : revenez en arrière ou ouvrez le conseil du jour.</p><p><a class="btn" href="/">Le conseil du jour</a></p></div>''', "/en/").replace('<meta name="description"', '<meta name="robots" content="noindex"><meta name="description"', 1))
    with open(os.path.join(OUT, "_headers"), "w") as f:
        f.write("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: SAMEORIGIN\n  Strict-Transport-Security: max-age=31536000\n\n/img/*\n  Cache-Control: public, max-age=2592000\n\n/style.css\n  Cache-Control: public, max-age=86400\n")
    def vsm(u):
        x = VIDEO_SM.get(u)
        if not x: return ""
        return (f"<video:video><video:thumbnail_loc>{SITE}/seances/{x['slug']}.jpg</video:thumbnail_loc><video:title>{esc(x['title'])}</video:title>"
                f"<video:description>{esc(x['desc'])}</video:description><video:content_loc>{SITE}/seances/{x['slug']}.mp4</video:content_loc><video:duration>{x['dur']}</video:duration>"
                f"<video:publication_date>{x.get('date', '2026-11-27')}</video:publication_date><video:family_friendly>yes</video:family_friendly></video:video>")
    sm = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{TODAY.isoformat()}</lastmod>{vsm(u)}</url>" for u in urls)
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">{sm}</urlset>')
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nDisallow: /admin/\n\nUser-agent: Bingbot\nAllow: /\nDisallow: /admin/\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: ChatGPT-User\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: Claude-SearchBot\nAllow: /\n\nUser-agent: Claude-User\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: Perplexity-User\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\nUser-agent: Applebot-Extended\nAllow: /\n\nUser-agent: MistralAI-User\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    llms = ["# Pickleball du Jour", "", "> Site indépendant du pickleball en français (et en anglais) créé par Thierry Garot, joueur de pickleball en France. Un conseil pratique chaque jour, des guides complets (règles FFT 2026, terrain, raquettes, débuter, pickleball ou padel), le calendrier des tournois en France et dans le monde.", "", "## Guides (FR)"]
    llms += [f"- [{p['h1']}]({SITE}/{p['slug']}/): {p['answer']}" for p in PFR]
    llms += ["", "## Guides (EN)"] + [f"- [{p['h1']}]({SITE}/en/{p['slug']}/): {p['answer']}" for p in PEN]
    llms += ["", "## Conseils du jour", f"- [Tous les conseils]({SITE}/conseils/): un conseil pratique publié chaque matin, avec un schéma de terrain et un exercice mesurable", f"- [All tips]({SITE}/en/tips/)"]
    llms += ["", "## Progresser", f"- [Bilan de niveau en 2 minutes]({SITE}/progresser/): 8 questions sans inscription ; niveau estimé (Découverte, Initié, Confirmé, Avancé), points forts, axes de progrès, conseils et séance vidéo recommandés"]
    llms += ["", "## Séances vidéo (30 secondes, par niveau)"] + [f"- [{x['title']}]({SITE}/seances/{x['slug']}/): niveau {dict(avance='Avancé', confirme='Confirmé', initie='Initié', decouverte='Découverte')[x['level']]}, {x['dur']} s. {x['desc']}" for x in SESSIONS]
    llms += ["", "## Tournois", f"- [Trouver un tournoi près de chez soi]({SITE}/tournois-pickleball/#recherche): tournois homologués FFT (K25 à K1000) et tournois de clubs, recherche par ville ou position, mis à jour chaque semaine"]
    llms += ["", "## Autres", f"- [Avis des joueurs]({SITE}/avis/)", f"- [Newsletter gratuite du dimanche]({SITE}/newsletter/)", f"- [À propos]({SITE}/a-propos/)"]
    with open(os.path.join(OUT, "tournois.json"), "w") as f:
        json.dump(tdata(), f, ensure_ascii=False)
    with open(os.path.join(OUT, "llms.txt"), "w") as f:
        f.write("\n".join(llms) + "\n")
    nf = layout("fr", "/404.html", "Page introuvable · Pickleball du Jour", "Page introuvable", '<div class="wrap page"><h1>Balle dehors !</h1><p>Cette page n\'existe pas. <a href="/">Retour à l\'accueil</a> · <a href="/en/">English</a></p></div>', "/en/")
    write("/404.html", nf)
    print(f"{len(urls)} pages built")


if __name__ == "__main__":
    main()
