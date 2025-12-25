from __future__ import annotations

import re

from buvis.pybase.formatting.string_operator.abbr import Abbr
from buvis.pybase.formatting.string_operator.string_case_tools import StringCaseTools
from buvis.pybase.formatting.string_operator.tag_suggester import TagSuggester
from buvis.pybase.formatting.string_operator.word_level_tools import WordLevelTools


class StringOperator:
    @staticmethod
    def collapse(text: str) -> str:
        return " ".join(text.split()).rstrip().lstrip()

    @staticmethod
    def shorten(text: str, limit: int, suffix_length: int) -> str:
        if len(text) > limit:
            return text[: limit - suffix_length] + "..." + text[-suffix_length:]

        return text

    @staticmethod
    def prepend(text: str, prepend_text: str) -> str:
        if text.startswith(prepend_text):
            return text

        return f"{prepend_text}{text}"

    @staticmethod
    def slugify(text: str) -> str:
        text = str(text)
        unsafe = [
            '"',
            "#",
            "$",
            "%",
            "&",
            "+",
            ",",
            "/",
            ":",
            ";",
            "=",
            "?",
            "@",
            "[",
            "\\",
            "]",
            "^",
            "`",
            "{",
            "|",
            "}",
            "~",
            "'",
            "_",
        ]
        text = text.translate({ord(char): "-" for char in unsafe})
        text = "-".join(text.split())
        text = re.sub("-{2,}", "-", text)

        return text.lower()

    @staticmethod
    def singularize(text: str) -> str:
        return WordLevelTools.singularize(text)

    @staticmethod
    def pluralize(text: str) -> str:
        return WordLevelTools.pluralize(text)

    @staticmethod
    def humanize(text: str) -> str:
        return StringCaseTools.humanize(text)

    @staticmethod
    def underscore(text: str) -> str:
        return StringCaseTools.underscore(text)

    @staticmethod
    def as_note_field_name(text: str) -> str:
        return StringCaseTools.as_note_field_name(text)

    @staticmethod
    def as_graphql_field_name(text: str) -> str:
        return StringCaseTools.as_graphql_field_name(text)

    @staticmethod
    def camelize(text: str) -> str:
        return StringCaseTools.camelize(text)

    @staticmethod
    def replace_abbreviations(
        text: str = "",
        abbreviations: list[dict] | None = None,
        level: int = 0,
    ) -> str:
        return Abbr.replace_abbreviations(text, abbreviations, level)

    @staticmethod
    def suggest_tags(text: str, limit_count: int = 10) -> list:
        tag_suggester = TagSuggester()

        return tag_suggester.suggest(text)[:limit_count]
