# 🏠 Live With Ease

Are you a student or new grad in Toronto struggling to stay on top of affordable rentals? Live With Ease is a web app that scrapes any rental site, filters listings by your budget using AI, and emails you the results, once or on a recurring schedule.

**[→ Try it live](https://live-with-ease.vercel.app/)**

![live-with-ease screenshot](project2.png)

---

## Features

- 🔍 **Scrapes any rental site** — paste any URL, not locked to one source
- 🤖 **AI-powered extraction** — Llama 3 via Groq reads the page; no brittle CSS selectors
- 💸 **Budget filtering** — only shows listings under your price limit
- 📬 **One-time email digest** — send results to yourself with one click
- 🔁 **Recurring subscriptions** — get weekly or monthly updates automatically
- 🚪 **Unsubscribe anytime** — every recurring email includes a one-click unsubscribe link

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite, deployed on Vercel |
| Backend | Python + FastAPI, deployed on Railway |
| Browser automation | Playwright (handles JS-rendered pages) |
| AI extraction | Groq API (free) with Llama 3.1 |
| Email | Resend API |
| Database | PostgreSQL on Railway |
| Scheduling | APScheduler (runs inside FastAPI) |

---

## Usage

1. Go to **[live-with-ease.vercel.app](https://live-with-ease.vercel.app/)**
2. Paste any rental site URL (e.g. `https://www.zumper.com/apartments-for-rent/toronto-on`)
3. Enter your monthly budget in CAD and hit **Search listings**
4. Browse results — click **View →** to open any listing
5. Enter your email and choose **Send once**, **Weekly**, or **Monthly**
6. Recurring subscribers can unsubscribe anytime via the link in any email

---

## Running Locally

Want to fork this and run it yourself? You'll need:

| Variable | Where to get it |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free |
| `RESEND_API_KEY` | [resend.com](https://resend.com) — free |
| `DATABASE_URL` | PostgreSQL connection string |

```bash
# Backend
cd backend && pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**.

---

## Security

- Never commit your `.env` file — it's in `.gitignore`
- Use `.env.example` as a template to share instead
