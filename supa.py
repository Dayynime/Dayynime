"""Akses tabel `products` di Supabase lewat REST (PostgREST), hanya pakai stdlib.

Environment variable:
  SUPABASE_URL          contoh https://xxxx.supabase.co
  SUPABASE_SERVICE_KEY  service_role key (rahasia, hanya dipakai di server)
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
TABLE = "products"

# Kolom untuk halaman publik. Sengaja tidak memuat buyer_note (catatan internal admin).
PUBLIC_COLS = (
    "id,slug,title,category,description,price,discount_price,"
    "status,images,demo_url,created_at"
)
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


class StoreError(Exception):
    """Gagal bicara dengan Supabase."""

    def __init__(self, message, conflict=False):
        super().__init__(message)
        self.conflict = conflict


def configured():
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _request(method, params=None, body=None, prefer=None):
    if not configured():
        raise StoreError("SUPABASE_URL / SUPABASE_SERVICE_KEY belum diisi")
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            raw = res.read()
    except urllib.error.HTTPError as err:
        detail = err.read()[:300].decode("utf-8", "replace")
        raise StoreError(f"Supabase {err.code}: {detail}", conflict=(err.code == 409)) from err
    except (urllib.error.URLError, TimeoutError) as err:
        raise StoreError(f"Tidak bisa menghubungi Supabase: {err}") from err
    return json.loads(raw) if raw else None


def list_public():
    """Semua produk untuk publik: yang masih tersedia di atas, lalu yang terjual."""
    return _request(
        "GET",
        {"select": PUBLIC_COLS, "order": "status.asc,created_at.desc"},
    ) or []


def get_public(slug):
    rows = _request("GET", {"select": PUBLIC_COLS, "slug": f"eq.{slug}", "limit": "1"})
    return rows[0] if rows else None


def list_admin():
    return _request("GET", {"select": "*", "order": "created_at.desc"}) or []


def get_admin(product_id):
    if not UUID_RE.match(product_id or ""):
        return None
    rows = _request("GET", {"select": "*", "id": f"eq.{product_id}", "limit": "1"})
    return rows[0] if rows else None


def create(data):
    rows = _request("POST", body=data, prefer="return=representation")
    return rows[0] if rows else None


def update(product_id, data):
    if not UUID_RE.match(product_id or ""):
        raise StoreError("ID produk tidak valid")
    rows = _request(
        "PATCH", {"id": f"eq.{product_id}"}, body=data, prefer="return=representation"
    )
    return rows[0] if rows else None


def delete(product_id):
    if not UUID_RE.match(product_id or ""):
        raise StoreError("ID produk tidak valid")
    _request("DELETE", {"id": f"eq.{product_id}"})
