"""
Wisdom System - Daily inspirational quotes based on project health.

A multi-source wisdom engine that provides quotes matched to project status,
designed for extraction to standalone package when needed.

Available Sources (21 total, including Hebrew):
- random: Randomly pick from any source (daily consistent) 🎲
- pistis_sophia: Gnostic mysticism (default)
- pirkei_avot, proverbs, ecclesiastes, psalms: Jewish texts via Sefaria.org 🕎
- bofh: Bastard Operator From Hell (tech humor)
- tao: Tao Te Ching (balance, flow)
- art_of_war: Sun Tzu (strategy)
- stoic: Marcus Aurelius, Epictetus, Seneca (resilience)
- bible: Proverbs & Ecclesiastes KJV (wisdom)
- tao_of_programming: Tech philosophy
- murphy: Murphy's Laws (pragmatism)
- shakespeare: The Bard (drama)
- confucius: The Analects (ethics)
- kybalion: Hermetic Philosophy (mental models) ⚗️
- gracian: Art of Worldly Wisdom (pragmatic maxims) 🎭
- enochian: John Dee's mystical calls 🔮

Hebrew Advisors (עברית):
- rebbe: The Rebbe - Chassidic wisdom from Pirkei Avot 🕎
- tzaddik: The Tzaddik - Path of righteousness from Proverbs ✡️
- chacham: The Chacham - Sage wisdom from Torah 📜

Credits:
- Many texts from https://sacred-texts.com/ (public domain)
- Hebrew texts from https://sefaria.org/ (open API)

Usage:
    from project_management_automation.tools.wisdom import get_wisdom, list_sources

    wisdom = get_wisdom(health_score=75.0, source="stoic")
    wisdom = get_wisdom(health_score=75.0, source="random")  # Different source each day!
    wisdom = get_wisdom(health_score=75.0, source="rebbe")   # Hebrew advisor
    wisdom = get_wisdom(health_score=75.0, source="pirkei_avot", include_hebrew=True)  # Bilingual
    sources = list_sources()

Configuration:
    EXARP_WISDOM_SOURCE=random          # Random source each day
    EXARP_WISDOM_SOURCE=<source>        # Specific source (default: pistis_sophia)
    EXARP_WISDOM_SOURCE=rebbe           # Hebrew advisor
    EXARP_WISDOM_HEBREW=1               # Enable bilingual Hebrew/English output
    EXARP_WISDOM_HEBREW_ONLY=1          # Hebrew text only (no English)
    EXARP_DISABLE_WISDOM=1              # Disable completely
    .exarp_no_wisdom                    # File marker to disable

Design Note:
    This package is designed for easy extraction to standalone `devwisdom`
    package. The public API (get_wisdom, list_sources, format_text) is stable.
    See docs/DESIGN_DECISIONS.md for extraction criteria.
"""

# Public API - stable for extraction
from .sources import (
    WISDOM_SOURCES,
    get_aeon_level,
    get_random_source,
    get_wisdom,
    list_hebrew_sources,  # NEW: Hebrew-specific source listing
    load_config,
    save_config,
)
from .sources import (
    format_wisdom_text as format_text,
)
from .sources import (
    list_available_sources as list_sources,
)

# Sefaria integration (optional, graceful degradation)
try:
    from .sefaria import (
        SEFARIA_SELECTIONS,
        fetch_sefaria_text,
        format_sefaria_wisdom,
        get_sefaria_wisdom,
    )
    SEFARIA_AVAILABLE = True
except ImportError:
    SEFARIA_AVAILABLE = False
    get_sefaria_wisdom = None
    fetch_sefaria_text = None

# Pistis Sophia (original source)
try:
    from .pistis_sophia import (
        PISTIS_SOPHIA_QUOTES,
    )
    from .pistis_sophia import (
        format_wisdom_ascii as format_pistis_sophia_ascii,
    )
    from .pistis_sophia import (
        format_wisdom_markdown as format_pistis_sophia_markdown,
    )
    from .pistis_sophia import (
        get_daily_wisdom as get_pistis_sophia_wisdom,
    )
    PISTIS_SOPHIA_AVAILABLE = True
except ImportError:
    PISTIS_SOPHIA_AVAILABLE = False
    get_pistis_sophia_wisdom = None

# Trusted Advisor System
from .advisors import (
    METRIC_ADVISORS,
    SCORE_CONSULTATION_FREQUENCY,
    STAGE_ADVISORS,
    TOOL_ADVISORS,
    consult_advisor,
    export_for_podcast,
    format_consultation,
    get_advisor_for_metric,
    get_advisor_for_stage,
    get_advisor_for_tool,
    get_consultation_log,
    get_consultation_mode,
    get_daily_briefing,
)

# Voice/TTS System removed - migrated to devwisdom-go MCP server
VOICE_AVAILABLE = False
ADVISOR_VOICES = {}
HEBREW_VOICES = {}

__all__ = [
    # Core API (stable)
    "get_wisdom",
    "list_sources",
    "list_hebrew_sources",  # Hebrew-specific listing
    "format_text",
    "load_config",
    "save_config",
    "get_aeon_level",

    # Data
    "WISDOM_SOURCES",

    # Feature flags
    "SEFARIA_AVAILABLE",
    "PISTIS_SOPHIA_AVAILABLE",
    "VOICE_AVAILABLE",

    # Trusted Advisor System
    "METRIC_ADVISORS",
    "TOOL_ADVISORS",
    "STAGE_ADVISORS",
    "SCORE_CONSULTATION_FREQUENCY",
    "get_advisor_for_metric",
    "get_advisor_for_tool",
    "get_advisor_for_stage",
    "get_consultation_mode",
    "consult_advisor",
    "format_consultation",
    "get_daily_briefing",
    "get_consultation_log",
    "export_for_podcast",

    # Voice/TTS System removed - migrated to devwisdom-go MCP server
]

# INTENTIONAL: Wisdom module has its own version, separate from Exarp.
# This subpackage is designed for extraction to standalone `devwisdom` package.
# When extracted, it will have independent versioning on PyPI.
# See: docs/DESIGN_DECISIONS.md#wisdom-system-versioning
__version__ = "1.0.0"
__author__ = "Exarp Project"

