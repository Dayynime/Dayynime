// admin katalog: konfirmasi hapus + upload foto langsung ke Cloudinary
(() => {
  // konfirmasi sebelum menghapus produk
  document.addEventListener('submit', (e) => {
    const msg = e.target.dataset && e.target.dataset.confirm;
    if (msg && !confirm(msg)) e.preventDefault();
  });

  const root = document.getElementById('photos');
  if (!root) return;
  const list = document.getElementById('ph-list');
  const pick = document.getElementById('ph-pick');
  const note = document.getElementById('ph-status');
  const saveBtn = document.getElementById('save-btn');
  const form = document.getElementById('product-form');
  const MAX_BYTES = 10 * 1024 * 1024; // batas Cloudinary free per foto
  let uploading = false;

  const say = (text, bad = false) => {
    note.textContent = text;
    note.classList.toggle('bad', bad);
  };

  const refresh = () => {
    [...list.children].forEach((li, i) => {
      li.querySelector('.ph-cover').hidden = i !== 0;
      li.querySelector('.ph-first').hidden = i === 0;
    });
  };

  const thumb = (url) => url.replace('/image/upload/', '/image/upload/f_auto,q_auto,c_fill,g_auto,ar_1:1,w_240/');

  const addItem = (url) => {
    const li = document.createElement('li');
    li.className = 'ph';
    li.dataset.url = url;
    const img = document.createElement('img');
    img.src = thumb(url);
    img.alt = '';
    img.width = 120;
    img.height = 120;
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'images';
    input.value = url;
    const cover = document.createElement('span');
    cover.className = 'ph-cover';
    cover.textContent = 'Sampul';
    const btns = document.createElement('div');
    btns.className = 'ph-btns';
    const first = document.createElement('button');
    first.type = 'button';
    first.className = 'ph-first';
    first.textContent = 'Jadikan sampul';
    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'ph-del';
    del.textContent = 'Hapus';
    btns.append(first, del);
    li.append(img, input, cover, btns);
    list.append(li);
  };

  list.addEventListener('click', (e) => {
    const li = e.target.closest('.ph');
    if (!li) return;
    if (e.target.closest('.ph-del')) li.remove();
    else if (e.target.closest('.ph-first')) list.prepend(li);
    else return;
    refresh();
  });

  form.addEventListener('submit', (e) => {
    if (uploading) {
      e.preventDefault();
      say('Tunggu sampai upload foto selesai, baru simpan.', true);
    }
  });

  if (pick) {
    pick.addEventListener('change', async () => {
      const files = [...pick.files];
      pick.value = '';
      if (!files.length) return;
      uploading = true;
      saveBtn.disabled = true;
      say('Menyiapkan upload...');

      let sign;
      try {
        const res = await fetch(root.dataset.sign, {
          method: 'POST',
          headers: { 'X-CSRF-Token': root.dataset.csrf },
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || 'Gagal menyiapkan upload.');
        sign = json;
      } catch (err) {
        say(err.message, true);
        uploading = false;
        saveBtn.disabled = false;
        return;
      }

      let done = 0;
      let failed = 0;
      for (const file of files) {
        if (!file.type.startsWith('image/') || file.size > MAX_BYTES) {
          failed++;
          continue;
        }
        const fd = new FormData();
        fd.append('file', file);
        fd.append('api_key', sign.api_key);
        fd.append('timestamp', sign.timestamp);
        fd.append('folder', sign.folder);
        fd.append('signature', sign.signature);
        try {
          const res = await fetch(`https://api.cloudinary.com/v1_1/${sign.cloud_name}/image/upload`, {
            method: 'POST',
            body: fd,
          });
          const json = await res.json();
          if (!res.ok) throw new Error(json.error && json.error.message);
          addItem(json.secure_url);
          refresh();
        } catch (err) {
          failed++;
        }
        done++;
        say(`Mengunggah ${done} dari ${files.length}...`);
      }

      uploading = false;
      saveBtn.disabled = false;
      const ok = files.length - failed;
      say(
        failed
          ? `${ok} foto terunggah, ${failed} gagal (harus gambar, maksimal 10 MB). Klik Simpan untuk menyimpan.`
          : `${ok} foto terunggah. Klik Simpan untuk menyimpan.`,
        failed > 0,
      );
    });
  }

  refresh();
})();
