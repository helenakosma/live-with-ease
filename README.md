# 🏠 live-with-ease

A web app for finding Toronto rentals within your budget, powered by AI.

Paste any rental site URL, set your budget, and get a clean list of matching listings in seconds. Optionally email the results to yourself.

![live-with-ease screenshot](https://i.imgur.com/placeholder.png)

---

## Features

- 🔍 **Scrapes any rental site** — not locked to one source
- 🤖 **AI-powered extraction** — no brittle CSS selectors, works across different site layouts
- 💸 **Budget filtering** — only shows listings under your price limit
- 📬 **Email digest** — send results to yourself with one click
- 🔁 **Deduplication** — tracks seen listings so you only get notified about new ones

---

## Tech Stack

- **Frontend** — React + Vite
- **Backend** — Python + FastAPI
- **Browser automation** — Playwright (handles JavaScript-rendered pages)
- **AI extraction** — Groq (free) with Llama 3
- **Email** — Resend API

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/helenakosma/live-with-ease.git
cd live-with-ease
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Fill in `.env` with your keys:

| Variable | Where to get it |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free |
| `RESEND_API_KEY` | [resend.com](https://resend.com) — free |
| `SITE_URL` | Any rental listings page URL |
| `BUDGET` | Your monthly budget in CAD |
| `EMAIL` | Your email address |

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Usage

1. Paste a rental site URL (e.g. `https://www.zumper.com/apartments-for-rent/toronto-on`)
2. Enter your monthly budget in CAD
3. Hit **Search listings**
4. Browse results — click **View →** to open any listing
5. Optionally enter your email and hit **Send** to get a formatted digest in your inbox

---

## Security

- Never commit your `.env` file — it's listed in `.gitignore`
- Use `.env.example` as a template and share that instead
