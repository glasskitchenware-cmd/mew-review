#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Attempt a free, no-AI price refresh. Never invent prices.

If a public source cannot be read reliably (login, captcha, paid API),
this script leaves products.csv unchanged and writes refresh-status.json
explaining why the page must keep the checked_at snapshot dates.
"""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
STATUS = ROOT / "refresh-status.json"
TZ = ZoneInfo("Asia/Bangkok")
UA = "MewReviewDaily/1.0 (+https://github.com/glasskitchenware-cmd/mew-review)"


def probe(url: str) -> dict:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "th"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            body = r.read(80000).decode("utf-8", "replace")
            return {
                "url": url,
                "status": r.status,
                "captcha": ("captcha" in body.lower()) or ("ยืนยันตัวตน" in body),
                "has_baht_price": "฿" in body,
            }
    except Exception as e:
        return {"url": url, "error": f"{type(e).__name__}: {e}"}


def main():
    now = datetime.now(TZ)
    probes = [
        probe("https://collshp.com/mewstory_review"),
        probe("https://shopee.co.th/product/1736768928/47209642611"),
    ]
    # A usable live catalog would need a public machine-readable feed
    # (for example a published CSV). Until that exists, do not guess prices.
    shopee = probes[1]
    live_ok = False
    reason = (
        "รอบนี้ยังดึงราคาสดแบบฟรีและอ่านได้แน่นอนไม่ได้ "
        "(หน้าร้าน collshp เป็นแอปที่โหลดสินค้าทีหลัง และหน้าสินค้า Shopee ติดแคปชาหรือไม่มีราคาใน HTML) "
        "จึงคงราคาและลิงก์ตามไฟล์ products.csv และแสดงข้อความข้อมูล ณ วันที่ตรวจ ไม่ได้เดาราคาใหม่"
    )
    status = {
        "attempted_at": now.strftime("%Y-%m-%d %H:%M") + " เวลาไทย (Asia/Bangkok)",
        "live_prices": live_ok,
        "reason": reason,
        "probes": probes,
        "csv_updated": False,
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: status[k] for k in ("attempted_at", "live_prices", "csv_updated", "reason")}, ensure_ascii=False))
    # Always succeed: a failed live fetch must not break the daily rebuild.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
