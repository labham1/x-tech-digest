#!/usr/bin/env python3
"""X Tech Digest - Daily Morning Technology Briefing

Extracts tech posts from your X timeline, curates & summarizes them with Gemini AI,
and delivers a clean HTML digest to your email inbox.

Usage:
  python main.py                  # Standard daily morning run (scrapes, summarizes, sends email)
  python main.py --mock           # Run end-to-end with mock data (no X login required)
  python main.py --preview        # Generate preview_newsletter.html without sending email
  python main.py --mock --preview # Generate instant preview using mock data
"""

import sys
import argparse
import logging
from datetime import datetime

from config.settings import (
    GEMINI_API_KEY,
    RECIPIENT_EMAIL,
    SMTP_USER,
    SMTP_PASS,
    EMAIL_PROVIDER,
    RESEND_API_KEY,
    NEWSLETTER_PREVIEW_PATH,
)
from extractor.session import is_session_available
from extractor.scraper import XFeedScraper, generate_mock_tweets
from processor.filter import filter_tech_tweets
from processor.summarizer import create_digest_with_gemini, create_fallback_digest
from mailer.renderer import NewsletterRenderer
from mailer.sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("x-tech-digest")


def run(use_mock: bool = False, preview_only: bool = False):
    print("=" * 65)
    print("           ⚡ X (Twitter) Daily Tech Digest ⚡           ")
    print("=" * 65)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'MOCK DATA' if use_mock else 'LIVE X SCRAPER'}")
    print(f"Email Dispatch: {'DISABLED (Preview Only)' if preview_only else 'ENABLED'}\n")

    # 1. Extraction Phase
    raw_tweets = []
    if use_mock:
        logger.info("Using realistic mock tech tweets for dry run...")
        raw_tweets = generate_mock_tweets()
    else:
        if not is_session_available():
            logger.error(
                "❌ No active X session found!\n"
                "Please run: python setup_auth.py to log into your X account once,\n"
                "or test the pipeline now using: python main.py --mock --preview"
            )
            sys.exit(1)

        scraper = XFeedScraper()
        raw_tweets = scraper.scrape_timeline()

    total_scanned = len(raw_tweets)
    logger.info(f"Step 1 Complete: Ingested {total_scanned} total posts.")

    # 2. Tech Filtering Phase
    tech_tweets = filter_tech_tweets(raw_tweets, min_score=0.35)
    logger.info(f"Step 2 Complete: Filtered down to {len(tech_tweets)} tech-relevant posts.")

    if not tech_tweets:
        logger.warning("No technical content detected in feed. Exiting gracefully without sending email.")
        return

    # 3. AI Summarization Phase
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        logger.info("Step 3: Generating AI digest using Google Gemini (Free Tier)...")
        digest = create_digest_with_gemini(tech_tweets, total_scanned)
    else:
        logger.warning(
            "⚠️ GEMINI_API_KEY not configured in .env. Using fallback structured digest.\n"
            "To enable intelligent AI summaries, get a free key at https://aistudio.google.com/"
        )
        digest = create_fallback_digest(tech_tweets, total_scanned)

    # 4. Rendering Phase
    logger.info("Step 4: Rendering HTML newsletter...")
    renderer = NewsletterRenderer()
    html_body = renderer.render_html(digest)
    text_body = renderer.render_plain_text(digest)

    preview_file = renderer.save_preview(digest)
    logger.info(f"Newsletter preview saved to: {preview_file}")

    if preview_only:
        print("\n" + "=" * 65)
        print("✅ PREVIEW READY!")
        print(f"Open this file in your browser to view your newsletter:")
        print(f"👉 file:///{str(preview_file).replace('\\', '/')}")
        print("=" * 65)
        return

    # 5. Dispatch Phase
    logger.info("Step 5: Sending morning email...")
    sender = EmailSender()
    try:
        sender.send_digest(
            subject=f"Tech Radar • {digest.date_str}",
            html_content=html_body,
            text_content=text_body
        )
        print("\n" + "=" * 65)
        print("✅ SUCCESS: Morning Tech Digest delivered to your email!")
        print(f"Recipient: {RECIPIENT_EMAIL}")
        print("=" * 65)
    except Exception as e:
        logger.error(f"❌ Failed to deliver email: {e}")
        print("\nTIP: You can review your generated HTML digest at:")
        print(f"file:///{str(preview_file).replace('\\', '/')}")


def main():
    parser = argparse.ArgumentParser(description="X Daily Morning Tech Digest")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run with sample tech tweets instead of scraping X"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Generate and save HTML newsletter preview without sending email"
    )
    args = parser.parse_args()

    run(use_mock=args.mock, preview_only=args.preview)


if __name__ == "__main__":
    main()
