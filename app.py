"""Website portofolio dan daftar harga jasa pembuatan website/aplikasi anime.

Semua isi (harga, fitur paket, karya) ada di bagian DATA di bawah ini.
Ubah di sini saja, template tidak perlu disentuh.
"""
import hashlib
import hmac
import os
import re
import secrets
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import quote

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import supa

# root_path eksplisit: templates/ dan static/ selalu dicari di samping app.py,
# apa pun folder kerja prosesnya (penting di Vercel).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, root_path=BASE_DIR)

# Admin katalog. Semua diatur lewat environment variable (jangan ditulis di kode):
#   ADMIN_PASSWORD, SECRET_KEY (opsional), SUPABASE_URL, SUPABASE_SERVICE_KEY,
#   CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
CLOUD_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
CLOUD_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")
CLOUD_FOLDER = "dayynime-katalog"

_secret = os.environ.get("SECRET_KEY")
if not _secret:
    # Turunan dari password admin supaya sesi tetap sama antar instance Vercel.
    _secret = (
        hashlib.sha256(f"dayynime-session:{ADMIN_PASSWORD}".encode()).hexdigest()
        if ADMIN_PASSWORD
        else secrets.token_hex(32)
    )
app.secret_key = _secret
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)

# ----------------------------------------------------------------------------
# DATA (edit bagian ini)
# ----------------------------------------------------------------------------

# Nomor WhatsApp format internasional tanpa + atau spasi, contoh: 6281234567890.
# Bisa juga diisi lewat environment variable WHATSAPP_NUMBER (di Vercel / Termux).
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "6285199329163")

SITE = {
    "name": "Dayynime",
    "tagline": "Jasa pembuatan website dan aplikasi anime, dikerjakan langsung oleh developer Zenime.",
    "download_url": "https://www.zenime.biz.id/download",
}

SERVICES = [
    {
        "kind": "web",
        "title": "Website streaming anime",
        "text": "Situs nonton lengkap dengan daftar anime, halaman detail, pencarian, "
        "dan pemutar video. Dibuat dengan Flask atau Next.js, lalu di-deploy ke Vercel.",
    },
    {
        "kind": "app",
        "title": "Aplikasi Android anime",
        "text": "Aplikasi native Jetpack Compose seperti Zenime: pemutar video, "
        "download offline, dan notifikasi.",
    },
    {
        "kind": "community",
        "tags": ["Akun pengguna", "Level dan XP", "Clan", "Chat global", "Premium"],
        "title": "Fitur komunitas dan premium",
        "text": "Akun pengguna, level dan XP, clan, chat global, serta sistem premium "
        "untuk monetisasi.",
    },
]

STACK = ["Flask", "Next.js", "Supabase", "Vercel", "Cloudinary", "Android (Compose)"]

DB_NOTE = (
    "Database berjalan di Supabase free plan. Kalau nanti kebutuhan melebihi "
    "batas free plan dan ingin upgrade, biaya langganannya ditanggung pembeli."
)

# Harga dipisah per jenis produk. price=None -> kartu menampilkan "Hubungi untuk harga"
# dan tombolnya jadi "Tanya harga". Isi angkanya di sini kalau sudah ditentukan.
CATEGORIES = [
    {
        "id": "web",
        "label": "Website",
        "intro": "Situs anime yang dibuka lewat browser di HP dan desktop.",
        "packages": [
            {
                "name": "Paket Non-Database",
                "price": 200_000,
                "desc": "Situs anime tanpa database sendiri. Data tayang diambil dari sumber eksternal.",
                "features": [
                    "Tampilan responsif untuk HP dan desktop",
                    "Daftar anime, halaman detail, dan halaman nonton",
                    "Pencarian dan filter genre",
                    "Backend Flask, siap deploy ke Vercel",
                    "Tanpa akun pengguna",
                ],
                "note": None,
                "tag": None,
                "hot": False,
            },
            {
                "name": "Paket Database",
                "price": 450_000,
                "desc": "Semua isi paket non-database, ditambah database Supabase untuk fitur akun.",
                "features": [
                    "Semua fitur Paket Non-Database",
                    "Database Supabase (free plan) sudah disetup",
                    "Login dan akun pengguna",
                    "Favorit dan riwayat tontonan",
                    "Komentar di tiap episode",
                ],
                "note": DB_NOTE,
                "tag": "Paling lengkap",
                "hot": True,
            },
        ],
    },
    {
        "id": "app",
        "label": "Aplikasi Android",
        "intro": "Aplikasi Android native dengan Jetpack Compose, seperti Zenime.",
        "packages": [
            {
                "name": "Paket Non-Database",
                "price": 300_000,
                "desc": "Aplikasi anime tanpa database sendiri. Data tayang diambil dari sumber eksternal.",
                "features": [
                    "Tampilan modern dengan Jetpack Compose",
                    "Daftar anime, halaman detail, dan pemutar video",
                    "Pencarian dan filter genre",
                    "Tanpa akun pengguna",
                ],
                "note": None,
                "tag": None,
                "hot": False,
            },
            {
                "name": "Paket Database",
                "price": 500_000,
                "desc": "Semua isi paket non-database, ditambah database Supabase untuk fitur akun.",
                "features": [
                    "Semua fitur Paket Non-Database",
                    "Database Supabase (free plan) sudah disetup",
                    "Login dan akun pengguna",
                    "Favorit dan riwayat tontonan",
                    "Komentar di tiap episode",
                ],
                "note": DB_NOTE,
                "tag": "Paling lengkap",
                "hot": True,
            },
        ],
    },
]

PROJECTS = [
    {
        "slug": "zenime",
        "name": "Zenime",
        "text": "Aplikasi streaming anime Android buatan sendiri, dibangun dan dikelola "
        "dari aplikasi sampai backend.",
        "features": [
            "Anime, donghua, dan komik dalam satu aplikasi",
            "Download dan nonton offline",
            "Chat Global dan Clan",
            "Level, XP, dan badge role",
            "Premium: kualitas hingga 1080p, bebas iklan, XP nonton x2",
        ],
        "cta": "Download Zenime",
        "url": SITE["download_url"],
    },
]

STEPS = [
    ("Konsultasi lewat WhatsApp", "Ceritakan kebutuhan dan paket yang dipilih."),
    ("Kesepakatan", "Fitur dan harga disepakati sebelum pengerjaan dimulai."),
    ("Pengerjaan", "Website atau aplikasi dibuat, progres dikabari berkala."),
    ("Serah terima", "Hasil di-deploy dan siap dipakai."),
]

# Langkah beli dan pindah kepemilikan produk katalog (tampil di halaman detail produk).
TRANSFER_STEPS = [
    ("Chat dan sepakati", "Hubungi lewat WhatsApp, tanyakan yang belum jelas, lalu sepakati harga."),
    ("Pembayaran", "Bayar sesuai harga yang disepakati dan kirim bukti pembayaran."),
    ("Pindah kepemilikan", "Source code, akses hosting, dan database (jika ada) dipindahkan ke akunmu."),
    ("Ditandai terjual", "Setelah serah terima selesai, produk ditandai terjual dan tidak dijual lagi."),
]

HERO_POINTS = [
    "Harga jelas sejak awal",
    "Dikerjakan langsung oleh developer",
    "Siap deploy ke Vercel",
]

# Chip kecil yang melayang di sekitar screenshot Zenime (hero)
HERO_CHIPS = ["Nonton offline", "Kualitas hingga 1080p", "Clan dan chat global"]

# Keterangan yang tampil di bawah daftar harga
PRICING_NOTES = [
    (
        "Sumber anime dari pihak ketiga",
        "Semua sumber anime pada website dan aplikasi berasal dari pihak ketiga. "
        "Sumber tidak disediakan oleh pihak Zenime karena keterbatasan server.",
    ),
    (
        "Request fitur tambahan",
        "Harga fitur di luar paket tergantung tingkat kesulitannya. "
        "Disepakati lewat WhatsApp sebelum pengerjaan.",
    ),
]

FAQ = [
    (
        "Apa bedanya Paket Non-Database dan Paket Database?",
        "Paket Non-Database mengambil data tayang dari sumber eksternal dan tidak punya akun "
        "pengguna. Paket Database menambah Supabase untuk login, favorit, riwayat tontonan, "
        "dan komentar.",
    ),
    (
        "Siapa yang menanggung biaya kalau database melebihi free plan?",
        "Database berjalan di Supabase free plan. Kalau kebutuhan melebihi batas dan kamu "
        "ingin upgrade, biaya langganannya ditanggung pembeli.",
    ),
    (
        "Hasilnya di-deploy di mana?",
        "Website dibuat dengan Flask atau Next.js dan di-deploy ke Vercel. Saat serah terima, "
        "hasilnya sudah online dan siap dipakai.",
    ),
    (
        "Bisa minta fitur di luar paket?",
        "Bisa. Level dan XP, clan, chat global, dan sistem premium termasuk yang bisa "
        "dikerjakan. Harganya tergantung tingkat kesulitan fitur, dan disepakati lewat "
        "WhatsApp sebelum pengerjaan dimulai.",
    ),
    (
        "Dari mana sumber anime-nya?",
        "Semua sumber anime pada website dan aplikasi berasal dari pihak ketiga. "
        "Sumber tidak disediakan oleh pihak Zenime karena keterbatasan server, sehingga "
        "ketersediaan dan kualitas tayangan mengikuti sumber tersebut.",
    ),
]

# ----------------------------------------------------------------------------
# DATA HALAMAN LAIN
# ----------------------------------------------------------------------------

# Baris tabel perbandingan di halaman Harga: (fitur, (Non-Database, Database))
_DB_ROWS = [
    ("Database Supabase (free plan) sudah disetup", (False, True)),
    ("Login dan akun pengguna", (False, True)),
    ("Favorit dan riwayat tontonan", (False, True)),
    ("Komentar di tiap episode", (False, True)),
]
COMPARE = {
    "web": [
        ("Tampilan responsif untuk HP dan desktop", (True, True)),
        ("Daftar anime, halaman detail, dan halaman nonton", (True, True)),
        ("Pencarian dan filter genre", (True, True)),
        ("Backend Flask, siap deploy ke Vercel", (True, True)),
    ] + _DB_ROWS,
    "app": [
        ("Tampilan modern dengan Jetpack Compose", (True, True)),
        ("Daftar anime, halaman detail, dan pemutar video", (True, True)),
        ("Pencarian dan filter genre", (True, True)),
    ] + _DB_ROWS,
}

# Penjelasan lengkap tiap layanan (halaman /layanan). Kuncinya sama dengan "kind" di SERVICES.
SERVICE_DETAILS = {
    "web": {
        "who": "Cocok kalau kamu ingin situs nonton anime yang bisa dibuka dari browser di HP maupun desktop.",
        "includes": [
            "Daftar anime dan halaman detail",
            "Halaman nonton dengan pemutar video",
            "Pencarian dan filter genre",
            "Tampilan responsif untuk HP dan desktop",
            "Backend Flask atau Next.js, di-deploy ke Vercel",
            "Opsional: akun, favorit, riwayat, dan komentar lewat Supabase",
        ],
        "tech": ["Flask", "Next.js", "Vercel", "Supabase"],
        "jenis": "web",
    },
    "app": {
        "who": "Cocok kalau kamu ingin aplikasi anime sendiri di Android, bukan sekadar situs di browser.",
        "includes": [
            "Aplikasi native dengan Jetpack Compose",
            "Daftar anime, halaman detail, dan pemutar video",
            "Pencarian dan filter genre",
            "Download dan nonton offline",
            "Notifikasi",
            "Opsional: akun, favorit, riwayat, dan komentar lewat Supabase",
        ],
        "tech": ["Android (Compose)", "Supabase"],
        "jenis": "app",
    },
    "community": {
        "who": "Cocok kalau kamu ingin pengguna betah lebih lama dan butuh jalur monetisasi.",
        "includes": [
            "Akun pengguna",
            "Level dan XP",
            "Clan",
            "Chat global",
            "Sistem premium untuk monetisasi",
        ],
        "example": "Contoh di Zenime: premium memberi kualitas hingga 1080p, bebas iklan, dan XP nonton x2.",
        "tech": ["Supabase"],
        "jenis": None,
    },
}

# Pilihan fitur tambahan di form pemesanan (/pesan)
FEATURE_OPTIONS = [
    "Level dan XP",
    "Clan",
    "Chat global",
    "Sistem premium",
    "Download dan nonton offline",
    "Notifikasi",
]
COMMUNITY_FEATURES = ["Level dan XP", "Clan", "Chat global", "Sistem premium"]

# Halaman detail karya (/karya/<slug>)
PROJECT_DETAILS = {
    "zenime": {
        "tagline": "Aplikasi streaming anime Android, dibangun dan dikelola sendiri dari aplikasi sampai backend.",
        "about": [
            "Zenime menggabungkan anime, donghua, dan komik dalam satu aplikasi. "
            "Penonton bisa mengunduh episode untuk ditonton offline, ngobrol di chat global, "
            "dan bergabung ke clan.",
            "Ada sistem level, XP, dan badge role. Akun premium mendapat kualitas hingga 1080p, "
            "bebas iklan, dan XP nonton x2.",
        ],
        "tech": ["Android (Jetpack Compose)", "Supabase"],
        "screenshots": [
            {
                "file": "img/zenime-profile.jpg",
                "alt": "Beranda aplikasi Zenime dengan akun premium, ZCoin, dan banner anime",
                "caption": "Beranda Zenime dengan akun premium, ZCoin, dan banner anime",
            },
        ],
    },
}

# Testimoni pelanggan. Isi kalau sudah ada yang mau dikutip, contoh:
#   {"nama": "Nama pelanggan", "produk": "Website streaming anime", "teks": "Isi testimoni."}
TESTIMONIALS = []
# Bukti transaksi: taruh gambar (yang sudah disamarkan nama dan nomornya) di static/img/bukti/
# dan halaman Testimoni otomatis menampilkannya.

# Halaman Tentang
ABOUT = {
    "intro": [
        "Dayynime adalah layanan pembuatan website dan aplikasi anime dari developer Zenime. "
        "Zenime sendiri adalah aplikasi streaming anime Android yang dibangun dan dikelola dari "
        "aplikasi sampai backend. Pesananmu dikerjakan oleh orang yang sama.",
        "Tidak ada perantara. Kamu bicara langsung lewat WhatsApp dengan orang yang mengerjakannya, "
        "dari konsultasi sampai serah terima.",
    ],
    "principles": [
        ("Harga jelas sejak awal", "Daftar harga dipajang terbuka. Fitur di luar paket disepakati sebelum pengerjaan."),
        ("Dikerjakan langsung", "Satu developer dari obrolan pertama sampai hasil jadi."),
        ("Progres dikabari berkala", "Kamu tahu sudah sampai mana, tanpa perlu menagih."),
        ("Terbuka soal sumber anime", "Sumber tayang berasal dari pihak ketiga dan tidak disediakan oleh pihak Zenime."),
    ],
}

# Halaman Syarat dan ketentuan: (judul, [paragraf])
TERMS_UPDATED = "3 Oktober 2026"
TERMS = [
    (
        "Lingkup pekerjaan",
        [
            "Yang dikerjakan adalah fitur yang tertulis di paket dan yang disepakati lewat WhatsApp sebelum pengerjaan dimulai.",
            "Fitur di luar itu dihitung sebagai fitur tambahan. Harganya tergantung tingkat kesulitan dan disepakati sebelum dikerjakan.",
        ],
    ),
    (
        "Pembayaran",
        [
            "Harga mengikuti daftar harga atau kesepakatan di WhatsApp. Metode dan tahapan pembayaran disepakati sebelum pengerjaan dimulai.",
            "Metode pembayaran yang tersedia, misalnya DANA dan QRIS, dikonfirmasi lewat chat WhatsApp. Pastikan nama penerima sesuai sebelum membayar.",
        ],
    ),
    (
        "Revisi",
        [
            "Perbaikan kecil pada fitur yang sudah disepakati, seperti teks, warna, atau bug, dikerjakan selama masa pengerjaan.",
            "Perubahan yang menambah atau mengganti fitur dihitung sebagai fitur tambahan.",
        ],
    ),
    (
        "Database dan biaya langganan",
        [
            "Paket Database memakai Supabase free plan yang sudah disetup.",
            "Kalau kebutuhan melebihi batas free plan dan kamu ingin upgrade, biaya langganannya ditanggung pembeli.",
        ],
    ),
    (
        "Sumber anime dari pihak ketiga",
        [
            "Semua sumber anime pada website dan aplikasi berasal dari pihak ketiga. Sumber tidak disediakan oleh pihak Zenime karena keterbatasan server.",
            "Ketersediaan dan kualitas tayangan mengikuti sumber tersebut.",
        ],
    ),
    (
        "Serah terima",
        [
            "Website di-deploy ke Vercel dan diserahkan dalam keadaan online dan siap dipakai. Progres dikabari berkala selama pengerjaan.",
        ],
    ),
]

# ----------------------------------------------------------------------------
# LOGIKA
# ----------------------------------------------------------------------------

NAV = [
    ("layanan", "Layanan"),
    ("harga", "Harga"),
    ("katalog", "Produk Jadi"),
    ("karya", "Karya"),
    ("alur_faq", "Alur & FAQ"),
    ("tentang", "Tentang"),
]


@app.template_filter("rupiah")
def rupiah(value):
    """200000 -> 'Rp200.000'"""
    return "Rp" + f"{int(value):,}".replace(",", ".")


def wa_link(message):
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(message)}"


def bukti_files():
    """Nama file gambar di static/img/bukti/ (kosong kalau folder belum ada)."""
    folder = os.path.join(app.static_folder, "img", "bukti")
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    return sorted(n for n in names if n.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))


def categories_view():
    """CATEGORIES + tabel perbandingan, tautan tombol, dan harga mulai dari."""
    out = []
    for c in CATEGORIES:
        packages = []
        for i, p in enumerate(c["packages"]):
            if p["price"]:
                href = url_for("pesan", jenis=c["id"], paket=i)
            else:
                href = wa_link(f"Halo Dayynime, saya mau tanya harga {p['name']} untuk {c['label']}.")
            packages.append({**p, "href": href})
        prices = [p["price"] for p in c["packages"] if p["price"]]
        out.append(
            {
                **c,
                "packages": packages,
                "compare": COMPARE.get(c["id"], []),
                "min_price": min(prices) if prices else None,
            }
        )
    return out


@app.context_processor
def inject_globals():
    endpoint = request.endpoint or ""
    nav = list(NAV)
    show_testimoni = bool(TESTIMONIALS or bukti_files())
    if show_testimoni:
        nav.append(("testimoni", "Testimoni"))
    return {
        "site": SITE,
        "nav_items": nav,
        "current": {"karya_detail": "karya", "katalog_detail": "katalog"}.get(endpoint, endpoint),
        "csrf_token": csrf_token,
        "show_testimoni": show_testimoni,
        "wa_general": wa_link("Halo Dayynime, saya tertarik dengan jasa pembuatan website/aplikasi anime. Boleh tanya-tanya dulu?"),
        "year": datetime.now().year,
    }


@app.route("/")
def index():
    categories = categories_view()
    prices = [c["min_price"] for c in categories if c["min_price"]]
    kat_items, kat_total = home_catalog()
    page = render_template(
        "index.html",
        kat_items=kat_items,
        kat_total=kat_total,
        services=SERVICES,
        stack=STACK,
        categories=categories,
        min_price=min(prices) if prices else None,
        projects=PROJECTS,
        hero_points=HERO_POINTS,
        hero_chips=HERO_CHIPS,
    )
    return cached(make_response(page), ok=bool(kat_items) or not supa.configured())


def home_catalog(limit=5):
    """Maksimal `limit` produk tersedia untuk daftar di beranda. Gagal diam-diam: beranda tetap tampil."""
    if not supa.configured():
        return [], 0
    try:
        rows = [decorate(r) for r in supa.list_public(timeout=3)]
    except supa.StoreError:
        return [], 0
    ready = [p for p in rows if not p["sold"]]
    return ready[:limit], len(ready)


@app.route("/layanan")
def layanan():
    services = [{**s, **SERVICE_DETAILS.get(s["kind"], {})} for s in SERVICES]
    return render_template(
        "layanan.html",
        services=services,
        community_features=COMMUNITY_FEATURES,
    )


@app.route("/harga")
def harga():
    categories = categories_view()
    active = request.args.get("jenis")
    if active not in [c["id"] for c in categories]:
        active = categories[0]["id"]
    return render_template(
        "harga.html",
        categories=categories,
        active=active,
        pricing_notes=PRICING_NOTES,
    )


@app.route("/karya")
def karya():
    return render_template("karya.html", projects=PROJECTS)


@app.route("/karya/<slug>")
def karya_detail(slug):
    project = next((p for p in PROJECTS if p.get("slug") == slug), None)
    if project is None:
        abort(404)
    return render_template(
        "karya_detail.html",
        project={**project, **PROJECT_DETAILS.get(slug, {})},
    )


@app.route("/pesan")
def pesan():
    categories = categories_view()
    by_id = {c["id"]: c for c in categories}
    jenis = request.args.get("jenis")
    if jenis not in by_id:
        jenis = categories[0]["id"]

    # paket yang tercentang: paket "hot" di tiap jenis, kecuali diminta lain lewat ?paket=
    selected = {
        c["id"]: next((i for i, p in enumerate(c["packages"]) if p["hot"]), 0)
        for c in categories
    }
    try:
        idx = int(request.args.get("paket", ""))
        if 0 <= idx < len(by_id[jenis]["packages"]):
            selected[jenis] = idx
    except ValueError:
        pass

    checked = [f for f in request.args.getlist("fitur") if f in FEATURE_OPTIONS]
    return render_template(
        "pesan.html",
        categories=categories,
        jenis=jenis,
        selected=selected,
        features=FEATURE_OPTIONS,
        checked=checked,
    )


@app.route("/pesan/kirim")
def pesan_kirim():
    """Susun pesan dari form lalu arahkan ke WhatsApp."""
    by_id = {c["id"]: c for c in CATEGORIES}
    cat = by_id.get(request.args.get("jenis"))
    if cat is None:
        return redirect(url_for("pesan"))

    try:
        idx = int(request.args.get(f"paket_{cat['id']}", ""))
        pkg = cat["packages"][idx] if 0 <= idx < len(cat["packages"]) else cat["packages"][0]
    except ValueError:
        pkg = cat["packages"][0]

    harga_teks = rupiah(pkg["price"]) if pkg["price"] else "harga mau ditanyakan dulu"
    fitur = [f for f in request.args.getlist("fitur") if f in FEATURE_OPTIONS]
    nama = request.args.get("nama", "").strip()[:60]
    catatan = request.args.get("catatan", "").strip()[:600]

    lines = [
        "Halo Dayynime, saya mau pesan:",
        f"- Jenis: {cat['label']}",
        f"- Paket: {pkg['name']} ({harga_teks})",
        f"- Fitur tambahan: {', '.join(fitur) if fitur else 'belum ada'}",
    ]
    if nama:
        lines.append(f"- Nama: {nama}")
    if catatan:
        lines.append(f"- Catatan: {catatan}")
    lines.append("Bisa dijelaskan prosesnya?")

    response = redirect(wa_link("\n".join(lines)))
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/syarat")
def syarat():
    return render_template("syarat.html", terms=TERMS, updated=TERMS_UPDATED)


@app.route("/alur-faq")
def alur_faq():
    return render_template("alur_faq.html", steps=STEPS, faq=FAQ)


@app.route("/tentang")
def tentang():
    return render_template("tentang.html", about=ABOUT, projects=PROJECTS, stack=STACK)


@app.route("/testimoni")
def testimoni():
    return render_template(
        "testimoni.html",
        testimonials=TESTIMONIALS,
        bukti=bukti_files(),
    )


# ----------------------------------------------------------------------------
# KATALOG (publik)
# ----------------------------------------------------------------------------

CDN_SIZES = {
    "card": "f_auto,q_auto,c_fill,g_auto,ar_16:10,w_640",
    "gal": "f_auto,q_auto,c_limit,w_900,h_900",
    "zoom": "f_auto,q_auto,c_limit,w_1800,h_1800",
    "admin": "f_auto,q_auto,c_fill,g_auto,ar_1:1,w_240",
}


@app.template_filter("cdn")
def cdn(url, size="card"):
    """Sisipkan transformasi Cloudinary (ukuran, format, kualitas otomatis)."""
    marker = "/image/upload/"
    if not url or marker not in url:
        return url
    return url.replace(marker, f"{marker}{CDN_SIZES[size]}/", 1)


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:60].strip("-") or "produk"


def decorate(row):
    """Tambah harga akhir, persen diskon, dan flag terjual ke satu baris produk."""
    p = dict(row)
    price = int(p["price"])
    disc = p.get("discount_price")
    disc = int(disc) if disc else None
    if disc and 0 < disc < price:
        p["final_price"] = disc
        p["percent"] = max(1, round((1 - disc / price) * 100))
    else:
        p["final_price"] = price
        p["percent"] = 0
    stock = p.get("stock")
    if stock is None:  # kolom stock belum ada: produk tunggal
        stock = 0 if p.get("status") == "sold" else 1
    p["stock"] = max(0, int(stock))
    p["db"] = "database" if p.get("db_type") == "database" else "none"
    p["sold"] = p.get("status") == "sold" or p["stock"] <= 0
    p["images"] = p.get("images") or []
    return p


def cached(response, ok=True):
    # Cache singkat di edge Vercel; status terjual ikut berubah paling lama sekitar semenit.
    response.headers["Cache-Control"] = (
        "public, max-age=0, s-maxage=30, stale-while-revalidate=60" if ok else "no-store"
    )
    return response


@app.route("/katalog")
def katalog():
    jenis = request.args.get("jenis")
    if jenis not in ("website", "aplikasi"):
        jenis = None
    db = request.args.get("db")
    if db not in ("database", "none"):
        db = None
    items, failed = [], False
    if supa.configured():
        try:
            items = [decorate(r) for r in supa.list_public()]
        except supa.StoreError:
            failed = True
    counts = {
        "all": len(items),
        "website": sum(1 for p in items if p["category"] == "website"),
        "aplikasi": sum(1 for p in items if p["category"] == "aplikasi"),
        "database": sum(1 for p in items if p["db"] == "database"),
        "none": sum(1 for p in items if p["db"] == "none"),
    }
    if jenis:
        items = [p for p in items if p["category"] == jenis]
    if db:
        items = [p for p in items if p["db"] == db]
    page = render_template(
        "katalog.html", items=items, jenis=jenis, db=db, failed=failed,
        counts=counts, steps=TRANSFER_STEPS,
    )
    return cached(make_response(page), ok=not failed)


@app.route("/katalog/<slug>")
def katalog_detail(slug):
    row = None
    if supa.configured():
        try:
            row = supa.get_public(slug)
        except supa.StoreError:
            return cached(make_response(render_template("katalog_error.html"), 503), ok=False)
    if row is None:
        abort(404)
    p = decorate(row)
    buy_link = wa_link(
        f"Halo Dayynime, saya mau beli {p['title']} ({rupiah(p['final_price'])}) "
        f"dari halaman Produk Jadi. Masih tersedia?\n{request.url}"
    )
    page = render_template(
        "katalog_detail.html", p=p, buy_link=buy_link, steps=TRANSFER_STEPS
    )
    return cached(make_response(page))


# ----------------------------------------------------------------------------
# ADMIN KATALOG
# ----------------------------------------------------------------------------

def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


@app.before_request
def check_admin_csrf():
    if request.method == "POST" and (request.endpoint or "").startswith("admin_"):
        expected = session.get("csrf", "")
        sent = request.form.get("csrf") or request.headers.get("X-CSRF-Token", "")
        if not expected or not hmac.compare_digest(sent, expected):
            abort(400)


@app.after_request
def admin_headers(response):
    if request.path.startswith("/admin"):
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        response.headers["Cache-Control"] = "no-store"
    return response


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            if request.endpoint == "admin_sign":
                return jsonify(error="Sesi habis, login ulang dulu."), 401
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def parse_int(raw):
    digits = re.sub(r"\D", "", raw or "")
    return int(digits) if digits else None


def valid_image_url(url):
    cloud = re.escape(CLOUD_NAME) if CLOUD_NAME else r"[A-Za-z0-9_-]+"
    return bool(
        re.fullmatch(rf"https://res\.cloudinary\.com/{cloud}/image/upload/[\w./,:%~-]+", url)
    )


def parse_product(form, existing=None):
    """Baca dan validasi form produk. Mengembalikan (data, errors, values)."""
    errors = []
    title = form.get("title", "").strip()[:120]
    category = form.get("category", "")
    description = form.get("description", "").strip()[:4000]
    price_raw = form.get("price", "")
    disc_raw = form.get("discount_price", "")
    status = form.get("status", "available")
    db_type = form.get("db_type", "none")
    stock_raw = form.get("stock", "")
    stock = parse_int(stock_raw)
    demo_url = form.get("demo_url", "").strip()[:300]
    buyer_note = form.get("buyer_note", "").strip()[:600]
    images = []
    for url in form.getlist("images"):
        url = url.strip()
        if url and url not in images and valid_image_url(url):
            images.append(url)
    images = images[:100]

    price = parse_int(price_raw)
    discount = parse_int(disc_raw)

    if not title:
        errors.append("Judul wajib diisi.")
    if category not in ("website", "aplikasi"):
        errors.append("Pilih jenis produk.")
    if price is None or price < 1:
        errors.append("Harga wajib diisi.")
    if discount is not None:
        if discount < 1:
            discount = None
        elif price is not None and discount >= price:
            errors.append("Harga diskon harus lebih kecil dari harga normal.")
    if status not in ("available", "sold"):
        status = "available"
    if db_type not in ("none", "database"):
        db_type = "none"
    if stock is None:
        stock = 0 if status == "sold" else 1
    stock = min(stock, 9999)
    if status == "sold":
        stock = 0  # terjual = stok habis
    elif stock < 1:
        errors.append("Stok 0 berarti habis. Isi stok minimal 1, atau ubah status ke Terjual.")
    if demo_url and not re.match(r"^https?://", demo_url):
        errors.append("Link demo harus diawali http:// atau https://.")

    data = {
        "title": title,
        "category": category,
        "description": description,
        "price": price,
        "discount_price": discount,
        "status": status,
        "stock": stock,
        "db_type": db_type,
        "demo_url": demo_url or None,
        "buyer_note": buyer_note or None,
        "images": images,
    }
    was_sold = bool(existing and existing.get("status") == "sold")
    if status == "sold" and not was_sold:
        data["sold_at"] = datetime.now(timezone.utc).isoformat()
    elif status == "available":
        data["sold_at"] = None

    values = {
        "title": title,
        "category": category,
        "description": description,
        "price": price_raw,
        "discount_price": disc_raw,
        "status": status,
        "stock": stock_raw if stock_raw.strip() else stock,
        "db_type": db_type,
        "demo_url": demo_url,
        "buyer_note": buyer_note,
        "images": images,
    }
    return data, errors, values


def _safe_next(target):
    return target if target and target.startswith("/admin") and not target.startswith("//") else None


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_index"))
    error = None
    if request.method == "POST":
        sent = request.form.get("password", "")
        if not ADMIN_PASSWORD:
            error = "ADMIN_PASSWORD belum diatur di environment variable."
        elif hmac.compare_digest(sent.encode(), ADMIN_PASSWORD.encode()):
            session.clear()
            session["admin"] = True
            session.permanent = True
            return redirect(_safe_next(request.args.get("next")) or url_for("admin_index"))
        else:
            time.sleep(1)  # perlambat tebak-tebakan password
            error = "Password salah."
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_index():
    items, error = [], None
    if not supa.configured():
        error = "SUPABASE_URL dan SUPABASE_SERVICE_KEY belum diatur."
    else:
        try:
            items = [decorate(r) for r in supa.list_admin()]
        except supa.StoreError as err:
            error = str(err)
    return render_template("admin_list.html", items=items, error=error)


def _form_page(product, values, errors):
    return render_template(
        "admin_form.html",
        product=product,
        values=values,
        errors=errors,
        cloud_ready=bool(CLOUD_NAME and CLOUD_KEY and CLOUD_SECRET),
    )


EMPTY_VALUES = {
    "title": "", "category": "aplikasi", "description": "", "price": "",
    "discount_price": "", "status": "available", "stock": 1, "db_type": "none",
    "demo_url": "", "buyer_note": "", "images": [],
}


@app.route("/admin/produk/baru", methods=["GET", "POST"])
@admin_required
def admin_new():
    if request.method == "GET":
        return _form_page(None, EMPTY_VALUES, [])
    data, errors, values = parse_product(request.form)
    if errors:
        return _form_page(None, values, errors), 400
    slug = slugify(data["title"])
    try:
        try:
            supa.create({**data, "slug": slug})
        except supa.StoreError as err:
            if not err.conflict:
                raise
            supa.create({**data, "slug": f"{slug}-{secrets.token_hex(2)}"})
    except supa.StoreError as err:
        return _form_page(None, values, [f"Gagal menyimpan: {err}"]), 502
    flash("Produk ditambahkan.")
    return redirect(url_for("admin_index"))


@app.route("/admin/produk/<pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit(pid):
    try:
        product = supa.get_admin(pid)
    except supa.StoreError:
        abort(502)
    if product is None:
        abort(404)
    if request.method == "GET":
        values = {
            **EMPTY_VALUES,
            "title": product["title"],
            "category": product["category"],
            "description": product.get("description") or "",
            "price": product["price"],
            "discount_price": product.get("discount_price") or "",
            "status": product["status"],
            "stock": product["stock"] if product.get("stock") is not None else (0 if product["status"] == "sold" else 1),
            "db_type": product.get("db_type") or "none",
            "demo_url": product.get("demo_url") or "",
            "buyer_note": product.get("buyer_note") or "",
            "images": product.get("images") or [],
        }
        return _form_page(product, values, [])
    data, errors, values = parse_product(request.form, existing=product)
    if errors:
        return _form_page(product, values, errors), 400
    try:
        supa.update(pid, data)
    except supa.StoreError as err:
        return _form_page(product, values, [f"Gagal menyimpan: {err}"]), 502
    flash("Perubahan disimpan.")
    return redirect(url_for("admin_index"))


@app.route("/admin/produk/<pid>/status", methods=["POST"])
@admin_required
def admin_status(pid):
    status = request.form.get("status")
    if status not in ("available", "sold"):
        abort(400)
    try:
        product = supa.get_admin(pid)
        if product is None:
            abort(404)
        stock = product.get("stock")
        if stock is None:
            stock = 0 if product.get("status") == "sold" else 1
        if status == "sold" and product.get("status") != "sold" and stock > 1:
            # stok lebih dari 1: catat satu terjual, produk tetap tersedia
            supa.update(pid, {"stock": stock - 1})
            flash(f"Terjual 1. Sisa stok {stock - 1}.")
        elif status == "sold":
            supa.update(pid, {
                "status": "sold", "stock": 0,
                "sold_at": datetime.now(timezone.utc).isoformat(),
            })
            flash("Ditandai terjual.")
        else:
            supa.update(pid, {"status": "available", "stock": max(stock, 1), "sold_at": None})
            flash("Ditandai tersedia lagi.")
    except supa.StoreError as err:
        flash(f"Gagal mengubah status: {err}")
    return redirect(url_for("admin_index"))


@app.route("/admin/produk/<pid>/hapus", methods=["POST"])
@admin_required
def admin_delete(pid):
    try:
        supa.delete(pid)
        flash("Produk dihapus.")
    except supa.StoreError as err:
        flash(f"Gagal menghapus: {err}")
    return redirect(url_for("admin_index"))


@app.route("/admin/cloudinary-sign", methods=["POST"])
@admin_required
def admin_sign():
    """Tanda tangan upload Cloudinary. Browser mengunggah foto langsung ke Cloudinary,
    jadi tidak kena batas ukuran request Vercel, dan API secret tidak pernah keluar dari server."""
    if not (CLOUD_NAME and CLOUD_KEY and CLOUD_SECRET):
        return jsonify(error="Cloudinary belum dikonfigurasi di environment variable."), 503
    params = {"folder": CLOUD_FOLDER, "timestamp": int(time.time())}
    to_sign = "&".join(f"{k}={params[k]}" for k in sorted(params))
    signature = hashlib.sha1((to_sign + CLOUD_SECRET).encode()).hexdigest()
    return jsonify(
        cloud_name=CLOUD_NAME,
        api_key=CLOUD_KEY,
        timestamp=params["timestamp"],
        folder=params["folder"],
        signature=signature,
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
