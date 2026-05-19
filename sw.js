const CACHE_NAME = 'tunika-erp-v1';
// List of static assets to cache (add more if needed)
const urlsToCache = [
    './index.html',
    './manifest.json',
    './styles.css', // optional stylesheet
    './app.js'      // main JS if exists
];

self.addEventListener('install', event => {
    // Activate new service worker immediately
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('activate', event => {
    // Take control of all clients as soon as activation completes
    self.clients.claim();
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (!cacheWhitelist.includes(cacheName)) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

self.addEventListener('fetch', event => {
    const request = event.request;
    // Bypass caching for API calls – always fetch from network
    if (request.url.includes('/api/')) {
        event.respondWith(fetch(request));
        return;
    }
    // Navigation requests (HTML) – network first, fallback to cache
    if (request.mode === 'navigate' || request.destination === 'document') {
        event.respondWith(
            fetch(request)
                .then(networkResponse => {
                    // Update cache with fresh HTML
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, networkResponse.clone());
                        return networkResponse;
                    });
                })
                .catch(() => caches.match(request))
        );
        return;
    }
    // Other static assets – cache first, then network
    event.respondWith(
        caches.match(request).then(cachedResponse => {
            if (cachedResponse) {
                return cachedResponse;
            }
            // Try network and cache the response for future use
            return fetch(request)
                .then(networkResponse => {
                    // Clone response because response streams can be consumed only once
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                    return networkResponse;
                })
                .catch(err => {
                    // If both cache and network fail, just fail silently to avoid warnings
                    console.warn('Service Worker fetch failed for', request.url, err);
                    return new Response('', { status: 504, statusText: 'Gateway Timeout' });
                });
        })
    );
});
