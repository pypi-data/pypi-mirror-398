from .Country import Country
from .CountryData import CountryData


class CacheForCountries:
    __countries: list[Country] = None

    def get_all_countries(self) -> list[Country]:
        if self.__countries is None:
            self.__countries = CountryData().get_all_countries()
        return self.__countries
