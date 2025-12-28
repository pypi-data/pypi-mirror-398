"""Keyword matching for Polymarket markets."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from ..config import KeywordGroup, KeywordsConfig


@dataclass
class MatchResult:
    """Result of matching a market against keywords."""

    market_id: str
    matched: bool
    matched_groups: List[str] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)
    score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market_id": self.market_id,
            "matched": self.matched,
            "matched_groups": self.matched_groups,
            "matched_keywords": self.matched_keywords,
            "score": self.score,
            "details": self.details,
        }


class KeywordMatcher:
    """Keyword matcher for Polymarket markets.

    Supports multiple matching modes:
    - contains: Case-insensitive substring match
    - regex: Regular expression match
    - fuzzy: Fuzzy string matching (simple Levenshtein distance)
    """

    def __init__(
        self,
        config: Optional[KeywordsConfig] = None,
        enabled_groups: Optional[Set[str]] = None,
    ):
        """Initialize the keyword matcher.

        Args:
            config: Keywords configuration.
            enabled_groups: Set of enabled keyword group names.
        """
        self.config = config or KeywordsConfig()
        self.enabled_groups = enabled_groups or set()
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}

        # Pre-compile regex patterns if any
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for keyword groups."""
        for group in self.config.keywords:
            if not group.enabled:
                continue
            if self.enabled_groups and group.name not in self.enabled_groups:
                continue

            if group.match_mode == "regex":
                patterns = []
                for pattern in group.patterns:
                    try:
                        compiled = re.compile(pattern, re.IGNORECASE)
                        patterns.append(compiled)
                    except re.error:
                        # Skip invalid regex patterns
                        continue
                self._compiled_patterns[group.name] = patterns

    def _match_contains(
        self,
        text: str,
        patterns: List[str],
    ) -> Set[str]:
        """Match using contains mode (case-insensitive substring).

        Args:
            text: Text to search in.
            patterns: List of patterns to match.

        Returns:
            Set of matched patterns.
        """
        text_lower = text.lower()
        matched = set()
        for pattern in patterns:
            if pattern.lower() in text_lower:
                matched.add(pattern)
        return matched

    def _match_regex(
        self,
        text: str,
        group_name: str,
    ) -> Set[str]:
        """Match using regex mode.

        Args:
            text: Text to search in.
            group_name: Name of the keyword group.

        Returns:
            Set of matched patterns.
        """
        patterns = self._compiled_patterns.get(group_name, [])
        matched = set()
        for pattern in patterns:
            if pattern.search(text):
                matched.add(pattern.pattern)
        return matched

    def _match_fuzzy(
        self,
        text: str,
        patterns: List[str],
        threshold: float = 0.8,
    ) -> Set[str]:
        """Match using fuzzy string matching.

        Uses a simple word-based matching approach.

        Args:
            text: Text to search in.
            patterns: List of patterns to match.
            threshold: Similarity threshold (0.0 to 1.0).

        Returns:
            Set of matched patterns.
        """
        text_words = set(text.lower().split())
        matched = set()

        for pattern in patterns:
            pattern_lower = pattern.lower()
            pattern_words = set(pattern_lower.split())

            # Check for exact word matches
            if pattern_lower in text_words:
                matched.add(pattern)
                continue

            # Check for partial matches
            for word in pattern_words:
                for text_word in text_words:
                    if word == text_word:
                        matched.add(pattern)
                        break

        return matched

    def _is_excluded(self, text: str) -> bool:
        """Check if the text matches any exclude rule.

        Args:
            text: Text to check.

        Returns:
            True if excluded.
        """
        text_lower = text.lower()
        for exclude in self.config.excludes:
            if exclude.pattern.lower() in text_lower:
                return True
        return False

    def match(
        self,
        market_id: str,
        question: str,
        description: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> MatchResult:
        """Match a market against configured keywords.

        Args:
            market_id: Market ID.
            question: Market question.
            description: Market description.
            categories: Market categories.
            tags: Market tags.

        Returns:
            MatchResult with match details.
        """
        result = MatchResult(market_id=market_id, matched=False)

        # Combine text fields for matching
        text_fields = [question]
        if description:
            text_fields.append(description)
        combined_text = " ".join(filter(None, text_fields))

        # Check exclusions first
        if self._is_excluded(combined_text):
            result.details["excluded"] = True
            result.details["reason"] = "Matches exclusion rule"
            return result

        # Match against each keyword group
        all_matched_keywords: Set[str] = set()
        matched_group_names: Set[str] = set()

        for group in self.config.keywords:
            if not group.enabled:
                continue
            if self.enabled_groups and group.name not in self.enabled_groups:
                continue

            group_matched = set()

            for text in text_fields:
                if group.match_mode == "regex":
                    group_matched = group_matched.union(
                        self._match_regex(text, group.name)
                    )
                elif group.match_mode == "fuzzy":
                    group_matched = group_matched.union(
                        self._match_fuzzy(text, group.patterns)
                    )
                else:  # contains
                    group_matched = group_matched.union(
                        self._match_contains(text, group.patterns)
                    )

            if group_matched:
                result.matched = True
                matched_group_names.add(group.name)
                all_matched_keywords.update(group_matched)
                result.score += group.priority

        result.matched_groups = list(matched_group_names)
        result.matched_keywords = list(all_matched_keywords)
        result.details["question"] = question

        if categories:
            result.details["categories"] = categories
        if tags:
            result.details["tags"] = tags

        return result

    def match_market_data(
        self,
        market_data: Dict[str, Any],
    ) -> MatchResult:
        """Match market data dictionary against keywords.

        Args:
            market_data: Market data dictionary.

        Returns:
            MatchResult with match details.
        """
        return self.match(
            market_id=market_data.get("id", ""),
            question=market_data.get("question", ""),
            description=market_data.get("description"),
            categories=[c.get("label") for c in market_data.get("categories", []) if c.get("label")],
            tags=[t.get("label") for t in market_data.get("tags", []) if t.get("label")],
        )

    def filter_markets(
        self,
        markets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Filter markets by keyword matching.

        Args:
            markets: List of market data dictionaries.

        Returns:
            List of markets that match the keywords.
        """
        matched = []
        for market in markets:
            result = self.match_market_data(market)
            if result.matched:
                market["_match_result"] = result.to_dict()
                matched.append(market)
        return matched

    def get_enabled_groups(self) -> List[KeywordGroup]:
        """Get list of enabled keyword groups.

        Returns:
            List of enabled KeywordGroup instances.
        """
        return [
            g for g in self.config.keywords
            if g.enabled and (not self.enabled_groups or g.name in self.enabled_groups)
        ]

    def get_group(self, name: str) -> Optional[KeywordGroup]:
        """Get a keyword group by name.

        Args:
            name: Group name.

        Returns:
            KeywordGroup instance or None.
        """
        for group in self.config.keywords:
            if group.name == name:
                return group
        return None


def create_matcher(
    keywords_config: KeywordsConfig,
    enabled_groups: Optional[Set[str]] = None,
) -> KeywordMatcher:
    """Create a keyword matcher from configuration.

    Args:
        keywords_config: Keywords configuration.
        enabled_groups: Set of enabled group names.

    Returns:
        KeywordMatcher instance.
    """
    return KeywordMatcher(keywords_config, enabled_groups)
