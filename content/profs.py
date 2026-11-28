"""Annuaire « Trouver un prof ou un cours de pickleball » : liste vérifiée + inscriptions modérées (worker /profs)."""
import json

CHECKED = "2026-11-28"

# type : "cours" = cours ou séances encadrées annoncés publiquement ; "club" = lieu de jeu, se renseigner pour les cours
# (nom, type, ville, dept, lat, lon, détail FR, détail EN, lien)
LIST = [
    ("Le Pickleball Club Paris", "cours", "Paris 15e", "75", 48.8323, 2.2880, "Salle 100 % pickleball (6 terrains couverts) : cours réservables, jeu libre et location de terrains.", "Dedicated indoor venue (6 courts): bookable lessons, open play and court hire.", "https://lepickleballclub.fr/"),
    ("Cours de pickleball, centre sportif Vaugirard-Littré", "cours", "Paris 6e", "75", 48.8466, 2.3254, "Cours à l'année pour adolescents (dès 14 ans) et adultes, débutants comme confirmés.", "Year-round classes for teenagers (14+) and adults, beginners to advanced.", "https://www.paris.fr/activites/pickleball-le-jeu-de-balle-qui-met-tout-le-monde-en-mouvement-99937"),
    ("Pickle Arena Bordeaux", "cours", "Bordeaux", "33", 44.8663, -0.5536, "Centre 100 % pickleball aux Bassins à flot : initiations pour tous, cours et sessions encadrées.", "Dedicated pickleball centre: taster sessions, lessons and coached sessions.", "https://quoifaireabordeaux.com/pickle-arena-a-bordeaux/"),
    ("Pickleball Nantes", "cours", "Nantes", "44", 47.1905, -1.5300, "Club pionnier (2017) : entraînements le lundi et le mardi, jeu libre plusieurs fois par semaine.", "Pioneer club (2017): coached training on Mondays and Tuesdays, open play during the week.", "https://www.helloasso.com/associations/pickleball-nantes"),
    ("Tennis et Padel des Pertuis", "cours", "La Couarde-sur-Mer (île de Ré)", "17", 46.1960, -1.4280, "Cours et stages de pickleball toute l'année, en français et en anglais.", "Pickleball lessons and courses all year, in French and English.", "https://www.iledere.com/en/organizing-activities-and-leisure/sport-and-sensation/padel-and-pickleball-lessons-and-courses-run-by-tennis-et-padel-des-pertuis-la-couarde-sur-mer-en-5309792/"),
    ("Aulnay Loulay Tennis Club", "cours", "Loulay", "17", 46.0500, -0.5000, "Sessions de pickleball encadrées par les initiateurs du club, à Aulnay et Loulay.", "Pickleball sessions led by the club's instructors in Aulnay and Loulay.", "https://www.helloasso.com/associations/aulnay-loulay-tennis-club/adhesions/adhesion-2025-2026"),
    ("Tennis Club des Issambres", "cours", "Roquebrune-sur-Argens", "83", 43.3410, 6.7280, "3 terrains en bord de mer : cours collectifs ou individuels, stages débutants et perfectionnement.", "3 seafront courts: group or private lessons, beginner and improver courses.", "https://provence-alpes-cotedazur.com/en/offres/pickleball-roquebrune-sur-argens-en-5454650/"),
    ("Garden Tennis Club", "cours", "Cabourg", "14", 49.2840, -0.1190, "Terrains ouverts toute l'année et séances d'initiation.", "Courts open all year and introductory sessions.", "https://en.normandie-tourisme.fr/sports-and-leisure-activities/pickleball/"),
    ("Tennis Club Saint-Maixentais", "cours", "Saint-Maixent-l'École", "79", 46.4130, -0.2070, "Créneau pickleball découverte avec pratique encadrée, et formule compétition.", "Taster pickleball slot with coached play, plus a competition option.", "https://www.helloasso.com/associations/tennis-club-saint-maixentais/adhesions/formulaire-d-inscription-2026-2027"),
    ("Pickleball Trinité-Nice", "club", "La Trinité", "06", 43.7420, 7.3140, "Club historique de la Côte d'Azur, animé par un entraîneur.", "Long-standing Riviera club run by a coach.", "https://www.pickleheads.com/courts/fr/provence-alpes-cote-d'azur/la-trinite/gymnase-de-la-bourgade"),
    ("Pickleball and Co", "club", "Vaux-sur-Mer", "17", 45.6430, -1.0590, "Association affiliée à la FFT, 4 terrains couverts : rencontres et découverte.", "FFT-affiliated club, 4 indoor courts.", "https://www.helloasso.com/associations/pickleball-and-co-vaux-sur-mer"),
    ("Pickleball Port d'Envaux", "club", "Port-d'Envaux", "17", 45.8250, -0.6830, "Association loisir et compétition, tous âges et tous niveaux.", "Leisure and competition club, all ages and levels.", "https://www.helloasso.com/associations/pickleball-port-d-envaux"),
    ("Inpick, House of Pickleball", "club", "Saint-Priest (Lyon)", "69", 45.6960, 4.9440, "Lieu dédié au pickleball dans l'est lyonnais.", "Dedicated pickleball venue east of Lyon.", "https://1npick.fr/"),
    ("Joco Pickleball", "club", "Lille", "59", 50.6330, 3.0590, "Présenté comme le plus grand complexe de pickleball de France.", "Billed as France's largest pickleball complex.", "https://www.helloasso.com/associations/100-pickleball-tour/evenements/cpc-tour-etape-5-lille"),
    ("PB7", "club", "Saint-Jory (Toulouse)", "31", 43.7420, 1.3700, "Complexe de raquettes au nord de Toulouse, terrains de pickleball couverts.", "Racket complex north of Toulouse with indoor pickleball courts.", "https://urbansportsclub.com/fr/venues/pb7"),
    ("Pickleball Time", "club", "Nîmes", "30", 43.8090, 4.3900, "Complexe dédié : 5 terrains couverts et 2 extérieurs, ouvert tous les jours.", "Dedicated venue: 5 indoor and 2 outdoor courts, open daily.", "https://www.tourismegard.com/fr/fiche/equipement/pickleball-time-nimes_TFO7832495/"),
    ("Raquette Club Port Camargue", "club", "Le Grau-du-Roi", "30", 43.5230, 4.1340, "12 terrains de pickleball.", "12 pickleball courts.", "https://www.objectifgard.com/actualites/pratiques-insolites-le-pickleball-tres-en-vogue-a-port-camargue-132267.php"),
    ("Modern Squash", "club", "Marseille 14e", "13", 43.3330, 5.3900, "Complexe multi-raquettes : pickleball en salle, cours possibles (se renseigner).", "Multi-racket centre with indoor pickleball; ask about lessons.", "https://www.marseille-tourisme.com/offres/modern-squash-marseille-14eme-fr-3381742/"),
    ("Tennis Club de Saint-Julien", "club", "Marseille 12e", "13", 43.3130, 5.4490, "Club de tennis avec une section pickleball et des tournois officiels.", "Tennis club with a pickleball section and official tournaments.", "https://www.helloasso.com/associations/tennis-club-de-saint-julien"),
    ("Club de Guénange", "club", "Guénange", "57", 49.2990, 6.2010, "Section pickleball avec un formateur au club.", "Pickleball section with an instructor.", "https://www.guenange.fr/UserFiles/File/revue-de-presse/2026/mars/qu-est-ce-que-le-pickleball-ce-sport-de-raquette-en-plein-essor-a-bertrange-et-guenange.pdf"),
]

TXT = {
 "fr": {"h": "Trouver un prof ou un cours près de chez vous", "ph": "Ville ou code postal", "go": "Chercher", "me": "Autour de moi",
        "r": "Rayon", "all": "Toute la France", "km": "km", "found": "adresses", "none": "Rien dans ce rayon pour l'instant. Élargissez la zone, ou demandez au club de tennis le plus proche : plus de 1 000 clubs FFT proposent le pickleball.",
        "only": "Seulement les cours", "cours": "Cours", "club": "Club · se renseigner", "see": "Voir", "more": "Voir plus", "checked": "Liste vérifiée le",
        "geo_err": "Position indisponible. Tapez plutôt une ville.", "notfound": "Ville introuvable. Essayez un code postal.", "new": "Inscrit",
        "note": "« Cours » : la structure annonce des cours ou des séances encadrées. « Club » : on y joue, demandez-leur s'il y a des cours. Votre position reste sur votre téléphone."},
 "en": {"h": "Find a coach or a class near you", "ph": "Town or postcode (France)", "go": "Search", "me": "Near me",
        "r": "Radius", "all": "All of France", "km": "km", "found": "places", "none": "Nothing within this radius yet. Try a wider area, or ask the nearest tennis club: over 1,000 FFT clubs offer pickleball.",
        "only": "Lessons only", "cours": "Lessons", "club": "Club · ask", "see": "Open", "more": "Show more", "checked": "List checked on",
        "geo_err": "Location unavailable. Type a town instead.", "notfound": "Town not found. Try a postcode.", "new": "Listed",
        "note": "“Lessons”: the venue advertises lessons or coached sessions. “Club”: you can play there, ask them about lessons. Your location stays on your phone."},
}

FORM = {
 "fr": {"h": "Vous êtes prof, club ou salle ? Faites-vous recenser", "p": "C'est gratuit. Chaque fiche est relue avant d'apparaître sur la carte.",
        "nom": "Nom (vous ou votre structure)", "type": "Vous êtes", "t1": "Prof ou entraîneur", "t2": "Club ou association", "t3": "Salle ou complexe",
        "ville": "Ville", "cp": "Code postal", "url": "Site, page ou réseau social", "email": "E-mail de contact", "email_n": "jamais publié : seulement pour vous joindre",
        "niv": "Pour qui ?", "niv_ph": "Débutants, enfants, compétition…", "dip": "Diplôme ou qualification", "dip_ph": "DE tennis, initiateur, module pickleball FFT…",
        "msg": "Ce que vous proposez", "msg_ph": "Cours collectifs le mardi soir, stages pendant les vacances…",
        "ok": "Je confirme que ces informations sont exactes et j'accepte qu'elles soient publiées (sauf l'e-mail).", "send": "Envoyer ma fiche",
        "thanks": "Merci ! Votre fiche sera publiée après relecture.", "err": "L'envoi n'a pas fonctionné. Écrivez-nous à contact@pickleballdujour.fr.",
        "e_nom": "Indiquez un nom.", "e_ville": "Indiquez la ville.", "e_mail": "Indiquez un e-mail valide pour qu'on puisse vous joindre.", "e_ok": "Cochez la case de confirmation."},
 "en": {"h": "Are you a coach, club or venue? Get listed", "p": "It's free. Every listing is checked before it appears on the map.",
        "nom": "Name (you or your organisation)", "type": "You are", "t1": "Coach", "t2": "Club or association", "t3": "Venue",
        "ville": "Town", "cp": "Postcode", "url": "Website, page or social profile", "email": "Contact e-mail", "email_n": "never published: only to reach you",
        "niv": "Who for?", "niv_ph": "Beginners, kids, competition…", "dip": "Qualification", "dip_ph": "State tennis diploma, FFT pickleball module…",
        "msg": "What you offer", "msg_ph": "Group lessons on Tuesday evenings, holiday camps…",
        "ok": "I confirm this information is accurate and agree to its publication (except the e-mail).", "send": "Send my listing",
        "thanks": "Thank you! Your listing will go live after review.", "err": "Sending failed. Write to contact@pickleballdujour.fr.",
        "e_nom": "Enter a name.", "e_ville": "Enter the town.", "e_mail": "Enter a valid e-mail so we can reach you.", "e_ok": "Tick the confirmation box."},
}


def data(lang):
    return [dict(n=n, t=t, c=c, d=d, la=la, lo=lo, x=(fr if lang == "fr" else en), u=u) for (n, t, c, d, la, lo, fr, en, u) in LIST]


def profs_html(lang, api):
    t, f = TXT[lang], FORM[lang]
    D = json.dumps(data(lang), ensure_ascii=False)
    d = CHECKED.split("-")
    chk = f"{d[2]}/{d[1]}/{d[0]}" if lang == "fr" else f"{d[2]}/{d[1]}/{d[0]}"
    return f'''<section class="finder" id="recherche"><h2 style="margin-top:0">{t["h"]}</h2>
<form id="pf" class="ffrow" role="search"><label class="sr" for="pq">{t["ph"]}</label><input id="pq" type="search" inputmode="search" autocomplete="address-level2" placeholder="{t["ph"]}"><button class="btn" type="submit">{t["go"]}</button></form>
<div class="ffrow"><button class="btn ghost" id="pme" type="button">◎ {t["me"]}</button>
<label class="sr" for="pr">{t["r"]}</label><select id="pr"><option value="50">50 {t["km"]}</option><option value="100" selected>100 {t["km"]}</option><option value="200">200 {t["km"]}</option><option value="0">{t["all"]}</option></select>
<label class="pfonly"><input type="checkbox" id="po"> {t["only"]}</label></div>
<p class="meta" id="ps" aria-live="polite"></p><ul class="tlist plist" id="pl"></ul><p><button class="btn ghost" id="pm" type="button" hidden></button></p>
<p class="note">{t["note"]} {t["checked"]} {chk}.</p></section>
<details class="avisform proform" id="inscription"><summary>{f["h"]}</summary><p class="note" style="margin-top:8px">{f["p"]}</p>
<form id="prf" novalidate>
<label>{f["nom"]} <input name="nom" maxlength="80" required></label>
<label>{f["type"]} <select name="type"><option value="prof">{f["t1"]}</option><option value="club">{f["t2"]}</option><option value="salle">{f["t3"]}</option></select></label>
<div class="avrow"><label>{f["ville"]} <input name="ville" maxlength="60" autocomplete="address-level2" required></label><label>{f["cp"]} <input name="cp" maxlength="5" inputmode="numeric" autocomplete="postal-code"></label></div>
<label>{f["url"]} <input name="url" type="url" maxlength="200" inputmode="url" placeholder="https://"></label>
<label>{f["email"]} <span class="opt">{f["email_n"]}</span><input name="email" type="email" maxlength="120" autocomplete="email" inputmode="email" required></label>
<label>{f["niv"]} <input name="niveaux" maxlength="120" placeholder="{f["niv_ph"]}"></label>
<label>{f["dip"]} <input name="diplome" maxlength="120" placeholder="{f["dip_ph"]}"></label>
<label>{f["msg"]} <textarea name="texte" rows="3" maxlength="500" placeholder="{f["msg_ph"]}"></textarea></label>
<input name="site" tabindex="-1" autocomplete="off" class="hp" aria-hidden="true">
<label class="chk"><input type="checkbox" name="accord" required> {f["ok"]}</label>
<button class="btn" type="submit">{f["send"]}</button><p class="avmsg" id="prmsg" aria-live="polite"></p>
</form></details>
<script>{{const D={D};const T={json.dumps(t, ensure_ascii=False)};const F={json.dumps(f, ensure_ascii=False)};const A='{api}';let P=null,N=12;
const q=document.getElementById('pq'),r=document.getElementById('pr'),o=document.getElementById('po'),L=document.getElementById('pl'),S=document.getElementById('ps');
const km=(a,b,c,d)=>{{const R=6371,x=(c-a)*Math.PI/180,y=(d-b)*Math.PI/180,h=Math.sin(x/2)**2+Math.cos(a*Math.PI/180)*Math.cos(c*Math.PI/180)*Math.sin(y/2)**2;return 2*R*Math.asin(Math.sqrt(h))}};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
const safe=u=>/^https?:\\/\\//i.test(u||'')?u:'';
function draw(){{const rad=+r.value;let x=D.map(e=>({{...e,k:P?km(P[0],P[1],e.la,e.lo):null}}));if(o.checked)x=x.filter(e=>e.t==='cours');
if(P&&rad)x=x.filter(e=>e.k<=rad);x.sort((a,b)=>P?a.k-b.k:(a.t===b.t?a.c.localeCompare(b.c):a.t==='cours'?-1:1));
S.textContent=x.length?x.length+' '+T.found+(P&&P[2]?' · '+P[2]:''):T.none;const M=document.getElementById('pm');M.hidden=x.length<=N;M.textContent=T.more+' ('+(x.length-N)+')';
L.innerHTML=x.slice(0,N).map(e=>`<li><div class="ti"><span class="lv ${{e.t==='cours'?'':'lvc'}}">${{e.t==='cours'?T.cours:T.club}}</span><strong>${{esc(e.n)}}</strong><span class="meta">${{esc(e.c)}} (${{esc(e.d)}})${{e.k!=null?' · '+Math.round(e.k)+' '+T.km:''}}</span><span>${{esc(e.x)}}</span>${{safe(e.u)?`<a href="${{esc(safe(e.u))}}" rel="nofollow noopener" target="_blank" onclick="window.pbj&&pbj('clic_prof',this.dataset.n)" data-n="${{esc(e.n)}}">${{T.see}} →</a>`:''}}</div></li>`).join('')}}
async function geo(v){{try{{const j=await fetch('https://api-adresse.data.gouv.fr/search/?type=municipality&limit=1&q='+encodeURIComponent(v)).then(x=>x.json());const f=j.features&&j.features[0];if(!f)return null;return [f.geometry.coordinates[1],f.geometry.coordinates[0],f.properties.city,f.properties.context]}}catch(e){{return null}}}}
document.getElementById('pf').addEventListener('submit',async e=>{{e.preventDefault();const v=q.value.trim();if(!v)return;window.pbj&&pbj('recherche_prof',v);const g=await geo(v);if(!g){{S.textContent=T.notfound;return}}P=g;N=12;draw()}});
document.getElementById('pme').addEventListener('click',()=>{{if(!navigator.geolocation){{S.textContent=T.geo_err;return}}window.pbj&&pbj('autour_de_moi','profs');navigator.geolocation.getCurrentPosition(p=>{{P=[p.coords.latitude,p.coords.longitude,''];N=12;draw()}},()=>{{S.textContent=T.geo_err}},{{timeout:8000}})}});
r.addEventListener('change',()=>{{N=12;draw()}});o.addEventListener('change',()=>{{N=12;draw()}});document.getElementById('pm').addEventListener('click',()=>{{N+=12;draw()}});draw();
fetch(A+'/profs/publics').then(x=>{{if(!x.ok)throw 0;return x.json()}}).then(j=>{{(j.profs||[]).forEach(p=>{{if(p.la&&p.lo)D.push({{n:p.nom,t:'cours',c:p.ville,d:p.dept||'',la:+p.la,lo:+p.lo,x:[p.texte,p.niveaux,p.diplome].filter(Boolean).join(' · '),u:p.url}})}});draw()}}).catch(()=>{{}});
const PF=document.getElementById('prf'),PM=document.getElementById('prmsg');
PF.addEventListener('submit',async e=>{{e.preventDefault();const f=new FormData(PF);const d=Object.fromEntries(['nom','type','ville','cp','url','email','niveaux','diplome','texte','site'].map(k=>[k,(f.get(k)||'').trim()]));d.accord=!!f.get('accord');
if(d.nom.length<2){{PM.textContent=F.e_nom;return}}if(d.ville.length<2){{PM.textContent=F.e_ville;return}}if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(d.email)){{PM.textContent=F.e_mail;return}}if(!d.accord){{PM.textContent=F.e_ok;return}}
PM.textContent='…';const g=await geo((d.cp?d.cp+' ':'')+d.ville);if(g){{d.la=g[0];d.lo=g[1];d.dept=(g[3]||'').split(',')[0].trim()}}
try{{const x=await fetch(A+'/profs',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}});if(!x.ok)throw 0;PF.reset();PM.textContent=F.thanks;window.pbj&&pbj('inscription_prof',d.type)}}
catch(err){{const b=Object.entries(d).filter(([k])=>!['site','accord'].includes(k)).map(([k,v])=>k+' : '+v).join('\\n');location.href='mailto:contact@pickleballdujour.fr?subject='+encodeURIComponent('Inscription annuaire des profs : '+d.nom)+'&body='+encodeURIComponent(b);PM.textContent=F.thanks}}}});
}}</script>'''
