
class Language:
    name_in_english: str
    abbreviation_iso639_1: str
    abbreviation_iso639_3: str

    def __init__(self, abbreviation_iso639_1: str, abbreviation_iso639_3: str, name_in_english: str):
        self.abbreviation_iso639_1 = abbreviation_iso639_1
        self.abbreviation_iso639_3 = abbreviation_iso639_3
        self.name_in_english = name_in_english

    def __str__(self):
        return f"{self.name_in_english} ({self.abbreviation_iso639_1}; {self.abbreviation_iso639_3})"

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, Language):
            return False
        return self.name_in_english == other.name_in_english

    def __hash__(self):
        return hash(self.name_in_english)
