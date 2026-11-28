// Statistiques de pickleballdujour.fr — Cloudflare Worker + base D1 (binding DB).
// Aucune adresse IP ni cookie stocké : un identifiant de visiteur quotidien est dérivé
// d'un hachage (IP + navigateur + date), non réversible, renouvelé chaque jour.
// À coller dans le Worker « pickleballdujour-stats ». Remplacer ADMIN_HASH par le SHA-256 du code d'accès.
const ADMIN_HASH = "__ADMIN_HASH__";
const ORIGINS = ["https://pickleballdujour.fr", "https://www.pickleballdujour.fr"];

const SCHEMA = [
  "CREATE TABLE IF NOT EXISTS avis (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, nom TEXT, ville TEXT, niveau TEXT, note INTEGER, texte TEXT, statut TEXT, vid TEXT, page TEXT)",
  "CREATE INDEX IF NOT EXISTS avis_statut ON avis(statut)",
  "CREATE TABLE IF NOT EXISTS hits (ts INTEGER, day TEXT, path TEXT, lang TEXT, ref TEXT, ref_host TEXT, src TEXT, utm TEXT, country TEXT, city TEXT, device TEXT, vid TEXT, ev TEXT, ev_val TEXT)",
  "CREATE INDEX IF NOT EXISTS hits_day ON hits(day)",
  "CREATE TABLE IF NOT EXISTS push_subs (endpoint TEXT PRIMARY KEY, ts INTEGER, lang TEXT)",
  "CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)",
];

// ---------- Notifications (Web Push sans contenu : le téléphone va chercher le conseil du jour) ----------
const VAPID_PUBLIC = "BAvVVsT0goxYtefwBLiCWDmNAXtPdmNKLj8IEi0DQSyJ2_miJbCINtOwXgXoSr_-kzuo5Q_jHNI0x1qW3XhHEBA";
const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const b64uStr = (s) => b64u(new TextEncoder().encode(s));
let _key = null;
async function vapidKey(env) {
  if (!_key) _key = await crypto.subtle.importKey("jwk", JSON.parse(env.VAPID_JWK), { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  return _key;
}
async function vapidJWT(env, aud) {
  const head = b64uStr(JSON.stringify({ typ: "JWT", alg: "ES256" }));
  const body = b64uStr(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: "mailto:contact@pickleballdujour.fr" }));
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, await vapidKey(env), new TextEncoder().encode(head + "." + body));
  return head + "." + body + "." + b64u(sig);
}
async function pushOne(env, endpoint) {
  const aud = new URL(endpoint).origin;
  const r = await fetch(endpoint, { method: "POST", headers: { Authorization: `vapid t=${await vapidJWT(env, aud)}, k=${VAPID_PUBLIC}`, TTL: "43200", Urgency: "normal", "Content-Length": "0" } });
  if (r.status === 404 || r.status === 410) await env.DB.prepare("DELETE FROM push_subs WHERE endpoint=?").bind(endpoint).run();
  return r.status;
}
async function pushAll(env) {
  const subs = (await env.DB.prepare("SELECT endpoint FROM push_subs").all()).results;
  const res = { total: subs.length, ok: 0, gone: 0, err: 0 };
  for (let i = 0; i < subs.length; i += 40) {
    const st = await Promise.all(subs.slice(i, i + 40).map((x) => pushOne(env, x.endpoint).catch(() => 0)));
    for (const c of st) c >= 200 && c < 300 ? res.ok++ : c === 404 || c === 410 ? res.gone++ : res.err++;
  }
  return res;
}
async function dailyPush(env) {
  const today = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris" }).format(new Date());
  const last = (await env.DB.prepare("SELECT v FROM meta WHERE k='push_last'").all()).results[0];
  if (last && last.v === today) return { skip: "deja envoye" };
  const tip = await fetch("https://pickleballdujour.fr/tip-du-jour.json", { cf: { cacheTtl: 0 } }).then((r) => r.json()).catch(() => null);
  if (!tip || tip.date !== today) return { skip: "pas de nouveau conseil" };
  const res = await pushAll(env);
  await env.DB.prepare("INSERT OR REPLACE INTO meta (k, v) VALUES ('push_last', ?)").bind(today).run();
  return res;
}

function cors(req) {
  const o = req.headers.get("Origin") || "";
  return { "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : ORIGINS[0], "Access-Control-Allow-Methods": "GET,POST,OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin" };
}
const json = (d, h, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "Content-Type": "application/json", ...h } });

async function sha(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}

function classify(host) {
  if (!host) return "Direct";
  const h = host.replace(/^www\./, "");
  if (h.endsWith("pickleballdujour.fr") || h.endsWith("pickleballdujour.com")) return "Interne";
  const map = [
    [/chatgpt\.com|openai\.com/, "IA · ChatGPT"], [/perplexity\.ai/, "IA · Perplexity"], [/claude\.ai/, "IA · Claude"],
    [/gemini\.google|bard\.google/, "IA · Gemini"], [/copilot\.microsoft|bing\.com\/chat/, "IA · Copilot"], [/mistral\.ai|chat\.mistral/, "IA · Le Chat"],
    [/google\./, "Recherche · Google"], [/bing\.com/, "Recherche · Bing"], [/duckduckgo/, "Recherche · DuckDuckGo"], [/qwant/, "Recherche · Qwant"], [/ecosia/, "Recherche · Ecosia"], [/yahoo/, "Recherche · Yahoo"],
    [/facebook\.com|fb\.com|m\.facebook/, "Réseau · Facebook"], [/instagram/, "Réseau · Instagram"], [/linkedin|lnkd\.in/, "Réseau · LinkedIn"], [/t\.co$|twitter|x\.com/, "Réseau · X"], [/tiktok/, "Réseau · TikTok"], [/youtube|youtu\.be/, "Réseau · YouTube"], [/whatsapp/, "Messagerie · WhatsApp"],
    [/mail\.google|outlook|brevo|sendibt|mailchi|kit\.com/, "E-mail"],
  ];
  for (const [re, name] of map) if (re.test(h)) return name;
  return "Site · " + h;
}

function device(ua, w) {
  if (/bot|crawl|spider|slurp|preview|headless/i.test(ua)) return "bot";
  if (/iPad|Tablet/i.test(ua) || (w >= 600 && w < 1024 && /Mobi|Android/i.test(ua))) return "Tablette";
  if (/Mobi|iPhone|Android/i.test(ua)) return "Mobile";
  return "Ordinateur";
}

async function hit(req, env) {
  let b = {};
  try { b = JSON.parse(await req.text() || "{}"); } catch (e) {}
  const ua = req.headers.get("User-Agent") || "";
  const dev = device(ua, +b.w || 0);
  if (dev === "bot") return;
  const now = new Date(), day = now.toISOString().slice(0, 10);
  let refHost = "";
  try { refHost = b.r ? new URL(b.r).hostname : ""; } catch (e) {}
  const ip = req.headers.get("CF-Connecting-IP") || "";
  const vid = (await sha(ip + "|" + ua + "|" + day)).slice(0, 16);
  const cf = req.cf || {};
  await env.DB.prepare("INSERT INTO hits VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)").bind(
    now.getTime(), day, String(b.p || "/").slice(0, 200), String(b.l || "").slice(0, 10), String(b.r || "").slice(0, 300), refHost,
    classify(refHost), String(b.u || "").slice(0, 100), cf.country || "", cf.city || "", dev, vid, String(b.e || "").slice(0, 30), String(b.v || "").slice(0, 100)
  ).run();
}

async function stats(url, env) {
  const days = Math.min(Math.max(+url.searchParams.get("days") || 30, 1), 365);
  const since = new Date(Date.now() - (days - 1) * 864e5).toISOString().slice(0, 10);
  const prev = new Date(Date.now() - (2 * days - 1) * 864e5).toISOString().slice(0, 10);
  const q = (sql, ...a) => { const st = env.DB.prepare(sql); return (sql.includes("?") ? st.bind(...(a.length ? a : [since])) : st).all().then(r => r.results); };
  const pv = "ev=''";
  const CAT = "CASE WHEN instr(src,' · ')>0 THEN substr(src,1,instr(src,' · ')-1) ELSE src END";
  // heure de Paris (UTC+1 l'hiver, +2 l'été)
  const H = "CAST(strftime('%H', ts/1000, 'unixepoch', CASE WHEN strftime('%m', ts/1000, 'unixepoch') BETWEEN '04' AND '10' THEN '+2 hours' ELSE '+1 hours' END) AS INTEGER)";
  const FIN = "ev='_fin' AND CAST(ev_val AS INTEGER) BETWEEN 3 AND 1800";
  const [[tot], [old], res] = await Promise.all([
    q(`SELECT COUNT(*) views, COUNT(DISTINCT vid||day) visitors FROM hits WHERE day>=? AND ${pv}`),
    q(`SELECT COUNT(*) views, COUNT(DISTINCT vid||day) visitors FROM hits WHERE day>=? AND day<? AND ${pv}`, prev, since),
    Promise.all([
      q(`SELECT day, COUNT(*) views, COUNT(DISTINCT vid) visitors FROM hits WHERE day>=? AND ${pv} GROUP BY day ORDER BY day`),
      q(`SELECT path k, COUNT(*) n, COUNT(DISTINCT vid||day) u FROM hits WHERE day>=? AND ${pv} GROUP BY path ORDER BY n DESC LIMIT 60`),
      q(`SELECT src k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} AND src<>'Interne' GROUP BY src ORDER BY n DESC LIMIT 40`),
      q(`SELECT ref k, COUNT(*) n FROM hits WHERE day>=? AND ${pv} AND ref<>'' AND src<>'Interne' GROUP BY ref ORDER BY n DESC LIMIT 40`),
      q(`SELECT utm k, COUNT(*) n FROM hits WHERE day>=? AND ${pv} AND utm<>'' GROUP BY utm ORDER BY n DESC LIMIT 20`),
      q(`SELECT country k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} GROUP BY country ORDER BY n DESC LIMIT 30`),
      q(`SELECT city||' ('||country||')' k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} AND city<>'' GROUP BY city, country ORDER BY n DESC LIMIT 30`),
      q(`SELECT device k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} GROUP BY device ORDER BY n DESC`),
      q(`SELECT lang k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} GROUP BY lang ORDER BY n DESC LIMIT 12`),
      q(`SELECT ev||CASE WHEN ev_val<>'' THEN ' · '||ev_val ELSE '' END k, COUNT(*) n FROM hits WHERE day>=? AND ev<>'' AND substr(ev,1,1)<>'_' GROUP BY ev, ev_val ORDER BY n DESC LIMIT 60`),
      q(`SELECT ts, path, src, city, country, device FROM hits WHERE day>=? AND ${pv} ORDER BY ts DESC LIMIT 30`),
      // nouveautés
      q(`SELECT day, ${CAT} cat, COUNT(*) n FROM (SELECT vid, day, src, MIN(ts) FROM hits WHERE day>=? AND ${pv} GROUP BY vid, day) GROUP BY day, cat`),
      q(`SELECT ${CAT} k, COUNT(*) n FROM (SELECT vid, day, src, MIN(ts) FROM hits WHERE day>=? AND ${pv} GROUP BY vid, day) GROUP BY k ORDER BY n DESC`),
      q(`SELECT path k, COUNT(*) n FROM (SELECT vid, day, path, MIN(ts) FROM hits WHERE day>=? AND ${pv} GROUP BY vid, day) GROUP BY path ORDER BY n DESC LIMIT 30`),
      q(`SELECT SUM(c=1) one, COUNT(*) n FROM (SELECT COUNT(*) c FROM hits WHERE day>=? AND ${pv} GROUP BY vid, day)`),
      q(`SELECT ${H} k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} GROUP BY k ORDER BY k`),
      q(`SELECT CAST(strftime('%w', day) AS INTEGER) k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} GROUP BY k ORDER BY k`),
      q(`SELECT AVG(CAST(ev_val AS INTEGER)) s, COUNT(*) n, AVG(CAST(substr(ev_val, instr(ev_val,'|')+1) AS INTEGER)) sc FROM hits WHERE day>=? AND ${FIN}`),
      q(`SELECT path k, ROUND(AVG(CAST(ev_val AS INTEGER))) s, ROUND(AVG(CAST(substr(ev_val, instr(ev_val,'|')+1) AS INTEGER))) sc, COUNT(*) n FROM hits WHERE day>=? AND ${FIN} GROUP BY path HAVING n>=1 ORDER BY n DESC LIMIT 40`),
      q(`SELECT ev k, COUNT(*) n FROM hits WHERE day>=? AND ev IN ('clic_newsletter','quiz_resultat','lecture_seance','notif_abonne','avis_envoye','telechargement_livret','clic_inscription','recherche_tournoi') GROUP BY ev`),
      q(`SELECT ev k, COUNT(*) n FROM hits WHERE day>=? AND day<? AND ev IN ('clic_newsletter','quiz_resultat','lecture_seance','notif_abonne','avis_envoye','telechargement_livret','clic_inscription','recherche_tournoi') GROUP BY ev`, prev, since),
      q(`SELECT (SELECT COUNT(*) FROM push_subs) push, (SELECT COUNT(*) FROM avis WHERE statut='publie') avis_pub, (SELECT COUNT(*) FROM avis WHERE statut='attente') avis_att, (SELECT COUNT(*) FROM hits WHERE ev='appli_invite' AND ev_val='accepted') installs`),
    ]),
  ]);
  const [series, pages, sources, refs, utm, countries, cities, devices, langs, events, live, chan_day, channels, landing, [bn], hours, wdays, [dur], page_dur, goals, goals_prev, [totals]] = res;
  return { v: 2, days, since, views: tot.views, visitors: tot.visitors, prev: old, series, pages, sources, refs, utm, countries, cities, devices, langs, events, live,
    chan_day, channels, landing, bounce: bn && bn.n ? bn.one / bn.n : null, hours, wdays, dur: dur && dur.n ? Math.round(dur.s) : null, scroll: dur && dur.n ? Math.round(dur.sc) : null,
    page_dur, goals, goals_prev, totals };
}

// ---------- Avis des joueurs : dépôt public, modération dans la console, publication ----------
const clean = (v, n) => String(v || "").replace(/[\u0000-\u001f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, n);
async function avisDepot(req, env) {
  let b = {};
  try { b = JSON.parse(await req.text() || "{}"); } catch (e) { return [400, { error: "format" }]; }
  if (b.site) return [200, { ok: true }];                       // champ piège anti-robots
  const nom = clean(b.nom, 40), ville = clean(b.ville, 40), niveau = clean(b.niveau, 20), texte = clean(b.texte, 600), note = Math.round(+b.note);
  if (nom.length < 2 || texte.length < 20 || !(note >= 1 && note <= 5) || b.accord !== true) return [400, { error: "champs" }];
  const ip = req.headers.get("CF-Connecting-IP") || "", day = new Date().toISOString().slice(0, 10);
  const vid = (await sha(ip + "|avis|" + day)).slice(0, 16);
  const [{ n }] = (await env.DB.prepare("SELECT COUNT(*) n FROM avis WHERE vid=?").bind(vid).all()).results;
  if (n >= 3) return [429, { error: "limite" }];
  await env.DB.prepare("INSERT INTO avis (ts,nom,ville,niveau,note,texte,statut,vid,page) VALUES (?,?,?,?,?,?,?,?,?)")
    .bind(Date.now(), nom, ville, niveau, note, texte, "attente", vid, clean(b.page, 120)).run();
  return [200, { ok: true }];
}

export default {
  async scheduled(event, env, ctx) { ctx.waitUntil(dailyPush(env)); },
  async fetch(req, env, ctx) {
    const url = new URL(req.url), h = cors(req);
    if (req.method === "OPTIONS") return new Response(null, { headers: h });
    if (url.pathname === "/setup") { for (const s of SCHEMA) await env.DB.prepare(s).run(); return json({ ok: true }, h); }
    if (url.pathname === "/hit" && req.method === "POST") { ctx.waitUntil(hit(req, env).catch(() => {})); return new Response(null, { status: 204, headers: h }); }
    if (url.pathname === "/push/sub" && req.method === "POST") {
      let b = {}; try { b = JSON.parse(await req.text() || "{}"); } catch (e) {}
      const ep = String(b.endpoint || "");
      if (!/^https:\/\/[a-z0-9.-]+\//i.test(ep) || ep.length > 600) return json({ error: "endpoint" }, h, 400);
      await env.DB.prepare("INSERT OR REPLACE INTO push_subs (endpoint, ts, lang) VALUES (?,?,?)").bind(ep, Date.now(), String(b.lang || "fr").slice(0, 5)).run();
      return json({ ok: true }, h);
    }
    if (url.pathname === "/push/unsub" && req.method === "POST") {
      let b = {}; try { b = JSON.parse(await req.text() || "{}"); } catch (e) {}
      await env.DB.prepare("DELETE FROM push_subs WHERE endpoint=?").bind(String(b.endpoint || "")).run();
      return json({ ok: true }, h);
    }
    if (url.pathname.startsWith("/push/admin")) {
      const k = url.searchParams.get("k") || "";
      if (!k || (await sha(k)) !== ADMIN_HASH) return json({ error: "code" }, h, 401);
      if (url.searchParams.get("send") === "1") return json(await pushAll(env), h);
      if (url.searchParams.get("daily") === "1") return json(await dailyPush(env), h);
      const [{ n }] = (await env.DB.prepare("SELECT COUNT(*) n FROM push_subs").all()).results;
      return json({ abonnes: n }, h);
    }
    if (url.pathname === "/avis" && req.method === "POST") { const [st, d] = await avisDepot(req, env); return json(d, h, st); }
    if (url.pathname === "/avis/publics") {
      const r = await env.DB.prepare("SELECT id, ts, nom, ville, niveau, note, texte FROM avis WHERE statut='publie' ORDER BY ts DESC LIMIT 60").all();
      return json({ avis: r.results }, { ...h, "Cache-Control": "public, max-age=120" });
    }
    if (url.pathname.startsWith("/avis/admin")) {
      const k = url.searchParams.get("k") || "";
      if (!k || (await sha(k)) !== ADMIN_HASH) return json({ error: "code" }, h, 401);
      if (req.method === "POST") {
        let b = {}; try { b = JSON.parse(await req.text() || "{}"); } catch (e) {}
        const id = Math.round(+b.id);
        if (b.action === "supprimer") await env.DB.prepare("DELETE FROM avis WHERE id=?").bind(id).run();
        else if (["publie", "refuse", "attente"].includes(b.action)) await env.DB.prepare("UPDATE avis SET statut=? WHERE id=?").bind(b.action, id).run();
        return json({ ok: true }, h);
      }
      const r = await env.DB.prepare("SELECT id, ts, nom, ville, niveau, note, texte, statut, page FROM avis ORDER BY (statut='attente') DESC, ts DESC LIMIT 200").all();
      return json({ avis: r.results }, h);
    }
    if (url.pathname === "/stats") {
      const k = url.searchParams.get("k") || "";
      if (!k || (await sha(k)) !== ADMIN_HASH) return json({ error: "code" }, h, 401);
      return json(await stats(url, env), h);
    }
    return new Response("pickleballdujour-stats", { headers: h });
  },
};
