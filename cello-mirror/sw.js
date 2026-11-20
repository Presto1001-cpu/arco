// Caches the page shell and, as they are used, the hand and body models, so the mirror works offline after the first visit.
const SHELL = 'cello-mirror-shell-v3', RUNTIME = 'cello-mirror-models-v1';
const FILES = ['./', 'index.html', 'manifest.webmanifest', 'icon.svg'];
self.addEventListener('install', e => { e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== RUNTIME).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const models = url.hostname === 'cdn.jsdelivr.net' || url.hostname === 'storage.googleapis.com';
  if (url.origin === location.origin) {                      // page: network first so updates arrive, cache as the fallback
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(SHELL).then(x => x.put(req, c)); return r; }).catch(() => caches.match(req).then(r => r || caches.match('index.html'))));
  } else if (models) {                                       // models: cache first, they do not change
    e.respondWith(caches.open(RUNTIME).then(c => c.match(req).then(hit => hit || fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; }))));
  }
});
