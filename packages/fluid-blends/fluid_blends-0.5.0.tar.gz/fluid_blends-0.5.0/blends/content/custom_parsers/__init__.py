from blends.content.custom_parsers.helm_templates import helm_parser
from blends.models import CustomParser, Language

custom_parsers_by_language: dict[Language, list[CustomParser]] = {
    Language.JSON: [helm_parser],
    Language.YAML: [helm_parser],
}
