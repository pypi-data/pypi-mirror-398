from ScriptCollection.GeneralUtilities import GeneralUtilities
from .Country import Country
from .Language import Language
from .CulturedLanguage import CulturedLanguage
from .CountryUtilities import CountryUtilities
from .CacheForCountries import CacheForCountries
from .CacheForLanguages import CacheForLanguages

version = "1.0.11"
__version__ = version


class CountryInformationCore:
    __country_utilities: CountryUtilities
    __cache_for_countries: CacheForCountries

    def __init__(self):
        self.__cache_for_countries = CacheForCountries()
        self.__cache_for_languages = CacheForLanguages()
        self.__country_utilities = CountryUtilities(self.__cache_for_countries)

    @GeneralUtilities.check_arguments
    def get_all_countries(self) -> list[Country]:
        return self.__cache_for_countries.get_all_countries()

    @GeneralUtilities.check_arguments
    def get_all_languages(self) -> list[Language]:
        return self.__cache_for_languages.get_all_languages()

    @GeneralUtilities.check_arguments
    def get_all_common_culture_language_combinations(self) -> list[CulturedLanguage]:
        return self.__country_utilities.get_all_common_culture_language_combinations()
