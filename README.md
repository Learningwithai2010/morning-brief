# Maxi's Morning Brief

Every morning at **7:00am ET**, a GitHub Actions workflow uses the Claude API to research and write a personalized news briefing — politics, tech & AI, soccer, and basketball — then publishes it to GitHub Pages and texts you the link.

No server. No local machine. Fully autonomous.

---

## Setup Guide

### 1. Fork or clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/morning-brief.git
cd morning-brief
```

### 2. Enable GitHub Pages

1. Go to your repo on GitHub → **Settings** → **Pages**
2. Under **Source**, select **Deploy from a branch**
3. Set branch to `main` and folder to `/docs`
4. Click **Save**

Your archive page will be live at `https://YOUR_USERNAME.github.io/morning-brief/`.

> The `docs/.nojekyll` file in this repo prevents GitHub from running Jekyll on your HTML files — this is already included, no action needed.

### 3. Set up a Twilio account (free)

1. Sign up for a free trial at [twilio.com/try-twilio](https://www.twilio.com/try-twilio) — you get ~$15 in credit, which lasts months at this volume (~1 SMS/day ≈ $0.01)
2. From the Twilio Console, grab a phone number (US toll-free or local works fine)
3. Note your **Account SID**, **Auth Token**, and **From Number** — you'll add these as GitHub secrets

> **Free trial note:** Free Twilio trial accounts prepend "Sent from a Twilio trial account" to every message. To remove this, upgrade to a paid account (still very cheap at ~$1/month for the number + usage).

### 4. Get your Anthropic API key

Sign in at [console.anthropic.com](https://console.anthropic.com) → **API Keys** → **Create Key**.

### 5. Add GitHub Actions secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Add all four:

| Secret name | Where to find it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `TWILIO_ACCOUNT_SID` | Twilio Console dashboard |
| `TWILIO_AUTH_TOKEN` | Twilio Console dashboard |
| `TWILIO_FROM_NUMBER` | Your Twilio number in `+1XXXXXXXXXX` format |

`GITHUB_TOKEN` is automatically provided by GitHub Actions — no action needed.

### 6. That's it

The workflow runs every day at **11:00 UTC (7:00am EDT)**. After setup, push to `main` and the next morning you'll receive your first brief.

---

## Manual trigger (for testing)

1. Go to your repo on GitHub → **Actions** → **Morning Brief**
2. Click **Run workflow** → **Run workflow**

This lets you test the full pipeline without waiting for 7am.

---

## Timezone note

The cron schedule is `0 11 * * *` UTC, which equals **7:00am EDT (UTC-4)** — the timezone from March through November.

When clocks fall back in **November** (EST = UTC-5), 7:00am ET = 12:00 UTC. To adjust:

1. Open `.github/workflows/morning-brief.yml`
2. Change `cron: "0 11 * * *"` → `cron: "0 12 * * *"`
3. Commit and push

Reverse this in **March** when clocks spring forward. A calendar reminder is your friend here.

---

## Costs

| Service | Cost |
|---|---|
| Anthropic API (Claude Sonnet) | ~$0.05–0.15/day |
| Twilio SMS (1 message/day) | ~$0.01/day + ~$1/month for the number |
| GitHub Actions (public repo) | Free |
| GitHub Pages | Free |

**Total: roughly $2–5/month.**

---

## Repository structure

```
morning-brief/
├── .github/workflows/morning-brief.yml   # Cron job: runs daily at 7am ET
├── docs/                                  # GitHub Pages root
│   ├── .nojekyll                          # Disables Jekyll processing
│   └── index.html                         # Archive listing all past briefs
├── scripts/
│   ├── generate_brief.py                  # Calls Claude API → brief_data.json
│   ├── publish_page.py                    # Renders HTML → commits to docs/
│   └── send_text.py                       # Sends SMS via Twilio
├── templates/
│   └── brief_template.html                # HTML template for daily brief page
├── requirements.txt
└── README.md
```
