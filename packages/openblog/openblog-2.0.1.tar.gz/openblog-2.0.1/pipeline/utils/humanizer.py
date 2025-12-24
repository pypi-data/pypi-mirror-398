"""
Content Humanizer - Detects and replaces AI-typical phrases.

Makes AI-generated content sound more natural by replacing overused 
AI patterns with simpler, more direct language.
"""

import re
import logging
import random
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


# AI-typical phrases - ORDERED BY PRIORITY (most common first)
AI_PHRASE_REPLACEMENTS: List[Tuple[str, List[str]]] = [
    # TIER 1: Most common AI buzzwords (ALWAYS replace)
    ("seamlessly", ["smoothly", "easily", ""]),
    ("leverage", ["use", "apply"]),
    ("utilize", ["use", "apply"]),
    ("impactful", ["effective", "meaningful"]),
    ("drive growth", ["grow", "increase"]),
    ("robust", ["strong", "reliable"]),
    ("comprehensive", ["full", "complete"]),
    ("empower", ["help", "enable"]),
    ("empowers", ["helps", "enables"]),
    ("streamline", ["simplify", "speed up"]),
    ("streamlines", ["simplifies", "speeds up"]),
    ("cutting-edge", ["modern", "new"]),
    ("game-changer", ["major change", "breakthrough"]),
    ("holistic", ["complete", "full"]),
    ("actionable insights", ["clear steps", "useful data"]),
    ("actionable", ["practical", "useful"]),
    
    # TIER 2: Filler transitions
    ("furthermore", [". Also,", ""]),
    ("moreover", [". Plus,", ""]),
    ("additionally", [". Also,", ""]),
    ("consequently", [". So,", ""]),
    ("subsequently", [". Then,", ""]),
    ("nevertheless", [". Still,", ""]),
    
    # TIER 3: AI-typical sentence starters
    ("it's important to note that", [""]),
    ("it's worth noting that", [""]),
    ("it is important to note", [""]),
    ("it is worth noting", [""]),
    ("it should be noted that", [""]),
    ("in conclusion", [""]),
    ("to summarize", [""]),
    ("as mentioned earlier", [""]),
    ("as we discussed", [""]),
    ("as previously mentioned", [""]),
    ("in today's world", ["today"]),
    ("in today's landscape", ["today"]),
    ("in the realm of", ["in"]),
    ("navigate the landscape", ["handle"]),
    ("navigating the", ["handling"]),
    ("at the end of the day", ["ultimately"]),
    ("moving forward", ["next"]),
    ("going forward", ["next"]),
    ("that being said", [". However,"]),
    
    # TIER 4: Hyperbolic buzzwords
    ("state-of-the-art", ["modern", "advanced"]),
    ("game changing", ["major"]),
    ("revolutionary", ["new"]),
    ("groundbreaking", ["new", "notable"]),
    ("paradigm shift", ["shift", "change"]),
    ("transformative", ["significant"]),
    ("world-class", ["excellent"]),
    ("best-in-class", ["leading"]),
    ("next-generation", ["new", "modern"]),
    
    # TIER 5: More corporate speak
    ("leveraging", ["using"]),
    ("utilizing", ["using"]),
    ("synergy", ["teamwork"]),
    ("synergies", ["benefits"]),
    ("empowering", ["helping"]),
    ("streamlining", ["simplifying"]),
    ("drives growth", ["grows"]),
    ("unlock potential", ["improve"]),
    ("unlocking", ["enabling"]),
    ("harness the power", ["use"]),
    ("harnessing", ["using"]),
    ("optimize your", ["improve your"]),
    ("optimizing", ["improving"]),
    ("scalable", ["flexible"]),
    ("mission-critical", ["essential"]),
    ("value proposition", ["benefit"]),
    ("low-hanging fruit", ["easy wins"]),
    ("deep dive", ["analysis"]),
    ("circle back", ["return to"]),
    ("touch base", ["connect"]),
    
    # TIER 6: Wordy phrases
    ("in order to", ["to"]),
    ("due to the fact that", ["because"]),
    ("for the purpose of", ["for"]),
    ("in the event that", ["if"]),
    ("at this point in time", ["now"]),
    ("a large number of", ["many"]),
    ("a wide variety of", ["many"]),
    ("the vast majority of", ["most"]),
    ("on an ongoing basis", ["regularly"]),
    ("in close proximity to", ["near"]),
]

# Contractions for natural flow
CONTRACTION_REPLACEMENTS: List[Tuple[str, str]] = [
    ("it is", "it's"),
    ("you are", "you're"),
    ("we are", "we're"),
    ("do not", "don't"),
    ("does not", "doesn't"),
    ("will not", "won't"),
    ("cannot", "can't"),
    ("you will", "you'll"),
    ("we will", "we'll"),
    ("that is", "that's"),
    ("there is", "there's"),
    ("here is", "here's"),
    ("let us", "let's"),
]


class ContentHumanizer:
    """Humanizes AI-generated content."""
    
    def __init__(self, aggression_level: str = "moderate"):
        self.aggression_level = aggression_level
        self.replacements_made: List[Tuple[str, str]] = []
    
    def humanize(self, content: str) -> str:
        """Main humanization function."""
        self.replacements_made = []
        content = self._replace_ai_phrases(content)
        content = self._add_contractions(content)
        if self.replacements_made:
            logger.info(f"Humanized: replaced {len(self.replacements_made)} AI phrases")
        return content
    
    def _replace_ai_phrases(self, content: str) -> str:
        """Replace AI-typical phrases."""
        # Light: first 16, Moderate: first 50, Aggressive: all
        if self.aggression_level == "light":
            patterns = AI_PHRASE_REPLACEMENTS[:16]
        elif self.aggression_level == "moderate":
            patterns = AI_PHRASE_REPLACEMENTS[:50]
        else:
            patterns = AI_PHRASE_REPLACEMENTS
        
        for ai_phrase, replacements in patterns:
            pattern = re.compile(re.escape(ai_phrase), re.IGNORECASE)
            if pattern.search(content):
                replacement = random.choice([r for r in replacements if r] or replacements)
                original = content
                content = pattern.sub(replacement, content)
                if content != original:
                    self.replacements_made.append((ai_phrase, replacement))
        
        return content
    
    def _add_contractions(self, content: str) -> str:
        """Add contractions for natural reading."""
        for full_form, contraction in CONTRACTION_REPLACEMENTS:
            pattern = re.compile(r'\b' + re.escape(full_form) + r'\b', re.IGNORECASE)
            def replacer(m, c=contraction):
                if random.random() < 0.7:  # 70% chance
                    return c.capitalize() if m.group(0)[0].isupper() else c
                return m.group(0)
            content = pattern.sub(replacer, content)
        return content
    
    def detect_ai_phrases(self, content: str) -> List[Tuple[str, int]]:
        """Detect AI phrases without replacing."""
        detected = []
        content_lower = content.lower()
        for ai_phrase, _ in AI_PHRASE_REPLACEMENTS:
            count = content_lower.count(ai_phrase.lower())
            if count > 0:
                detected.append((ai_phrase, count))
        return sorted(detected, key=lambda x: x[1], reverse=True)
    
    def get_ai_score(self, content: str) -> float:
        """Calculate AI-ness score (0-100, lower is better)."""
        detected = self.detect_ai_phrases(content)
        if not detected:
            return 0.0
        word_count = len(content.split())
        if word_count == 0:
            return 0.0
        
        # Weight by position (earlier = more weight)
        score = sum((len(AI_PHRASE_REPLACEMENTS) - i) * count 
                    for i, (phrase, count) in enumerate(
                        (p, c) for p, c in detected 
                        for i2, (p2, _) in enumerate(AI_PHRASE_REPLACEMENTS) 
                        if p == p2
                    ) if i < 20) / 10
        
        return min(100, round(score * 100 / max(word_count / 50, 1), 1))


def humanize_content(content: str, aggression: str = "moderate") -> str:
    """Humanize content."""
    return ContentHumanizer(aggression_level=aggression).humanize(content)


def detect_ai_patterns(content: str) -> List[Tuple[str, int]]:
    """Detect AI patterns."""
    return ContentHumanizer().detect_ai_phrases(content)


def get_ai_score(content: str) -> float:
    """Get AI-ness score (0-100, lower is better)."""
    return ContentHumanizer().get_ai_score(content)
