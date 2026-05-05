import json
import os
import re
from datetime import date

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # optional: pip install python-dotenv


# ── Deduplication helpers ─────────────────────────────────────────────────────
def cache_path(url: str) -> str:
    """One cache file per site, stored next to this script."""
    slug = re.sub(r"[^a-z0-9]", "_", url.lower())[:60]
    return os.path.join(os.path.dirname(__file__), f"seen_{slug}.json")

def load_seen(url: str) -> set:
    path = cache_path(url)
    if os.path.exists(path):
        with open(path) as f:
            return set(json.load(f))
    return set()

def save_seen(url: str, seen: set):
    with open(cache_path(url), "w") as f:
        json.dump(list(seen), f, indent=2)


# ── Page fetcher (Playwright) ─────────────────────────────────────────────────
def fetch_page_text(url: str) -> str:
    """
    Fetches the page using requests + BeautifulSoup and returns visible text.
    """
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    print(f"[INFO] Loading {url} ...")
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove script/style noise
    for tag in soup(["script", "style", "noscript", "head"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)

    # Trim to ~12,000 chars to stay within a reasonable token budget
    if len(text) > 12_000:
        text = text[:12_000] + "\n...[truncated]"
    return text


# ── AI extraction ─────────────────────────────────────────────────────────────
def extract_listings_with_ai(page_text: str, site_url: str) -> list[dict]:
    """
    Sends the page text to Groq and asks it to extract rental listings as JSON.
    Requires GROQ_API_KEY in environment / .env file.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise SystemExit("[ERROR] OpenAI SDK not installed.\nRun: pip install openai")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("[ERROR] GROQ_API_KEY not set. Add it to your .env file.")

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    prompt = f"""Below is the visible text scraped from a rental listings page: {site_url}

Your job is to extract every rental listing you can find and return them as a JSON array.
Each item must have these fields:
  - "building": name of the building or property (string)
  - "area": neighbourhood or address (string, empty string if unknown)
  - "price": monthly price as a number in CAD (integer or float, 0 if not found)
  - "url": direct link to the listing (string, use the site's base URL if no specific link is visible)

Rules:
- Return ONLY a raw JSON array — no markdown, no explanation, no code fences.
- If you cannot find any listings, return an empty array: []
- Do not invent listings. Only include what is clearly present in the text.

Page text:
{page_text}"""

    print("[INFO] Asking Groq to extract listings...")
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if Claude wrapped it anyway
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        listings = json.loads(raw)
        if not isinstance(listings, list):
            raise ValueError("Response was not a JSON array")
        return listings
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[WARN] Could not parse AI response: {e}")
        print(f"[WARN] Raw response: {raw[:500]}")
        return []


# ── Main scrape pipeline ──────────────────────────────────────────────────────
def get_apartments(site_url: str, budget: float) -> tuple[list[dict], list[dict]]:
    """Returns (new_listings, all_listings) filtered by budget."""
    page_text = fetch_page_text(site_url)
    all_found  = extract_listings_with_ai(page_text, site_url)

    seen = load_seen(site_url)
    all_listings, new_listings = [], []

    for apt in all_found:
        try:
            price = float(apt.get("price", 0))
        except (TypeError, ValueError):
            price = 0

        if price <= 0 or price >= budget:
            continue

        listing = {
            "building": apt.get("building", "Unknown"),
            "area":     apt.get("area", ""),
            "price":    price,
            "url":      apt.get("url", site_url),
        }
        all_listings.append(listing)
        if listing["url"] not in seen:
            new_listings.append(listing)

    seen.update(l["url"] for l in all_listings)
    save_seen(site_url, seen)

    print(f"[INFO] {len(all_listings)} listings within budget, {len(new_listings)} new.")
    return new_listings, all_listings


# ── HTML email ────────────────────────────────────────────────────────────────
def build_html_email(listings: list[dict], budget: float, site_url: str) -> str:
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
          <td style="padding:12px 16px; border-bottom:1px solid #eee; color:#555;">
            {apt['area']}
          </td>
          <td style="padding:12px 16px; border-bottom:1px solid #eee; font-weight:700; color:#16a34a; white-space:nowrap;">
            ${apt['price']:,.0f}/mo
          </td>
          <td style="padding:12px 16px; border-bottom:1px solid #eee;">
            <a href="{apt['url']}"
               style="background:#2563eb; color:#fff; padding:6px 14px; border-radius:6px;
                      text-decoration:none; font-size:13px; white-space:nowrap;">
              View →
            </a>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0; padding:0; background:#f3f4f6; font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 16px;">
    <tr><td align="center">
      <table width="620" cellpadding="0" cellspacing="0"
             style="background:#fff; border-radius:12px; overflow:hidden;
                    box-shadow:0 2px 12px rgba(0,0,0,.08);">
        <tr>
          <td style="background:#2563eb; padding:28px 32px;">
            <h1 style="margin:0; color:#fff; font-size:22px; font-weight:700;">🏠 live-with-ease</h1>
            <p style="margin:6px 0 0; color:#bfdbfe; font-size:14px;">
              {domain} &nbsp;·&nbsp; {today}
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 8px;">
            <p style="margin:0; font-size:15px; color:#374151;">
              Found <strong>{count} new listing{"s" if count != 1 else ""}</strong>
              under <strong>${budget:,.0f}/mo</strong> since your last check.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border-collapse:collapse; font-size:14px;">
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
              Powered by live-with-ease · Only new listings are shown each run
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ── Email sender (Resend) ─────────────────────────────────────────────────────
def email_user(listings: list[dict], budget: float, site_url: str, user_email: str):
    try:
        import resend
    except ImportError:
        raise SystemExit("[ERROR] Resend not installed.\nRun: pip install resend")

    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        raise SystemExit("[ERROR] RESEND_API_KEY not set. Add it to your .env file.")

    count = len(listings)
    domain = re.sub(r"https?://(www\.)?", "", site_url).split("/")[0]

    resend.Emails.send({
        "from": "live-with-ease <onboarding@resend.dev>",
        "to": [user_email],
        "subject": f"🏠 {count} new listing{'s' if count != 1 else ''} on {domain} under ${budget:,.0f}",
        "html": build_html_email(listings, budget, site_url),
    })
    print(f"[INFO] Email sent to {user_email} successfully.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    site_url   = os.getenv("SITE_URL") or input("Enter the rental site URL: ").strip()
    budget_env = os.getenv("BUDGET")
    user_email = os.getenv("EMAIL")    or input("Enter your email: ").strip()
    budget     = float(budget_env) if budget_env else float(input("Enter your budget (in CAD): ").strip())

    new_listings, _ = get_apartments(site_url, budget)

    if new_listings:
        email_user(new_listings, budget, site_url, user_email)
    else:
        print("No new listings found since last run.")


if __name__ == "__main__":
    main()
