import json
import logging
from typing import List
from datetime import datetime

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from models import Tweet, DailyDigest, DigestCategory, DigestItem, DigestLink

logger = logging.getLogger(__name__)


def create_digest_with_gemini(tweets: List[Tweet], total_scanned: int) -> DailyDigest:
    """Uses Google Gemini API (free tier) to curate, summarize, and categorize tech tweets."""
    if not tweets:
        return DailyDigest(
            total_scanned=total_scanned,
            total_tech_selected=0,
            categories=[]
        )

    # Format tweets for the prompt
    tweets_payload = []
    for idx, t in enumerate(tweets[:25]):  # Process top 25 high-scoring tech tweets
        tweets_payload.append({
            "index": idx + 1,
            "author": f"{t.author_name} ({t.author_handle})",
            "url": t.url,
            "text": t.text,
            "likes": t.likes,
            "retweets": t.retweets,
            "links": t.outbound_urls
        })

    prompt = f"""
You are an expert technology editor creating a daily morning newsletter for a software engineer and AI practitioner.
Below is a list of tech-related tweets extracted from their personal X feed over the last 24 hours.

TASK:
1. Review the tweets and identify the most valuable, high-signal items.
2. Filter out trivial or repetitive takes.
3. Group the selected items into 2 to 4 logical categories, such as:
   - "🚀 Breakthroughs & AI News"
   - "🛠️ Developer Tools & Open Source Releases"
   - "💡 Architecture, Best Practices & Deep Dives"
   - "📈 Industry Trends & Engineering Perspectives"
4. For each selected item, write:
   - A clear, punchy headline (e.g. "Karpathy Releases llm.c with FP8 Quantization")
   - 2-3 concise summary bullet points (TL;DR) explaining what was announced or explained
   - A 1-sentence "Why it matters" statement
   - Author handle and original tweet URL
   - External links mentioned (e.g. GitHub repos, arXiv papers, project docs)
   - 2-3 tech tags (e.g. ["AI", "LLM", "C++"])

INPUT TWEETS (JSON):
{json.dumps(tweets_payload, indent=2)}

OUTPUT REQUIREMENT:
Respond ONLY with a valid JSON object strictly matching this JSON schema:
{{
  "date_str": "Day, Month DD, YYYY",
  "greeting": "Morning greeting summarizing today's tech pulse in 1 sentence",
  "categories": [
    {{
      "category_name": "Category Name",
      "emoji": "🚀",
      "description": "Short 1-sentence summary of this section",
      "items": [
        {{
          "headline": "...",
          "summary_bullets": ["bullet 1", "bullet 2"],
          "why_it_matters": "...",
          "author_handle": "@handle",
          "tweet_url": "https://x.com/...",
          "links": [
            {{"label": "GitHub Repo", "url": "https://..."}}
          ],
          "tags": ["Tag1", "Tag2"]
        }}
      ]
    }}
  ]
}}
Do NOT wrap the response in markdown code blocks like ```json ... ```, just pure JSON text.
"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )

        response_text = response.text.strip()
        # Clean potential markdown formatting if returned
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        data = json.loads(response_text.strip())

        categories = []
        total_items = 0
        for cat in data.get("categories", []):
            items = []
            for it in cat.get("items", []):
                links = [DigestLink(label=l.get("label", "Link"), url=l.get("url", "#")) for l in it.get("links", [])]
                items.append(DigestItem(
                    headline=it.get("headline", "Tech Update"),
                    summary_bullets=it.get("summary_bullets", []),
                    why_it_matters=it.get("why_it_matters", ""),
                    author_handle=it.get("author_handle", "@unknown"),
                    tweet_url=it.get("tweet_url", "#"),
                    links=links,
                    tags=it.get("tags", [])
                ))
            total_items += len(items)
            categories.append(DigestCategory(
                category_name=cat.get("category_name", "Tech Highlights"),
                emoji=cat.get("emoji", "⚡"),
                description=cat.get("description", ""),
                items=items
            ))

        return DailyDigest(
            date_str=data.get("date_str", datetime.now().strftime("%A, %B %d, %Y")),
            greeting=data.get("greeting", "Here is your morning technology briefing."),
            total_scanned=total_scanned,
            total_tech_selected=total_items,
            categories=categories
        )

    except Exception as e:
        logger.error(f"Gemini API summarization failed: {e}. Falling back to rule-based digest.")
        return create_fallback_digest(tweets, total_scanned)


def create_fallback_digest(tweets: List[Tweet], total_scanned: int) -> DailyDigest:
    """Constructs a clean structured digest without LLM if API key is not yet configured."""
    items = []
    for t in tweets[:8]:
        links = [DigestLink(label="Resource Link", url=u) for u in t.outbound_urls]
        bullets = [t.text[:140] + ("..." if len(t.text) > 140 else "")]
        items.append(DigestItem(
            headline=f"Update from {t.author_name}",
            summary_bullets=bullets,
            why_it_matters=f"Gained {t.likes} likes and {t.retweets} retweets among tech community.",
            author_handle=t.author_handle,
            tweet_url=t.url,
            links=links,
            tags=["Trending", "Tech"]
        ))

    cat = DigestCategory(
        category_name="Top Tech Feed Highlights",
        emoji="⚡",
        description="Top high-engagement tech posts detected from your timeline.",
        items=items
    )

    return DailyDigest(
        date_str=datetime.now().strftime("%A, %B %d, %Y"),
        greeting="Here is your automated morning digest of top tech posts from your X feed.",
        total_scanned=total_scanned,
        total_tech_selected=len(items),
        categories=[cat]
    )
