from .Country import Country
from .Language import Language


class CulturedLanguage:
    language: Language
    country: Country

    def __init__(self, language: Language, country: Country):
        self.language = language
        self.country = country

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, CulturedLanguage):
            return False
        return self.language == other.language and self.country == other.country

    def __hash__(self):
        return hash((self.language, self.country))

    def get_abbreviation(self) -> str:
        return f"{self.language.abbreviation_iso639_1}-{self.country.country_code}"
