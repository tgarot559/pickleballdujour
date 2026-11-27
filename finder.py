"""Moteur de recherche des tournois par ville, code postal ou position (mobile first)."""
import json, datetime
from content.local_tourneys import LOCAL, CHECKED

TXT = {
 "fr": {"h": "Trouver un tournoi près de chez vous", "ph": "Ville ou code postal", "go": "Chercher", "me": "Autour de moi",
        "r": "Rayon", "all": "Toute la France", "none": "Aucun tournoi dans ce rayon pour l'instant. Élargissez la zone.",
        "km": "km", "src": "Voir la fiche et s'inscrire", "more": "Voir plus de tournois", "found": "tournois trouvés", "checked": "Liste vérifiée le",
        "geo_err": "Position indisponible. Tapez plutôt une ville.", "notfound": "Ville introuvable. Essayez un code postal.",
        "note": "Tournois homologués FFT (K25 à K1000) et tournois de clubs. Inscription sur Ten'Up ou sur la fiche de l'organisateur. Votre position reste sur votre téléphone : elle n'est ni envoyée ni enregistrée."},
 "en": {"h": "Find a tournament near you", "ph": "Town or postcode (France)", "go": "Search", "me": "Near me",
        "r": "Radius", "all": "All of France", "none": "No tournament within this radius yet. Try a wider area.",
        "km": "km", "src": "Details and entry", "more": "Show more tournaments", "found": "tournaments found", "checked": "List checked on",
        "geo_err": "Location unavailable. Type a town instead.", "notfound": "Town not found. Try a postcode.",
        "note": "FFT-sanctioned tournaments (K25 to K1000) and club events in France. Entry via Ten'Up or the organiser's page. Your location stays on your phone: it is never sent or stored."},
}

def data():
    today = datetime.date.today().isoformat()
    return [dict(s=a, e=b, n=n, c=c, d=d, g=g, l=lv, la=la, lo=lo, u=u) for (a, b, n, c, d, g, lv, la, lo, u) in LOCAL if b >= today]

def finder_html(lang):
    t = TXT[lang]
    D = json.dumps(data(), ensure_ascii=False)
    loc = "fr-FR" if lang == "fr" else "en-GB"
    return f'''<section class="finder" id="recherche"><h2 style="margin-top:0">{t["h"]}</h2>
<form id="ff" class="ffrow" role="search"><label class="sr" for="fq">{t["ph"]}</label><input id="fq" type="search" inputmode="search" autocomplete="address-level2" placeholder="{t["ph"]}"><button class="btn" type="submit">{t["go"]}</button></form>
<div class="ffrow"><button class="btn ghost" id="fme" type="button">◎ {t["me"]}</button>
<label class="sr" for="fr">{t["r"]}</label><select id="fr"><option value="50">50 {t["km"]}</option><option value="100" selected>100 {t["km"]}</option><option value="200">200 {t["km"]}</option><option value="0">{t["all"]}</option></select></div>
<p class="meta" id="fs" aria-live="polite"></p><ul class="tlist" id="fl"></ul><p><button class="btn ghost" id="fm" type="button" hidden></button></p>
<p class="note">{t["note"]} {t["checked"]} {datetime.date.fromisoformat(CHECKED).strftime("%d/%m/%Y")}.</p></section>
<script>{{const D={D};const T={json.dumps(t, ensure_ascii=False)};let P=null,N=12;
const q=document.getElementById('fq'),r=document.getElementById('fr'),L=document.getElementById('fl'),S=document.getElementById('fs');
const km=(a,b,c,d)=>{{const R=6371,x=(c-a)*Math.PI/180,y=(d-b)*Math.PI/180,h=Math.sin(x/2)**2+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(y/2)**2;return 2*R*Math.asin(Math.sqrt(h))}};
const fd=s=>new Date(s+'T12:00:00').toLocaleDateString('{loc}',{{weekday:'short',day:'numeric',month:'short'}});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
function draw(){{const rad=+r.value;let x=D.map(o=>({{...o,k:P?km(P[0],P[1],o.la,o.lo):null}}));
if(P&&rad)x=x.filter(o=>o.k<=rad);x.sort((a,b)=>a.s<b.s?-1:a.s>b.s?1:0);
S.textContent=x.length?x.length+' '+T.found+(P&&P[2]?' · '+P[2]:''):T.none;
const M=document.getElementById('fm');M.hidden=x.length<=N;M.textContent=T.more+' ('+(x.length-N)+')';L.innerHTML=x.slice(0,N).map(o=>`<li><div class="td"><b>${{esc(fd(o.s))}}</b>${{o.e!==o.s?'<span> → '+esc(fd(o.e))+'</span>':''}}</div><div class="ti"><span class="lv">${{esc(o.l)}}</span><strong>${{esc(o.n)}}</strong><span class="meta">${{esc(o.c)}} (${{esc(o.d)}})${{o.k!=null?' · '+Math.round(o.k)+' '+T.km:''}}</span><a href="${{esc(o.u)}}" rel="nofollow noopener" target="_blank" onclick="window.pbj&&pbj('clic_inscription_tournoi',this.dataset.n)" data-n="${{esc(o.n)}}">${{T.src}} →</a></div></li>`).join('')}}
async function geo(v){{try{{const j=await fetch('https://api-adresse.data.gouv.fr/search/?type=municipality&limit=1&q='+encodeURIComponent(v)).then(x=>x.json());const f=j.features&&j.features[0];if(!f){{S.textContent=T.notfound;return}}P=[f.geometry.coordinates[1],f.geometry.coordinates[0],f.properties.city];draw()}}catch(e){{S.textContent=T.notfound}}}}
document.getElementById('ff').addEventListener('submit',e=>{{e.preventDefault();const v=q.value.trim();if(v){{geo(v);window.pbj&&pbj('recherche_tournoi',v)}}}});
document.getElementById('fme').addEventListener('click',()=>{{if(!navigator.geolocation){{S.textContent=T.geo_err;return}}window.pbj&&pbj('autour_de_moi','');navigator.geolocation.getCurrentPosition(p=>{{P=[p.coords.latitude,p.coords.longitude,''];draw()}},()=>{{S.textContent=T.geo_err}},{{timeout:8000}})}});
r.addEventListener('change',()=>{{N=12;draw()}});document.getElementById('fm').addEventListener('click',()=>{{N+=12;draw()}});draw();}}</script>'''
