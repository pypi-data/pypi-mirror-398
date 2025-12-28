"""Matcher module for keyword and market filtering."""

from .keyword_matcher import KeywordMatcher, MatchResult, create_matcher

__all__ = [
    "KeywordMatcher",
    "MatchResult",
    "create_matcher",
]
