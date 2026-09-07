# ⚡ Automated Daily X Tech Digest (100% Free)

An automated morning newsletter system that monitors your **X (Twitter)** feed, isolates technical content (AI/ML, software architecture, open source tools, frameworks), summarizes discussions using **Google Gemini AI**, and delivers an email to your inbox every morning.

---

## 💡 Why This Setup is 100% Free

1. **No X API Subscription Needed**: Avoids the $100/mo X API fee by using a local headless Playwright browser session with your saved auth cookies.
2. **Free AI Summaries**: Uses **Google Gemini 2.5 Flash** via Google AI Studio's free tier (up to 15 requests per minute, more than enough for a daily digest).
3. **Free Email Dispatch**: Uses your existing Gmail account with a standard **Google App Password** over SMTP.
4. **Free Automation**: Runs on **Windows Task Scheduler** on your PC or on **GitHub Actions** in the cloud.

---

## 📁 Project Structure

```
D:\Project_WorkSpace\x-tech-digest\
│
├── .env.example                    # Configuration template with guides
├── requirements.txt                # Python dependencies
├── setup_auth.py                   # One-time tool to log in & capture session
├── main.py                         # Daily morning execution script
├── run_digest.bat                  # One-click Windows Task Scheduler runner
│
├── config/
│   └── settings.py                 # Configuration and environment variables
│
├── extractor/
│   ├── session.py                  # Session cookie management
│   └── scraper.py                  # Headless Playwright feed extractor
│
├── processor/
│   ├── filter.py                   # Heuristic spam & non-tech noise filter
│   └── summarizer.py               # Gemini AI structuring and summarization
│
├── mailer/
│   ├── renderer.py                 # Jinja2 newsletter builder
│   ├── sender.py                   # SMTP (Gmail) / Resend email dispatcher
│   └── templates/
│       └── newsletter.html         # Responsive email template
│
└── .github/workflows/
    └── daily_digest.yml            # Cloud cron runner (optional)
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies

Open PowerShell in this directory:
```powershell
cd D:\Project_WorkSpace\x-tech-digest

# Recommended: create a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

---

### 2. Configure Credentials (`.env`)

Create your `.env` file from the template:
```powershell
cp .env.example .env
```

Open `.env` and fill in:

#### A. Free Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account and click **"Get API key"**.
3. Set `GEMINI_API_KEY=your_key_here`.

#### B. Gmail Free SMTP Credentials
1. Go to your [Google Account Security](https://myaccount.google.com/security) settings.
2. Ensure **2-Step Verification** is turned ON.
3. Visit [App Passwords](https://myaccount.google.com/apppasswords).
4. Create a new App Password named **"X Tech Digest"**.
5. Copy the generated 16-character password into `.env`:
   ```env
   SMTP_USER=your_email@gmail.com
   SMTP_PASS=xxxx xxxx xxxx xxxx
   RECIPIENT_EMAIL=your_email@gmail.com
   ```

---

### 3. Log In to X (One-Time Setup)

Run the interactive session creator:
```powershell
python setup_auth.py
```
1. A Chromium browser window will open automatically.
2. Log in to your X (Twitter) account as usual.
3. Once you see your home timeline, press **Enter** in the terminal.
4. Your authenticated session will be saved to `session.json`.

---

### 4. Test & Preview the Newsletter

You can test the entire pipeline without sending an email using the `--preview` flag:
```powershell
# Test with mock data first:
python main.py --mock --preview

# Test with your live X feed:
python main.py --preview
```

This generates `preview_newsletter.html`. Open it in any browser to see exactly how your morning email will look!

To test a full live run including email delivery:
```powershell
python main.py --mock   # Sends test email using mock data
python main.py          # Sends morning digest from your live X feed
```

---

## ⏰ How to Schedule for Every Morning

### Option A: Windows Task Scheduler (Recommended Local)

1. Press `Win + R`, type `taskschd.msc`, and hit **Enter**.
2. Click **"Create Basic Task..."** on the right panel.
3. **Name**: `Daily X Tech Digest`.
4. **Trigger**: Select **Daily** and set your preferred morning time (e.g., `07:00 AM`).
5. **Action**: Select **Start a program**.
6. **Program/script**: Browse and select:
   ```
   D:\Project_WorkSpace\x-tech-digest\run_digest.bat
   ```
7. **Start in (optional)**: Set to:
   ```
   D:\Project_WorkSpace\x-tech-digest
   ```
8. Click **Finish**.

Now, your computer will automatically run the digest every morning and log results into `logs/run_YYYY-MM-DD.log`.

---

### Option B: Cloud Automation (GitHub Actions)

If you prefer not having your PC on in the morning:
1. Create a private GitHub repository and push this directory.
2. Go to **Settings > Secrets and variables > Actions > New repository secret**.
3. Add:
   - `GEMINI_API_KEY`
   - `SMTP_USER`
   - `SMTP_PASS`
   - `RECIPIENT_EMAIL`
   - `X_SESSION_JSON`: Paste the entire content of your local `session.json`.
4. The workflow in `.github/workflows/daily_digest.yml` will run automatically every morning at 7:00 AM IST!
