from ScriptCollection.GeneralUtilities import GeneralUtilities
from .CulturedLanguage import CulturedLanguage
from .CacheForCountries import CacheForCountries


class CountryUtilities:
    __cache_for_countries: CacheForCountries

    def __init__(self, __cache_for_countries: CacheForCountries):
        if __cache_for_countries is None:
            __cache_for_countries = CacheForCountries()
        self.__cache_for_countries = __cache_for_countries

    @GeneralUtilities.check_arguments
    def get_all_common_culture_language_combinations(self) -> list[CulturedLanguage]:
        result: set[CulturedLanguage] = set()
        for country in self.__cache_for_countries.get_all_countries():
            for language in country.languages:
                result.add(CulturedLanguage(language, country))
        return sorted(result, key=lambda item: item.get_abbreviation())
