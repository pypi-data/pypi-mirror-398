from ScriptCollection.GeneralUtilities import GeneralUtilities
from .CacheForLanguages import CacheForLanguages
from .Language import Language
from .LanguageCodeConversionUtilities import LanguageCodeConversionUtilities


class LanguageUtilities:
    __cache_for_languages: CacheForLanguages

    def __init__(self, cache_for_languages: CacheForLanguages):
        if cache_for_languages is None:
            cache_for_languages = CacheForLanguages()
        self.__cache_for_languages = cache_for_languages

    @GeneralUtilities.check_arguments
    def get_language_from_iso639_1_code(self,  iso639_1_code: str) -> Language:
        for language in self.__cache_for_languages.get_all_languages():
            if language.abbreviation_iso639_1 == iso639_1_code:
                return language
        raise ValueError(f"No language found with abbreviation \"{iso639_1_code}\".")

    @GeneralUtilities.check_arguments
    def get_language_from_code_iso639_3(self,  iso639_3_code: str) -> Language:
        return self.get_language_from_iso639_1_code(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3(iso639_3_code))
