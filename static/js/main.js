(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // navbar: kasih latar setelah scroll
  const nav = $('#nav');
  const onScroll = () => nav.classList.toggle('scrolled', scrollY > 12);
  onScroll();
  addEventListener('scroll', onScroll, { passive: true });

  // menu mobile
  const burger = $('#burger'), menu = $('#menu');
  const setMenu = (open) => {
    burger.setAttribute('aria-expanded', open);
    burger.setAttribute('aria-label', open ? 'Tutup menu' : 'Buka menu');
    menu.classList.toggle('open', open);
  };
  burger.addEventListener('click', () => setMenu(burger.getAttribute('aria-expanded') !== 'true'));
  menu.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
  addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });


  // tombol WhatsApp melayang: muncul setelah hero, sembunyi saat bagian kontak atau footer terlihat
  const fab = $('#fab');
  if (fab) {
    const covering = new Set();
    const sync = () => fab.classList.toggle('show', scrollY > 520 && covering.size === 0);
    const watch = new IntersectionObserver((entries) => {
      entries.forEach((en) => en.isIntersecting ? covering.add(en.target) : covering.delete(en.target));
      sync();
    }, { threshold: 0.3 });
    ['#kontak', '.foot'].forEach((sel) => { const el = $(sel); if (el) watch.observe(el); });
    addEventListener('scroll', sync, { passive: true });
    sync();
  }

  // muncul saat di-scroll
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      en.target.classList.add(en.target.matches('.steps li') ? 'on' : 'in');
      io.unobserve(en.target);
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });
  $$('[data-reveal], .steps li').forEach((el) => io.observe(el));


  // form pemesanan: ringkasan ikut berubah saat pilihan diganti
  const order = $('#order');
  if (order) {
    const out = { kind: $('#sum-kind'), pkg: $('#sum-pkg'), price: $('#sum-price'), feat: $('#sum-feat') };
    const rupiah = (n) => 'Rp' + Number(n).toLocaleString('id-ID');
    const sync = () => {
      const j = order.querySelector('input[name="jenis"]:checked');
      if (!j) return;
      const p = order.querySelector(`input[name="paket_${j.value}"]:checked`);
      const feats = $$('input[name="fitur"]:checked', order).map((i) => i.value);
      out.kind.textContent = j.dataset.label;
      out.pkg.textContent = p ? p.dataset.name : '-';
      out.price.textContent = p && p.dataset.price ? rupiah(p.dataset.price) : 'Tanya dulu';
      out.feat.textContent = feats.length ? feats.join(', ') : 'Belum ada';
    };
    order.addEventListener('change', sync);
    sync();
  }

  if (reduce) return;

  // sorot mengikuti kursor
  $$('.spot').forEach((el) => {
    el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      el.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
  });

  // HP miring mengikuti kursor (hanya mouse)
  const stage = $('#stage'), phone = $('#phone');
  if (stage && matchMedia('(hover: hover)').matches) {
    stage.addEventListener('pointermove', (e) => {
      const r = stage.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      phone.style.transform = `rotateY(${x * 14}deg) rotateX(${-y * 10}deg)`;
    });
    stage.addEventListener('pointerleave', () => { phone.style.transform = ''; });
  }
})();
