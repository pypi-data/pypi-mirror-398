from inflection import pluralize as infl_pluralize
from inflection import singularize as infl_singularize


class WordLevelTools:
    @staticmethod
    def singularize(text: str) -> str:
        exceptions = ["minutes"]

        return text if text in exceptions else infl_singularize(text)

    @staticmethod
    def pluralize(text: str) -> str:
        exceptions = ["minutes"]

        return text if text in exceptions else infl_pluralize(text)
