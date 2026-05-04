import json
import os
import re
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

app = FastAPI(title="live-with-ease API")

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


# ── Page fetcher ──────────────────────────────────────────────────────────────
def fetch_page_text(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise HTTPException(500, "Playwright not installed. Run: pip install playwright && playwright install chromium")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            # Give JS a moment to render listings
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
        raise HTTPException(500, "OpenAI SDK not installed. Run: pip install openai")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(500, "GROQ_API_KEY not set in .env file. Get a free key at https://console.groq.com")

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
        model="llama3-8b-8192",
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


# ── HTML email builder ────────────────────────────────────────────────────────
def build_html_email(listings: list, budget: float, site_url: str) -> str:
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
              Powered by live-with-ease
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


# ── Routes ────────────────────────────────────────────────────────────────────
@app.post("/scrape")
def scrape(req: ScrapeRequest):
    try:
        page_text = fetch_page_text(req.url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page fetch failed: {type(e).__name__}: {e}")

    try:
        all_found = extract_listings_with_ai(page_text, req.url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {type(e).__name__}: {e}")

    listings = []
    for apt in all_found:
        try:
            price = float(apt.get("price", 0))
        except (TypeError, ValueError):
            price = 0
        if 0 < price < req.budget:
            listings.append({
                "building": apt.get("building", "Unknown"),
                "area":     apt.get("area", ""),
                "price":    price,
                "url":      apt.get("url", req.url),
            })

    return {"listings": listings}


@app.post("/email")
def send_email(req: EmailRequest):
    try:
        import resend
    except ImportError:
        raise HTTPException(500, "Resend not installed. Run: pip install resend")

    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        raise HTTPException(500, "RESEND_API_KEY not set in .env file.")

    count = len(req.listings)
    domain = re.sub(r"https?://(www\.)?", "", req.site_url).split("/")[0]

    resend.Emails.send({
        "from": "live-with-ease <onboarding@resend.dev>",
        "to": [req.email],
        "subject": f"🏠 {count} listing{'s' if count != 1 else ''} on {domain} under ${req.budget:,.0f}",
        "html": build_html_email(req.listings, req.budget, req.site_url),
    })

    return {"success": True}
