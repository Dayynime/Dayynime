// galeri foto di halaman detail produk: klik thumbnail untuk ganti foto utama
(() => {
  const main = document.getElementById('gal-main');
  const strip = document.getElementById('gal-strip');
  if (!main || !strip) return;
  strip.addEventListener('click', (e) => {
    const btn = e.target.closest('.pd-th');
    if (!btn) return;
    main.src = btn.dataset.full;
    strip.querySelectorAll('.pd-th').forEach((b) => b.removeAttribute('aria-current'));
    btn.setAttribute('aria-current', 'true');
  });
})();
