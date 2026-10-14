/* Homepage Google rating pill: the page ships with the last known rating and
 * review count baked in; this refreshes them from /api/google (the dfc-api
 * service, which caches the Google Places numbers). Fails silently. */
(function () {
  var pill = document.querySelector('[data-google-rating]');
  if (!pill || !window.fetch) return;
  fetch('/api/google', { headers: { Accept: 'application/json' } })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.rating || !d.count) return;
      var rating = Number(d.rating).toFixed(1);
      var rt = pill.querySelector('[data-gr-rating]'), ct = pill.querySelector('[data-gr-count]');
      if (rt) rt.textContent = rating;
      if (ct) ct.textContent = d.count;
      pill.setAttribute('aria-label', 'Rated ' + rating + ' out of 5 from ' + d.count + ' Google reviews');
    })
    .catch(function () {});
})();
