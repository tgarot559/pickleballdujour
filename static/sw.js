// Service worker de Pickleball du Jour : pages lues disponibles hors connexion, notifications du conseil du jour.
const V = "__VERSION__";
const PAGES = "pbj-pages-v1", STATIC = "pbj-static-" + V;
const PRECACHE = ["/", "/conseils/", "/seances/", "/progresser/", "/hors-ligne/", "/style.css?v=" + V, "/favicon.svg", "/img/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(STATIC).then((c) => c.addAll(PRECACHE).catch(() => {})).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith("pbj-static-") && k !== STATIC).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

async function trimPages() {
  const c = await caches.open(PAGES), ks = await c.keys();
  for (let i = 0; i < ks.length - 80; i++) await c.delete(ks[i]);
}

self.addEventListener("fetch", (e) => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== "GET" || u.origin !== location.origin) return;
  if (u.pathname.startsWith("/admin") || /\.(mp4|xml)$/.test(u.pathname) || u.pathname === "/tip-du-jour.json") return;
  if (r.mode === "navigate") {
    // Réseau d'abord (contenu toujours à jour), copie gardée pour la lecture hors connexion
    e.respondWith(fetch(r).then((res) => {
      if (res.ok) { const cp = res.clone(); caches.open(PAGES).then((c) => c.put(r, cp)).then(trimPages); }
      return res;
    }).catch(async () => (await caches.match(r)) || (await caches.match("/hors-ligne/")) || Response.error()));
    return;
  }
  if (/\.(css|js|woff2|png|jpg|jpeg|svg|webp|vtt|ico|webmanifest)$/.test(u.pathname)) {
    e.respondWith(caches.open(STATIC).then(async (c) => {
      const hit = await c.match(r);
      const net = fetch(r).then((res) => { if (res.ok) c.put(r, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    }));
  }
});

// Notification sans contenu : on va chercher le conseil du jour au moment de l'afficher
self.addEventListener("push", (e) => {
  e.waitUntil(fetch("/tip-du-jour.json", { cache: "no-store" }).then((r) => r.json()).catch(() => null).then((t) =>
    self.registration.showNotification(t ? t.title : "Le conseil du jour est là", {
      body: t ? t.summary : "Un conseil de pickleball à essayer dès votre prochaine partie.",
      icon: "/img/icon-192.png", badge: "/img/icon-192.png", tag: "conseil-du-jour",
      data: { url: t ? t.url : "/" },
    })
  ));
});
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "/";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((cs) => {
    for (const c of cs) if ("focus" in c) { c.navigate(url); return c.focus(); }
    return self.clients.openWindow(url);
  }));
});
