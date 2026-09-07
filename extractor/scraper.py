import re
import time
import random
import logging
from typing import List, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from config.settings import (
    SESSION_FILE,
    X_FEED_URL,
    MAX_TWEETS_TO_SCAN,
    SCROLL_COUNT,
    HEADLESS,
)
from extractor.session import is_session_available
from models import Tweet

logger = logging.getLogger(__name__)


def parse_metric(text: Optional[str]) -> int:
    """Parses metric strings like '1.2K', '450', '2M' into integer counts."""
    if not text:
        return 0
    clean = text.strip().upper().replace(",", "")
    try:
        if "K" in clean:
            return int(float(clean.replace("K", "")) * 1000)
        elif "M" in clean:
            return int(float(clean.replace("M", "")) * 1000000)
        return int(re.sub(r"[^\d]", "", clean) or 0)
    except Exception:
        return 0


class XFeedScraper:
    """Extracts posts from the user's X timeline using Playwright and saved session cookies."""

    def __init__(self, session_path=SESSION_FILE, feed_url=X_FEED_URL):
        self.session_path = session_path
        self.feed_url = feed_url

    def scrape_timeline(self, max_tweets: int = MAX_TWEETS_TO_SCAN) -> List[Tweet]:
        """Scrapes the user's feed headlessly and returns extracted Tweet objects."""
        if not is_session_available(self.session_path):
            raise FileNotFoundError(
                f"No active X session found at {self.session_path}. "
                "Please run 'python setup_auth.py' first to log in once."
            )

        logger.info(f"Starting headless feed scrape from {self.feed_url}...")
        tweets_by_id = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=HEADLESS,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            context = browser.new_context(
                storage_state=str(self.session_path),
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                page.goto(self.feed_url, timeout=45000, wait_until="domcontentloaded")
                time.sleep(3)  # Allow initial feed hydration

                # Check if we were redirected to login
                if "login" in page.url or "i/flow/login" in page.url:
                    raise PermissionError("Session expired or invalid. Please re-run 'python setup_auth.py'.")

                # Wait for tweet articles
                try:
                    page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)
                except PlaywrightTimeoutError:
                    logger.warning("Timeout waiting for tweet selector. Taking snapshot...")

                # Scroll loop
                for scroll_i in range(SCROLL_COUNT):
                    articles = page.query_selector_all('article[data-testid="tweet"]')
                    logger.info(f"Scroll {scroll_i + 1}/{SCROLL_COUNT}: found {len(articles)} rendered articles")

                    for article in articles:
                        try:
                            tweet_data = self._extract_article_data(article)
                            if tweet_data and tweet_data.id not in tweets_by_id:
                                tweets_by_id[tweet_data.id] = tweet_data
                        except Exception as e:
                            logger.debug(f"Error extracting tweet: {e}")

                        if len(tweets_by_id) >= max_tweets:
                            break

                    if len(tweets_by_id) >= max_tweets:
                        break

                    # Scroll down naturally
                    page.mouse.wheel(0, random.randint(800, 1200))
                    time.sleep(random.uniform(1.5, 2.8))

            finally:
                browser.close()

        extracted_list = list(tweets_by_id.values())
        logger.info(f"Successfully extracted {len(extracted_list)} unique tweets from feed.")
        return extracted_list

    def _extract_article_data(self, article) -> Optional[Tweet]:
        """Extracts text, author, links, and engagement from an individual tweet DOM node."""
        # Find status link to get tweet ID and URL
        status_links = article.query_selector_all('a[href*="/status/"]')
        tweet_url = ""
        tweet_id = ""
        timestamp_str = None

        for link in status_links:
            href = link.get_attribute("href") or ""
            match = re.search(r"/([^/]+)/status/(\d+)", href)
            if match:
                tweet_id = match.group(2)
                tweet_url = f"https://x.com{match.group(0)}"
                time_el = link.query_selector("time")
                if time_el:
                    timestamp_str = time_el.get_attribute("datetime")
                break

        if not tweet_id:
            return None

        # Author details
        author_name = ""
        author_handle = ""
        user_name_el = article.query_selector('div[data-testid="User-Name"]')
        if user_name_el:
            name_text = user_name_el.inner_text()
            lines = [l.strip() for l in name_text.split("\n") if l.strip()]
            if len(lines) >= 1:
                author_name = lines[0]
            for l in lines:
                if l.startswith("@"):
                    author_handle = l
                    break

        # Tweet text
        tweet_text_el = article.query_selector('div[data-testid="tweetText"]')
        tweet_text = tweet_text_el.inner_text().strip() if tweet_text_el else ""

        if not tweet_text:
            return None

        # Outbound external links
        outbound_urls = []
        if tweet_text_el:
            link_elements = tweet_text_el.query_selector_all("a[href]")
            for a in link_elements:
                href = a.get_attribute("href") or ""
                # Avoid internal hashtag / mention links
                if href and not href.startswith("/") and "hashtag" not in href:
                    outbound_urls.append(href)

        # Engagement metrics
        likes = 0
        retweets = 0
        replies = 0

        like_el = article.query_selector('div[data-testid="like"]')
        if like_el:
            likes = parse_metric(like_el.inner_text())

        retweet_el = article.query_selector('div[data-testid="retweet"]')
        if retweet_el:
            retweets = parse_metric(retweet_el.inner_text())

        reply_el = article.query_selector('div[data-testid="reply"]')
        if reply_el:
            replies = parse_metric(reply_el.inner_text())

        return Tweet(
            id=tweet_id,
            url=tweet_url,
            author_name=author_name or "Tech Creator",
            author_handle=author_handle or "@unknown",
            text=tweet_text,
            timestamp=timestamp_str,
            likes=likes,
            retweets=retweets,
            replies=replies,
            outbound_urls=outbound_urls,
        )


def generate_mock_tweets() -> List[Tweet]:
    """Generates realistic sample tech tweets for testing and dry-runs."""
    return [
        Tweet(
            id="179001",
            url="https://x.com/karpathy/status/179001",
            author_name="Andrej Karpathy",
            author_handle="@karpathy",
            text="Large language models are rapidly becoming the kernel of a new computing architecture. Just released an educational walkthrough building a mini-transformer from scratch with FP8 quantization and KV-cache optimizations. GitHub: https://github.com/karpathy/llm.c",
            likes=14500,
            retweets=2800,
            replies=420,
            outbound_urls=["https://github.com/karpathy/llm.c"]
        ),
        Tweet(
            id="179002",
            url="https://x.com/swyx/status/179002",
            author_name="swyx",
            author_handle="@swyx",
            text="The rise of compound AI systems: Why single-prompt LLMs are losing to multi-agent architectures that orchestrate tools, memory retrieval, and self-correction loops. Full breakdown in today's essay: https://latentspace.pod/compound-ai",
            likes=3200,
            retweets=450,
            replies=89,
            outbound_urls=["https://latentspace.pod/compound-ai"]
        ),
        Tweet(
            id="179003",
            url="https://x.com/mitabor/status/179003",
            author_name="Mitchell Hashimoto",
            author_handle="@mitchellh",
            text="Ghostty terminal 1.0 update: Native GPU acceleration via Metal and OpenGL has slashed input latency down to sub-5ms across macOS and Linux. Memory footprint is under 40MB. Architecture doc: https://ghostty.org/docs/features",
            likes=6100,
            retweets=780,
            replies=140,
            outbound_urls=["https://ghostty.org/docs/features"]
        ),
        Tweet(
            id="179004",
            url="https://x.com/random_user/status/179004",
            author_name="Coffee & Chill",
            author_handle="@coffee_chill",
            text="Nothing beats a fresh cup of espresso on a rainy Monday morning! What is everyone having for breakfast today? ☕🥞",
            likes=45,
            retweets=2,
            replies=12,
            outbound_urls=[]
        ),
        Tweet(
            id="179005",
            url="https://x.com/shadcn/status/179005",
            author_name="shadcn",
            author_handle="@shadcn",
            text="New UI components added to registry: Interactive command palettes, animated data tables with virtualized scrolling, and theme-toggle presets built on Tailwind v4 and React 19.",
            likes=8900,
            retweets=1100,
            replies=190,
            outbound_urls=["https://ui.shadcn.com"]
        ),
        Tweet(
            id="179006",
            url="https://x.com/fastai/status/179006",
            author_name="Jeremy Howard",
            author_handle="@jeremyphoward",
            text="Excited to publish our new benchmark on small language models (SLMs) fine-tuned on synthetic domain-specific corpora. A 3B parameter model matched a 70B general model on code synthesis tasks. Paper: https://arxiv.org/abs/2405.01234",
            likes=4200,
            retweets=670,
            replies=95,
            outbound_urls=["https://arxiv.org/abs/2405.01234"]
        ),
    ]
