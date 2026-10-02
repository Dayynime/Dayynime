// detail produk: klik foto untuk melihatnya layar penuh, tetap bisa digeser ke samping
(() => {
  const lb = document.getElementById('lb');
  if (!lb || typeof lb.showModal !== 'function') return;
  const track = document.getElementById('lb-track');
  const count = document.getElementById('lb-count');
  const slides = [...track.children];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let loaded = false;
  let raf = 0;

  const current = () => Math.min(slides.length - 1, Math.max(0, Math.round(track.scrollLeft / track.clientWidth)));
  const label = () => { count.textContent = `${current() + 1} / ${slides.length}`; };
  const go = (i, smooth) => {
    const to = Math.min(slides.length - 1, Math.max(0, i)) * track.clientWidth;
    track.scrollTo({ left: to, behavior: smooth && !reduce ? 'smooth' : 'auto' });
  };

  // foto ukuran besar baru diunduh saat penampil pertama kali dibuka
  const load = () => {
    if (loaded) return;
    loaded = true;
    slides.forEach((s) => { const im = s.querySelector('img'); im.src = im.dataset.src; });
  };

  document.addEventListener('click', (e) => {
    const item = e.target.closest('.gal-item');
    if (!item) return;
    load();
    lb.showModal();
    go(Number(item.dataset.i), false);
    label();
    track.focus({ preventScroll: true });
  });

  track.addEventListener('scroll', () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(label);
  }, { passive: true });

  document.getElementById('lb-close').addEventListener('click', () => lb.close());
  const prev = document.getElementById('lb-prev');
  const next = document.getElementById('lb-next');
  if (prev) prev.addEventListener('click', () => go(current() - 1, true));
  if (next) next.addEventListener('click', () => go(current() + 1, true));

  // ketuk area gelap di luar foto untuk menutup
  lb.addEventListener('click', (e) => {
    if (e.target === lb || e.target === track || e.target.classList.contains('lb-slide')) lb.close();
  });

  lb.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(current() - 1, true); }
    if (e.key === 'ArrowRight') { e.preventDefault(); go(current() + 1, true); }
  });

  addEventListener('resize', () => { if (lb.open) go(current(), false); });
})();
