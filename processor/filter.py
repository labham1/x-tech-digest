import re
import logging
from typing import List
from models import Tweet

logger = logging.getLogger(__name__)

# High-confidence technical keywords
TECH_KEYWORDS = {
    # AI / ML
    "ai", "llm", "gpt", "gemini", "claude", "transformer", "diffusion", "rag",
    "agent", "agents", "weights", "fine-tuning", "quantization", "embedding",
    "pytorch", "huggingface", "cuda", "gpu", "inference", "deep learning",
    "machine learning", "neural", "arxiv", "prompt engineering",

    # Software Engineering & Languages
    "python", "rust", "typescript", "javascript", "golang", "c++", "zig",
    "react", "nextjs", "vue", "svelte", "tailwind", "node", "compiler",
    "algorithm", "backend", "frontend", "fullstack", "architecture", "refactor",
    "api", "graphql", "rest", "grpc", "microservices",

    # Infrastructure, Cloud & DevOps
    "docker", "kubernetes", "k8s", "linux", "aws", "gcp", "azure", "serverless",
    "database", "postgres", "sqlite", "redis", "mongodb", "sql", "vector db",
    "ci/cd", "git", "github", "open source", "terminal", "bash",

    # Hardware & Systems
    "apple silicon", "nvidia", "cpu", "chip", "semiconductor", "arm64", "kernel"
}

# Non-tech / spam indicators
NOISE_KEYWORDS = {
    "airdrop", "giveaway", "free crypto", "dm to buy", "follow for follow",
    "horoscope", "astrology", "dating", "casino", "slots", "lottery",
    "presale", "whitelist", "pump and dump", "retweet to win"
}


def evaluate_tweet_relevance(tweet: Tweet) -> float:
    """Evaluates a tweet and returns a tech relevance score between 0.0 and 1.0."""
    text_lower = tweet.text.lower()

    # Immediate disqualifiers
    for noise in NOISE_KEYWORDS:
        if noise in text_lower:
            return 0.0

    # Tokenize words cleanly
    words = set(re.findall(r"\b[a-z0-9#_/\-+\.]{2,}\b", text_lower))

    # Match tech keywords
    matched_tech = words.intersection(TECH_KEYWORDS)

    # Check for external tech links (github, arxiv, huggingface, etc.)
    has_tech_link = any(
        any(domain in url.lower() for domain in ["github.com", "arxiv.org", "huggingface.co", "dev.to", "subgraph", "latent"])
        for url in tweet.outbound_urls
    )

    if not matched_tech and not has_tech_link:
        return 0.1  # Low confidence

    # Base score by keyword matches
    score = min(0.4 + (len(matched_tech) * 0.15), 0.85)

    if has_tech_link:
        score = min(score + 0.2, 1.0)

    # Engagement bonus (viral tech discussions score higher)
    engagement = tweet.likes + (tweet.retweets * 2)
    if engagement > 500:
        score = min(score + 0.1, 1.0)

    return round(score, 2)


def filter_tech_tweets(tweets: List[Tweet], min_score: float = 0.4) -> List[Tweet]:
    """Filters a list of tweets, keeping only tech-relevant ones sorted by score and engagement."""
    scored_tweets = []
    for t in tweets:
        score = evaluate_tweet_relevance(t)
        t.relevance_score = score
        if score >= min_score:
            scored_tweets.append(t)

    # Sort descending by relevance score, then engagement
    scored_tweets.sort(key=lambda t: (t.relevance_score, t.likes + t.retweets * 2), reverse=True)
    logger.info(f"Pre-filter: Kept {len(scored_tweets)} tech tweets out of {len(tweets)} scanned.")
    return scored_tweets
