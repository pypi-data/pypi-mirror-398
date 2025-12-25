from __future__ import annotations

import re

from buvis.pybase.configuration import ConfigurationKeyNotFoundError, cfg

abbr_pattern = r"\b(\w+)\b(?!\s*\))"


class Abbr:
    @staticmethod
    def replace_abbreviations(
        text: str = "",
        abbreviations: list[dict] | None = None,
        level: int = 0,
    ) -> str:
        # Check if the passed list is None or empty, then use the default list
        if abbreviations is None or len(abbreviations) == 0:
            try:
                abbreviations = cfg.get_configuration_item("abbreviations")
            except ConfigurationKeyNotFoundError as _:
                abbreviations = []

        replacements = _get_abbreviations_replacements(abbreviations)

        # Replace occurrences of the abbreviation that are whole words
        # Replacement depends on the level:
        # 0: just fix the abbreviation case
        # 1: replace with expanded short text
        # 2: replace with expanded short text followed by abbreviation in paranthesis
        # 3: replace with expanded long text
        # 4: replace with expanded long text followed by abbreviation in paranthesis

        def replace_by_level(match: re.Match) -> str:
            abbr = match.group(1)
            if abbr.lower() not in replacements:
                return abbr

            abbr_correct, short, long = replacements[abbr.lower()]

            match level:
                case 0:
                    return abbr_correct
                case 1:
                    return short
                case 2:
                    return (
                        f"{short} ({abbr_correct})" if short != abbr_correct else short
                    )
                case 3:
                    return long
                case _:
                    return f"{long} ({abbr_correct})" if long != abbr_correct else long

        return re.sub(abbr_pattern, replace_by_level, text)


def _get_abbreviations_replacements(
    abbreviations: list[dict] | None = None,
) -> dict:
    if not abbreviations:
        return {}

    replacements = {}

    for abbreviation in abbreviations:
        if not isinstance(abbreviation, dict):
            abbreviation_dict = {abbreviation: abbreviation}
        else:
            abbreviation_dict = abbreviation

        for abbr, expansion in abbreviation_dict.items():
            short_long_expansion_pattern = r"^(?P<short>[^<]*)(?:<<(?P<long>[^>]*)>>)?$"
            if expansion is None:
                match = re.match(short_long_expansion_pattern, abbr)
            else:
                match = re.match(short_long_expansion_pattern, expansion)

            if match:
                short = match.group("short").strip()
                long = match.group("long")
                if long:
                    long = long.strip()
            else:
                short = abbr
                long = abbr

            if short is None or short == "":
                short = abbr

            if long is None or long == "":
                long = short
            replacements[abbr.lower()] = (abbr, short, long)

    return replacements
