const C='ssga-shell-v412';
self.addEventListener('install',event=>{self.skipWaiting();event.waitUntil(caches.open(C).then(cache=>cache.addAll(['/','/manifest.webmanifest','/favicon.svg','/icon.svg'])))});
self.addEventListener('activate',event=>event.waitUntil(Promise.all([self.clients.claim(),caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==C).map(key=>caches.delete(key))))])));
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET'||event.request.url.includes('/api/'))return;
 const navigation=event.request.mode==='navigate';
 event.respondWith(fetch(event.request).then(response=>{
  if(response.ok&&new URL(event.request.url).origin===location.origin){const copy=response.clone();caches.open(C).then(cache=>cache.put(event.request,copy))}
  return response;
 }).catch(async()=>{
  const cached=await caches.match(event.request);if(cached)return cached;
  if(navigation)return caches.match('/');
  return new Response('Resource unavailable',{status:503,statusText:'Offline'});
 }));
});
