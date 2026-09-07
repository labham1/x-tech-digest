from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class Tweet(BaseModel):
    """Represents a single extracted tweet from the feed."""
    id: str
    url: str
    author_name: str
    author_handle: str
    text: str
    timestamp: Optional[str] = None
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: Optional[str] = None
    outbound_urls: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0


class DigestLink(BaseModel):
    """External link extracted from or referenced by the tweet."""
    label: str
    url: str


class DigestItem(BaseModel):
    """A curated tech insight ready for the newsletter."""
    headline: str
    summary_bullets: List[str] = Field(default_factory=list)
    why_it_matters: str
    author_handle: str
    tweet_url: str
    links: List[DigestLink] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class DigestCategory(BaseModel):
    """A category grouping in the daily newsletter."""
    category_name: str
    emoji: str
    description: str
    items: List[DigestItem] = Field(default_factory=list)


class DailyDigest(BaseModel):
    """The complete newsletter payload for the day."""
    date_str: str = Field(default_factory=lambda: datetime.now().strftime("%A, %B %d, %Y"))
    greeting: str = "Here is your morning briefing of the top tech developments, tools, and discussions from your X feed."
    total_scanned: int = 0
    total_tech_selected: int = 0
    categories: List[DigestCategory] = Field(default_factory=list)
