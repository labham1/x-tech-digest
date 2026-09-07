import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    ENV_PATH = BASE_DIR / ".env"
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
    else:
        load_dotenv()
except ImportError:
    pass  # python-dotenv not installed yet, rely on standard os.environ

# Gemini AI Configuration (Free Tier via Google AI Studio)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# X (Twitter) Session Configuration
SESSION_FILE = Path(os.getenv("SESSION_FILE", BASE_DIR / "session.json"))
X_FEED_URL = os.getenv("X_FEED_URL", "https://x.com/home")
MAX_TWEETS_TO_SCAN = int(os.getenv("MAX_TWEETS_TO_SCAN", "60"))
SCROLL_COUNT = int(os.getenv("SCROLL_COUNT", "8"))
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")

# Email Delivery Configuration (Free via Gmail SMTP or standard SMTP)
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp").lower()  # "smtp" or "resend"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")  # For Gmail, use an App Password
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USER)
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

# Optional Resend API configuration (if user chooses Resend)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# Digest Customization
DIGEST_TITLE = os.getenv("DIGEST_TITLE", "Your Morning Tech Radar ⚡")
NEWSLETTER_PREVIEW_PATH = BASE_DIR / "preview_newsletter.html"
