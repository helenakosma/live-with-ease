import json
import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise HTTPException(500, "DATABASE_URL not set.")
    return psycopg2.connect(url, cursor_factory=RealDictCursor, sslmode="require")

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                site_url TEXT NOT NULL,
                budget REAL NOT NULL,
                frequency TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL,
                last_sent TIMESTAMP,
                next_run TIMESTAMP NOT NULL
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[INFO] Database initialised.")
    except Exception as e:
        print(f"[WARN] DB init failed: {e}")


# ── Scheduler ─────────────────────────────────────────────────────────────────
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(check_subscriptions, "interval", hours=1, id="subscription_check")
    scheduler.start()
    yield
    scheduler.shutdown()


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="live-with-ease API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ────────────────────────────────────────────────────────────
class ScrapeRequest(BaseModel):
    url: str
    budget: float

class EmailRequest(BaseModel):
    listings: list
    budget: float
    site_url: str
    email: str

class SubscribeRequest(BaseModel):
    email: str
    site_url: str
    budget: float
    frequency: str  # 'weekly' or 'monthly'


# ── Page fetcher ──────────────────────────────────────────────────────────────
def fetch_page_text(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise HTTPException(500, "Playwright not installed.")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(3000)
        except Exception as e:
            browser.close()
            raise HTTPException(502, f"Page failed to load: {e}")

        text = page.inner_text("body")
        browser.close()

    if len(text) > 12_000:
        text = text[:12_000] + "\n...[truncated]"
    return text


# ── AI extraction ─────────────────────────────────────────────────────────────
def extract_listings_with_ai(page_text: str, site_url: str) -> list[dict]:
    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(500, "OpenAI SDK not installed.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(500, "GROQ_API_KEY not set.")

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    prompt = f"""Below is the visible text scraped from a rental listings page: {site_url}

Extract every rental listing and return them as a JSON array.
Each item must have:
  - "building": name of the building or property (string)
  - "area": neighbourhood or address (string, empty string if unknown)
  - "price": monthly price as a number in CAD (integer or float, 0 if not found)
  - "url": direct link to the listing (string, use the site base URL if no specific link is visible)

Return ONLY a raw JSON array — no markdown, no explanation, no code fences.
If no listings found, return [].

Page text:
{page_text}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        listings = json.loads(raw)
        return listings if isinstance(listings, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def filter_listings(all_found: list, budget: float, site_url: str) -> list:
    listings = []
    for apt in all_found:
        try:
            price = float(apt.get("price", 0))
        except (TypeError, ValueError):
            price = 0
        if 0 < price < budget:
            listings.append({
                "building": apt.get("building", "Unknown"),
                "area":     apt.get("area", ""),
                "price":    price,
                "url":      apt.get("url", site_url),
            })
    return listings


# ── HTML email builder ────────────────────────────────────────────────────────
def build_html_email(listings: list, budget: float, site_url: str,
                     unsubscribe_url: str = None, frequency: str = None) -> str:
    today = date.today().strftime("%B %d, %Y")
    count = len(listings)
    domain = re.sub(r"https?://(www\.)?", "", site_url).split("/")[0]

    rows = ""
    for apt in listings:
        rows += f"""
        <tr>
          <td style="padding:12px 16px; border-bottom:1px solid #eee;">
            <a href="{apt['url']}" style="color:#2563eb; font-weight:600; text-decoration:none;">
              {apt['building']}
            </a>
          </td>
          <td style="padding:12px 16px; border-bottom:1px solid #eee; color:#555;">{apt['area']}</td>
          <td style="padding:12px 16px; border-bottom:1px solid #eee; font-weight:700; color:#16a34a; white-space:nowrap;">
            ${apt['price']:,.0f}/mo
          </td>
          <td style="padding:12px 16px; border-bottom:1px solid #eee;">
            <a href="{apt['url']}" style="background:#2563eb; color:#fff; padding:6px 14px;
               border-radius:6px; text-decoration:none; font-size:13px; white-space:nowrap;">
              View →
            </a>
          </td>
        </tr>"""

    freq_note = f"You're receiving this because you subscribed to {frequency} updates." if frequency else ""
    unsub_link = (f'<a href="{unsubscribe_url}" style="color:#9ca3af;">Unsubscribe</a>'
                  if unsubscribe_url else "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0; padding:0; background:#f3f4f6; font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 16px;">
    <tr><td align="center">
      <table width="620" cellpadding="0" cellspacing="0"
             style="background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,.08);">
        <tr>
          <td style="background:#2563eb; padding:28px 32px;">
            <h1 style="margin:0; color:#fff; font-size:22px; font-weight:700;">🏠 live-with-ease</h1>
            <p style="margin:6px 0 0; color:#bfdbfe; font-size:14px;">{domain} &nbsp;·&nbsp; {today}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 8px;">
            <p style="margin:0; font-size:15px; color:#374151;">
              Found <strong>{count} listing{"s" if count != 1 else ""}</strong> under <strong>${budget:,.0f}/mo</strong>.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse; font-size:14px;">
              <thead>
                <tr style="background:#f9fafb;">
                  <th style="padding:10px 16px; text-align:left; color:#6b7280; font-weight:600; border-bottom:2px solid #e5e7eb;">Building</th>
                  <th style="padding:10px 16px; text-align:left; color:#6b7280; font-weight:600; border-bottom:2px solid #e5e7eb;">Neighbourhood</th>
                  <th style="padding:10px 16px; text-align:left; color:#6b7280; font-weight:600; border-bottom:2px solid #e5e7eb;">Price</th>
                  <th style="padding:10px 16px; border-bottom:2px solid #e5e7eb;"></th>
                </tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background:#f9fafb; padding:16px 32px; border-top:1px solid #e5e7eb;">
            <p style="margin:0; font-size:12px; color:#9ca3af; text-align:center;">
              {freq_note} {unsub_link}
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


# ── Email sender ──────────────────────────────────────────────────────────────
def send_resend_email(to: str, subject: str, html: str):
    import resend
    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        raise HTTPException(500, "RESEND_API_KEY not set.")
    resend.Emails.send({
        "from": "live-with-ease <onboarding@resend.dev>",
        "to": [to],
        "subject": subject,
        "html": html,
    })


# ── Subscription checker (runs every hour) ────────────────────────────────────
async def check_subscriptions():
    print("[SCHEDULER] Checking subscriptions...")
    now = datetime.utcnow()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM subscriptions WHERE next_run <= %s", (now,))
        due = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[SCHEDULER] DB error: {e}")
        return

    for sub in due:
        try:
            page_text = fetch_page_text(sub["site_url"])
            all_found = extract_listings_with_ai(page_text, sub["site_url"])
            listings  = filter_listings(all_found, sub["budget"], sub["site_url"])

            if listings:
                backend_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
                if backend_url:
                    backend_url = f"https://{backend_url}"
                unsub_url = f"{backend_url}/unsubscribe/{sub['token']}" if backend_url else None
                domain = re.sub(r"https?://(www\.)?", "", sub["site_url"]).split("/")[0]
                html = build_html_email(listings, sub["budget"], sub["site_url"],
                                        unsubscribe_url=unsub_url, frequency=sub["frequency"])
                send_resend_email(
                    sub["email"],
                    f"🏠 {len(listings)} new listing{'s' if len(listings)!=1 else ''} on {domain}",
                    html
                )
                print(f"[SCHEDULER] Sent {len(listings)} listings to {sub['email']}")

            # Schedule next run
            delta = timedelta(weeks=1) if sub["frequency"] == "weekly" else timedelta(days=30)
            next_run = now + delta
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE subscriptions SET last_sent=%s, next_run=%s WHERE id=%s",
                        (now, next_run, sub["id"]))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[SCHEDULER] Failed for {sub['email']}: {e}")


# ── Routes ────────────────────────────────────────────────────────────────────
@app.post("/scrape")
def scrape(req: ScrapeRequest):
    try:
        page_text = fetch_page_text(req.url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Page fetch failed: {type(e).__name__}: {e}")

    try:
        all_found = extract_listings_with_ai(page_text, req.url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"AI extraction failed: {type(e).__name__}: {e}")

    return {"listings": filter_listings(all_found, req.budget, req.url)}


@app.post("/email")
def send_email(req: EmailRequest):
    count  = len(req.listings)
    domain = re.sub(r"https?://(www\.)?", "", req.site_url).split("/")[0]
    send_resend_email(
        req.email,
        f"🏠 {count} listing{'s' if count!=1 else ''} on {domain} under ${req.budget:,.0f}",
        build_html_email(req.listings, req.budget, req.site_url)
    )
    return {"success": True}


@app.post("/subscribe")
def subscribe(req: SubscribeRequest):
    if req.frequency not in ("weekly", "monthly"):
        raise HTTPException(400, "frequency must be 'weekly' or 'monthly'")

    sub_id = str(uuid.uuid4())
    token  = str(uuid.uuid4())
    now    = datetime.utcnow()
    delta  = timedelta(weeks=1) if req.frequency == "weekly" else timedelta(days=30)

    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO subscriptions (id, email, site_url, budget, frequency, token, created_at, next_run)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (sub_id, req.email, req.site_url, req.budget, req.frequency, token, now, now + delta))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        raise HTTPException(500, f"Could not save subscription: {e}")

    return {"success": True, "message": f"Subscribed! You'll receive {req.frequency} updates."}


@app.get("/unsubscribe/{token}", response_class=HTMLResponse)
def unsubscribe(token: str):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM subscriptions WHERE token = %s RETURNING email", (token,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return HTMLResponse(f"<h2>Something went wrong: {e}</h2>", status_code=500)

    if row:
        return HTMLResponse("""<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{{font-family:'Helvetica Neue',Arial,sans-serif;display:flex;align-items:center;
        justify-content:center;min-height:100vh;margin:0;background:#f0f4ff}}
        .box{{background:#fff;border-radius:16px;padding:48px;text-align:center;
        box-shadow:0 2px 20px rgba(0,0,0,.08);max-width:400px}}</style></head>
        <body><div class="box"><div style="font-size:48px">✅</div>
        <h2 style="color:#1e293b;margin:16px 0 8px">Unsubscribed</h2>
        <p style="color:#64748b">You've been removed from live-with-ease updates.</p>
        <a href="https://live-with-ease.vercel.app" style="color:#2563eb">Back to app →</a>
        </div></body></html>""")
    else:
        return HTMLResponse("""<!DOCTYPE html><html><body style="font-family:sans-serif;text-align:center;padding:48px">
        <h2>Link not found</h2><p>This unsubscribe link may have already been used.</p>
        </body></html>""", status_code=404)
