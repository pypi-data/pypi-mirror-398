from inflection import camelize as infl_camelize
from inflection import humanize as infl_humanize
from inflection import underscore as infl_underscore


class StringCaseTools:
    @staticmethod
    def humanize(text: str) -> str:
        return infl_humanize(text)

    @staticmethod
    def underscore(text: str) -> str:
        return infl_underscore(text)

    @staticmethod
    def as_note_field_name(text: str) -> str:
        return StringCaseTools.underscore(text).replace("_", "-").lower()

    @staticmethod
    def as_graphql_field_name(text: str) -> str:
        return StringCaseTools.camelize(text)

    @staticmethod
    def camelize(text: str) -> str:
        text = text.replace("-", "_")

        return infl_camelize(text)
