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
];

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
  const q = (sql) => env.DB.prepare(sql).bind(since).all().then(r => r.results);
  const pv = "ev=''";
  const [tot] = await q(`SELECT COUNT(*) views, COUNT(DISTINCT vid||day) visitors FROM hits WHERE day>=? AND ${pv}`);
  const [res] = await Promise.all([Promise.all([
    q(`SELECT day, COUNT(*) views, COUNT(DISTINCT vid) visitors FROM hits WHERE day>=? AND ${pv} GROUP BY day ORDER BY day`),
    q(`SELECT path k, COUNT(*) n FROM hits WHERE day>=? AND ${pv} GROUP BY path ORDER BY n DESC LIMIT 40`),
    q(`SELECT src k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} AND src<>'Interne' GROUP BY src ORDER BY n DESC LIMIT 40`),
    q(`SELECT ref k, COUNT(*) n FROM hits WHERE day>=? AND ${pv} AND ref<>'' AND src<>'Interne' GROUP BY ref ORDER BY n DESC LIMIT 40`),
    q(`SELECT utm k, COUNT(*) n FROM hits WHERE day>=? AND ${pv} AND utm<>'' GROUP BY utm ORDER BY n DESC LIMIT 20`),
    q(`SELECT country k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} GROUP BY country ORDER BY n DESC LIMIT 30`),
    q(`SELECT city||' ('||country||')' k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} AND city<>'' GROUP BY city, country ORDER BY n DESC LIMIT 30`),
    q(`SELECT device k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} GROUP BY device ORDER BY n DESC`),
    q(`SELECT lang k, COUNT(DISTINCT vid||day) n FROM hits WHERE day>=? AND ${pv} GROUP BY lang ORDER BY n DESC LIMIT 12`),
    q(`SELECT ev||' · '||ev_val k, COUNT(*) n FROM hits WHERE day>=? AND ev<>'' GROUP BY ev, ev_val ORDER BY n DESC LIMIT 40`),
    q(`SELECT ts, path, src, city, country, device FROM hits WHERE day>=? AND ${pv} ORDER BY ts DESC LIMIT 30`),
  ])]);
  const [series, pages, sources, refs, utm, countries, cities, devices, langs, events, live] = res;
  return { days, since, views: tot.views, visitors: tot.visitors, series, pages, sources, refs, utm, countries, cities, devices, langs, events, live };
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
  async fetch(req, env, ctx) {
    const url = new URL(req.url), h = cors(req);
    if (req.method === "OPTIONS") return new Response(null, { headers: h });
    if (url.pathname === "/setup") { for (const s of SCHEMA) await env.DB.prepare(s).run(); return json({ ok: true }, h); }
    if (url.pathname === "/hit" && req.method === "POST") { ctx.waitUntil(hit(req, env).catch(() => {})); return new Response(null, { status: 204, headers: h }); }
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
