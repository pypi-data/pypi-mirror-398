"""
Pistis Sophia Daily Wisdom

Provides inspirational quotes from the Gnostic text "Pistis Sophia"
based on current project status. Quotes are selected to match the
project's journey from chaos to enlightenment.

To disable: Set EXARP_DISABLE_WISDOM=1 in environment or create
.exarp_no_wisdom file in project root.
"""

import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Quotes organized by project "Aeon" (health level)
PISTIS_SOPHIA_QUOTES = {
    # Chaos (0-30% health) - Sophia's fall and despair
    "chaos": [
        {
            "quote": "I am become as a demon apart, who dwelleth in matter and in whom is no light.",
            "chapter": "Chapter 32",
            "context": "When the project feels overwhelming",
            "encouragement": "Even in darkness, the path to Light exists."
        },
        {
            "quote": "I looked to the height to the Light in which I had trusted, and they gave me over to the chaos.",
            "chapter": "Chapter 33",
            "context": "When things aren't going as planned",
            "encouragement": "Trust the process. Sophia ascended through 13 repentances."
        },
        {
            "quote": "Save me out of the chaos and the darkness.",
            "chapter": "Chapter 36",
            "context": "When you need to start fresh",
            "encouragement": "Every cleanup sprint is a step toward the Light."
        },
    ],

    # Lower Aeons (31-50% health) - Beginning the ascent
    "lower_aeons": [
        {
            "quote": "I have turned to the Light, and it hath known my affliction.",
            "chapter": "Chapter 39",
            "context": "When you've identified the problems",
            "encouragement": "Recognition is the first step to resolution."
        },
        {
            "quote": "Let not the chaos submerge me, and let not the deep swallow me.",
            "chapter": "Chapter 40",
            "context": "When maintaining momentum is hard",
            "encouragement": "Keep iterating. Small wins compound."
        },
        {
            "quote": "I cried unto thee, O Light of lights, in my affliction and thou didst hearken unto me.",
            "chapter": "Chapter 41",
            "context": "When tests finally pass",
            "encouragement": "Your work is being recognized."
        },
    ],

    # Middle Aeons (51-70% health) - Steady progress
    "middle_aeons": [
        {
            "quote": "The Light hath become my salvation.",
            "chapter": "Chapter 50",
            "context": "When the project is stabilizing",
            "encouragement": "You're past the hardest part."
        },
        {
            "quote": "I will sing praises unto the Light, for it hath sent me its light from the height.",
            "chapter": "Chapter 53",
            "context": "When documentation is complete",
            "encouragement": "Celebrate your progress."
        },
        {
            "quote": "The Light hath heard me and saved me from all my afflictions.",
            "chapter": "Chapter 55",
            "context": "When blockers are resolved",
            "encouragement": "Clear skies ahead."
        },
    ],

    # Upper Aeons (71-85% health) - Approaching enlightenment
    "upper_aeons": [
        {
            "quote": "I will praise the name of the Light, and I will sing unto it in hymns.",
            "chapter": "Chapter 58",
            "context": "When the project is healthy",
            "encouragement": "Your diligence is paying off."
        },
        {
            "quote": "The Light hath power in its mystery.",
            "chapter": "Chapter 60",
            "context": "When architecture is solid",
            "encouragement": "Good foundations enable great things."
        },
        {
            "quote": "I have become as a man who is freed.",
            "chapter": "Chapter 62",
            "context": "When technical debt is low",
            "encouragement": "Freedom to build, not just maintain."
        },
    ],

    # Treasury of Light (86-100% health) - Enlightenment achieved
    "treasury": [
        {
            "quote": "Sophia is raised to her original place in the Thirteenth Aeon.",
            "chapter": "Chapter 64",
            "context": "When production-ready",
            "encouragement": "You've reached enlightenment. Maintain the Light."
        },
        {
            "quote": "The mystery of the ineffable is completed.",
            "chapter": "Chapter 136",
            "context": "When all goals are met",
            "encouragement": "The journey continues. New mysteries await."
        },
        {
            "quote": "Enter into the Light and become Light.",
            "chapter": "Chapter 140",
            "context": "When sharing your work with others",
            "encouragement": "Your Light illuminates the path for others."
        },
    ],
}


def get_aeon_level(health_score: float) -> str:
    """Determine which Aeon the project is in based on health score."""
    if health_score <= 30:
        return "chaos"
    elif health_score <= 50:
        return "lower_aeons"
    elif health_score <= 70:
        return "middle_aeons"
    elif health_score <= 85:
        return "upper_aeons"
    else:
        return "treasury"


def get_aeon_number(health_score: float) -> int:
    """Convert health score to approximate Aeon number (1-13 + Treasury)."""
    if health_score <= 30:
        return 0  # Chaos
    elif health_score >= 95:
        return 14  # Treasury of Light
    else:
        # Map 31-94 to Aeons 1-13
        return int((health_score - 30) / 5) + 1


def is_wisdom_disabled() -> bool:
    """Check if user has disabled daily wisdom."""
    # Check environment variable
    if os.environ.get('EXARP_DISABLE_WISDOM', '').lower() in ('1', 'true', 'yes'):
        return True

    # Check for disable file in project root
    project_root = Path(__file__).resolve().parents[2]
    if (project_root / '.exarp_no_wisdom').exists():
        return True

    return False


def check_first_run_and_prompt() -> Optional[str]:
    """
    Check if this is the first time showing wisdom and return a friendly prompt.
    Creates a marker file after first run.

    Returns:
        First-run message if applicable, None otherwise.
    """
    project_root = Path(__file__).resolve().parents[2]
    marker_file = project_root / '.exarp_wisdom_seen'

    if marker_file.exists():
        return None

    # Create marker
    try:
        marker_file.write_text(f"First seen: {datetime.now().isoformat()}\n")
    except OSError:
        pass  # Don't fail if can't write

    return """
┌──────────────────────────────────────────────────────────────────────┐
│  ✨ NEW FEATURE: Pistis Sophia Daily Wisdom                          │
├──────────────────────────────────────────────────────────────────────┤
│  Exarp now includes inspirational quotes from the Gnostic text       │
│  "Pistis Sophia" matched to your project's health status.            │
│                                                                      │
│  Like Sophia's journey from Chaos to the Treasury of Light,          │
│  your project ascends through the Aeons as it improves!              │
│                                                                      │
│  📖 To learn more: https://en.wikipedia.org/wiki/Pistis_Sophia       │
│                                                                      │
│  Would you like to disable this feature?                             │
│    • export EXARP_DISABLE_WISDOM=1                                   │
│    • touch .exarp_no_wisdom                                          │
└──────────────────────────────────────────────────────────────────────┘
"""


def get_daily_wisdom(health_score: float, seed_date: bool = True) -> Optional[dict[str, Any]]:
    """
    Get a Pistis Sophia quote based on project health.

    Args:
        health_score: Project health score (0-100)
        seed_date: If True, same quote shown all day. If False, random each time.

    Returns:
        Dictionary with quote, chapter, context, encouragement, and aeon info.
        Returns None if wisdom is disabled.
    """
    if is_wisdom_disabled():
        return None

    aeon_level = get_aeon_level(health_score)
    aeon_number = get_aeon_number(health_score)
    quotes = PISTIS_SOPHIA_QUOTES[aeon_level]

    # Use date as seed for consistent daily quote
    if seed_date:
        today = datetime.now().strftime("%Y%m%d")
        random.seed(int(today) + int(health_score))

    quote = random.choice(quotes)

    # Reset random seed
    random.seed()

    return {
        "quote": quote["quote"],
        "chapter": quote["chapter"],
        "context": quote["context"],
        "encouragement": quote["encouragement"],
        "aeon_level": aeon_level.replace("_", " ").title(),
        "aeon_number": aeon_number,
        "health_score": health_score,
        "source": "Pistis Sophia (Gnostic Text, ~3rd Century CE)",
    }


def format_wisdom_ascii(wisdom: dict[str, Any]) -> str:
    """Format wisdom as ASCII art for terminal display."""
    if wisdom is None:
        return ""

    aeon_display = f"Aeon {wisdom['aeon_number']}" if wisdom['aeon_number'] > 0 else "Chaos"
    if wisdom['aeon_number'] == 14:
        aeon_display = "Treasury of Light"

    return f"""
╔══════════════════════════════════════════════════════════════════════╗
║  📜 PISTIS SOPHIA DAILY WISDOM                                       ║
║  Project Status: {wisdom['aeon_level']:<20} ({aeon_display})         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  "{wisdom['quote'][:64]}"
║  {wisdom['quote'][64:] if len(wisdom['quote']) > 64 else ''}
║                                                                      ║
║  — {wisdom['chapter']:<60} ║
║                                                                      ║
║  💡 {wisdom['encouragement']:<62} ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  To disable: export EXARP_DISABLE_WISDOM=1                           ║
║              or create .exarp_no_wisdom file in project root         ║
╚══════════════════════════════════════════════════════════════════════╝
"""


def format_wisdom_markdown(wisdom: dict[str, Any]) -> str:
    """Format wisdom as Markdown."""
    if wisdom is None:
        return ""

    aeon_display = f"Aeon {wisdom['aeon_number']}" if wisdom['aeon_number'] > 0 else "Chaos"
    if wisdom['aeon_number'] == 14:
        aeon_display = "Treasury of Light ✨"

    return f"""
---

### 📜 Pistis Sophia Daily Wisdom

**Project Status:** {wisdom['aeon_level']} ({aeon_display})

> *"{wisdom['quote']}"*
>
> — {wisdom['chapter']}

💡 **{wisdom['encouragement']}**

<details>
<summary>ℹ️ About this quote</summary>

- **Context:** {wisdom['context']}
- **Source:** {wisdom['source']}
- **Health Score:** {wisdom['health_score']:.1f}%

To disable daily wisdom: `export EXARP_DISABLE_WISDOM=1` or create `.exarp_no_wisdom` file.

</details>

---
"""


# CLI support
if __name__ == "__main__":
    import sys

    # Get health score from argument or use default
    health = float(sys.argv[1]) if len(sys.argv) > 1 else 75.0

    wisdom = get_daily_wisdom(health)
    if wisdom:
        print(format_wisdom_ascii(wisdom))
    else:
        print("Daily wisdom is disabled.")

