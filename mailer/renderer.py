from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from models import DailyDigest
from config.settings import NEWSLETTER_PREVIEW_PATH

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


class NewsletterRenderer:
    """Renders DailyDigest models into responsive HTML and plain-text email bodies."""

    def __init__(self, templates_dir: Path = TEMPLATES_DIR):
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True
        )
        self.template = self.env.get_template("newsletter.html")

    def render_html(self, digest: DailyDigest) -> str:
        """Renders the HTML email body."""
        return self.template.render(digest=digest)

    def render_plain_text(self, digest: DailyDigest) -> str:
        """Generates a plain-text version for email clients without HTML support."""
        lines = [
            f"=== 𝕏 TECH RADAR - {digest.date_str} ===",
            digest.greeting,
            f"({digest.total_scanned} scanned | {digest.total_tech_selected} highlights)",
            ""
        ]

        for cat in digest.categories:
            lines.append(f"\n[{cat.emoji} {cat.category_name.upper()}]")
            for item in cat.items:
                lines.append(f"\n* {item.headline} (by {item.author_handle})")
                for bullet in item.summary_bullets:
                    lines.append(f"  - {bullet}")
                if item.why_it_matters:
                    lines.append(f"  Why it matters: {item.why_it_matters}")
                lines.append(f"  Link: {item.tweet_url}")
                for l in item.links:
                    lines.append(f"  Resource: {l.label} ({l.url})")

        lines.append("\n---\nSent by X Tech Digest (Automated)")
        return "\n".join(lines)

    def save_preview(self, digest: DailyDigest, output_path: Path = NEWSLETTER_PREVIEW_PATH) -> Path:
        """Saves rendered HTML to disk for browser inspection."""
        html = self.render_html(digest)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path
