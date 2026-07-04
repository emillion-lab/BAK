// BakshishApp Service Worker
// Кешира файловете за офлайн работа

const CACHE_NAME = 'bakshishapp-bak-v3';
const STATIC_FILES = [
  '/BAK/',
  '/BAK/index.html',
  '/BAK/app.js',
  '/BAK/leaflet.min.js',
  '/BAK/leaflet.min.css',
  '/BAK/manifest.json',
];

// Инсталация — кешира статичните файлове
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_FILES);
    })
  );
  self.skipWaiting();
});

// Активация — изтрива стари кешове
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// Fetch — network first, cache fallback
// Динамичните файлове (flight-cache, config, weather) — винаги от мрежата
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // API заявки и динамични данни — само network, без кеш
  const dynamicPatterns = [
    'openweathermap.org',
    'aviationstack.com',
    'nominatim.openstreetmap.org',
    'flight-cache.json',
    'config.json',
  ];
  
  const isDynamic = dynamicPatterns.some(p => url.href.includes(p));
  
  if (isDynamic) {
    // Network only — при грешка, тихо пропуска
    event.respondWith(
      fetch(event.request).catch(() => new Response('{}', {
        headers: {'Content-Type': 'application/json'}
      }))
    );
    return;
  }

  // Статични файлове — network first, cache fallback
  event.respondWith(
    fetch(event.request, {cache: 'no-cache'})
      .then(response => {
        // Кешира успешните отговори
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
