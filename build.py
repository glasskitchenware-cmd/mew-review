#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the static affiliate review page from products.csv.
Never invents prices. Does not call paid APIs or AI.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "products.csv"
OUT_PATH = ROOT / "index.html"
STATUS_PATH = ROOT / "refresh-status.json"
TZ = ZoneInfo("Asia/Bangkok")


def load_products():
    rows = []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            link = (r.get("affiliate_link") or "").strip()
            if not link.startswith("https://s.shopee.co.th/"):
                continue
            pub = (r.get("publish") or "YES").strip().upper()
            if pub not in ("YES", "Y", "TRUE", "1", ""):
                continue
            rows.append(r)
    return rows


def load_status():
    if not STATUS_PATH.exists():
        return {}
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def checked_range(rows):
    dates = sorted({(r.get("checked_at") or "").strip() for r in rows if (r.get("checked_at") or "").strip()})
    if not dates:
        return "", ""
    return dates[0], dates[-1]


def render(rows, now, status):
    dmin, dmax = checked_range(rows)
    if dmin and dmax and dmin != dmax:
        date_label = f"ข้อมูลราคา ณ วันที่ {escape(dmin)} ถึง {escape(dmax)} เวลาไทย (Asia/Bangkok)"
    elif dmax:
        date_label = f"ข้อมูลราคา ณ วันที่ {escape(dmax)} เวลาไทย (Asia/Bangkok)"
    else:
        date_label = "ยังไม่มีวันที่ตรวจราคาในไฟล์สินค้า"
    live = bool(status.get("live_prices"))
    if live:
        refresh_note = escape(status.get("summary") or "อัปเดตราคาจากแหล่งสาธารณะแล้ว")
    else:
        reason = status.get("reason") or "ยังดึงราคาสดจาก Shopee แบบฟรีไม่ได้ในรอบนี้ จึงแสดงราคาตามวันที่ตรวจในแต่ละสินค้า ไม่ได้เดาราคาใหม่"
        refresh_note = escape(reason)

    cats = sorted({(r.get("category") or "อื่น").strip() or "อื่น" for r in rows})
    options = "\n".join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in cats)
    cards = []
    for r in rows:
        name = escape((r.get("short_name") or r.get("name") or "สินค้า").strip())
        full = escape((r.get("name") or "").strip())
        cat = escape((r.get("category") or "อื่น").strip() or "อื่น")
        price = escape((r.get("price_as_shown") or "ดูราคาที่ Shopee").strip())
        sold = escape((r.get("sold") or "").strip())
        rating = escape((r.get("rating") or "").strip())
        checked = escape((r.get("checked_at") or "").strip())
        link = escape((r.get("affiliate_link") or "").strip())
        badge = '<span class="badge">มีคลิปรีวิวในช่อง</span>' if (r.get("has_review_clip") or "").strip() == "ใช่" else ""
        meta = " · ".join(
            x
            for x in [
                f"ขายแล้ว {sold}" if sold else "",
                f"เรตติ้ง {rating}" if rating else "",
                f"ข้อมูล ณ วันที่ {checked}" if checked else "ยังไม่มีวันที่ตรวจราคา",
            ]
            if x
        )
        cards.append(
            f'<article class="card" data-cat="{cat}" data-name="{name} {full}">'
            f"<h3>{name}</h3><p class='full'>{full}</p>"
            f"<div class='row'><span class='cat'>{cat}</span>{badge}</div>"
            f"<p class='price'>{price}</p><p class='meta'>{meta}</p>"
            f'<a class="btn" href="{link}" rel="nofollow sponsored noopener" target="_blank">ดูราคาล่าสุดบน Shopee</a>'
            f"</article>"
        )

    stamp = now.strftime("%Y-%m-%d %H:%M") + " เวลาไทย (Asia/Bangkok)"
    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>รีวิวของใช้ดีราคาเบา โดยน้องมิว Mew Story</title>
<meta name="description" content="รวมสินค้าที่น้องมิวรีวิว ลิงก์เป็นลิงก์แอฟฟิลิเอตของ Shopee ราคาตามวันที่ตรวจในแต่ละสินค้า">
<style>
:root {{ --pink:#c2185b; --lilac:#6a1b9a; --bg:#fdf0f8; --card:#fff; --line:#e1bee7; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,"Noto Sans Thai",sans-serif; background:var(--bg); color:#222; }}
header {{ background:#fff; border-bottom:4px solid var(--pink); padding:20px 16px 16px; }}
.wrap {{ max-width:1100px; margin:0 auto; padding:0 12px 48px; }}
h1 {{ margin:0 0 8px; font-size:1.5rem; color:var(--lilac); }}
.disclose {{ background:#fff8e1; border-left:4px solid #f9a825; padding:10px 12px; margin:12px 0; border-radius:8px; font-size:14px; }}
.warn {{ background:#fff; border-left:4px solid var(--pink); padding:10px 12px; margin:12px 0; border-radius:8px; font-size:14px; color:#880e4f; }}
.toolbar {{ display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 16px; align-items:center; }}
input, select {{ font:inherit; padding:8px 10px; border:1px solid var(--line); border-radius:10px; min-width:180px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:12px; }}
.card {{ background:var(--card); border:1.5px solid var(--line); border-radius:14px; padding:14px; display:flex; flex-direction:column; gap:6px; }}
.card h3 {{ margin:0; color:var(--lilac); font-size:1.05rem; }}
.full {{ margin:0; font-size:12px; color:#555; }}
.price {{ margin:0; font-size:1.2rem; font-weight:800; color:var(--pink); }}
.meta, .cat {{ font-size:12px; color:#6a1b9a; }}
.row {{ display:flex; gap:6px; align-items:center; flex-wrap:wrap; }}
.badge {{ font-size:11px; background:#f3e5f5; color:var(--lilac); padding:2px 6px; border-radius:999px; }}
.btn {{ display:block; text-align:center; background:var(--pink); color:#fff; text-decoration:none; font-weight:700; padding:10px; border-radius:10px; margin-top:auto; }}
.btn:hover {{ background:#ad1457; }}
footer {{ font-size:13px; color:#555; margin-top:28px; }}
.hidden {{ display:none; }}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>ของใช้ดีราคาเบา ที่น้องมิวรีวิว</h1>
<p>รวมสินค้าจากหน้าร้าน <a href="https://collshp.com/mewstory_review" rel="noopener" target="_blank">collshp.com/mewstory_review</a> ของช่องน้องมิว Mew Story</p>
</header>
<div class="disclose"><strong>เปิดเผยลิงก์แอฟฟิลิเอต:</strong> เมื่อซื้อผ่านลิงก์ในหน้านี้ ช่องน้องมิวอาจได้รับค่าคอมจาก Shopee การเป็นลิงก์แอฟฟิลิเอตไม่ได้ทำให้ผู้ซื้อจ่ายแพงขึ้น</div>
<div class="warn"><strong>{date_label}</strong><br>{refresh_note} ราคา ยอดขาย และเรตติ้งอาจไม่ตรงของวันนี้ ให้กดดูราคาล่าสุดบน Shopee ก่อนซื้อ หน้านี้ไม่มีรีวิวที่แต่งขึ้น และไม่รับประกันยอดขายหรือรายได้</div>
<div class="toolbar">
<input id="q" type="search" placeholder="ค้นหาชื่อสินค้า" aria-label="ค้นหาชื่อสินค้า">
<select id="cat" aria-label="หมวดสินค้า"><option value="">ทุกหมวด</option>
{options}
</select>
<span id="count"></span>
</div>
<section class="grid" id="grid">
{"".join(cards)}
</section>
<footer>
<p>สร้างหน้านี้เมื่อ {escape(stamp)} จำนวน {len(rows)} รายการที่ลิงก์ขึ้นต้นด้วย https://s.shopee.co.th/</p>
<p>ช่องทางอื่น: เพจ Facebook น้องมิว Mew Story · IG @miu_mewstory</p>
<p>อัปเดตรายวันด้วย GitHub Actions ฟรี ไม่ใช้ AI รหัสต้นทางอยู่ที่ <a href="https://github.com/glasskitchenware-cmd/mew-review">github.com/glasskitchenware-cmd/mew-review</a></p>
</footer>
</div>
<script>
const q=document.getElementById('q'), cat=document.getElementById('cat'), cards=[...document.querySelectorAll('.card')], count=document.getElementById('count');
function filt(){{
  const s=(q.value||'').trim().toLowerCase(), c=cat.value;
  let n=0;
  cards.forEach(el=>{{
    const ok=(!c||el.dataset.cat===c)&&(!s||(el.dataset.name||'').toLowerCase().includes(s));
    el.classList.toggle('hidden',!ok); if(ok)n++;
  }});
  count.textContent=n+' รายการ';
}}
q.addEventListener('input',filt); cat.addEventListener('change',filt); filt();
</script>
</body>
</html>
"""


def main():
    rows = load_products()
    now = datetime.now(TZ)
    html = render(rows, now, load_status())
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"wrote {OUT_PATH} items={len(rows)} at {now.isoformat()}")


if __name__ == "__main__":
    main()
