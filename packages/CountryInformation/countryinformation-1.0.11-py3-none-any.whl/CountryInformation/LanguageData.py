# The content of this file is generated.
from .Language import Language
from .LanguageCodeConversionUtilities import LanguageCodeConversionUtilities

class LanguageData:
    def get_all_languages(self)->list[Language]:
        result:list[Language]=[]

        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("afr"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("afr"), "afr", "Afrikaans"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("amh"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("amh"), "amh", "Amharic"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ara"), "ara", "Arabic"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("arc"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("arc"), "arc", "Aramaic"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("aym"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("aym"), "aym", "Aymara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("aze"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("aze"), "aze", "Azerbaijani"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bar"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("bar"), "bar", "Austro-Bavarian German"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bel"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("bel"), "bel", "Belarusian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ben"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ben"), "ben", "Bengali"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ber"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ber"), "ber", "Berber"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bis"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("bis"), "bis", "Bislama"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bjz"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("bjz"), "bjz", "Belizean Creole"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bos"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("bos"), "bos", "Bosnian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bul"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("bul"), "bul", "Bulgarian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bwg"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("bwg"), "bwg", "Chibarwe"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("cat"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("cat"), "cat", "Catalan"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ces"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ces"), "ces", "Czech"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ckb"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ckb"), "ckb", "Sorani"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("cnr"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("cnr"), "cnr", "Montenegrin"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("crs"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("crs"), "crs", "Seychellois Creole"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("dan"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("dan"), "dan", "Danish"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("deu"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("deu"), "deu", "German"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("div"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("div"), "div", "Maldivian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("dzo"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("dzo"), "dzo", "Dzongkha"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ell"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ell"), "ell", "Greek"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("eng"), "eng", "English"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("est"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("est"), "est", "Estonian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fas"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("fas"), "fas", "Persian (Farsi)"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fij"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("fij"), "fij", "Fijian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fil"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("fil"), "fil", "Filipino"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fin"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("fin"), "fin", "Finnish"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("fra"), "fra", "French"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("gil"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("gil"), "gil", "Gilbertese"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("gle"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("gle"), "gle", "Irish"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("grn"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("grn"), "grn", "Guaraní"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("gsw"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("gsw"), "gsw", "Swiss German"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hat"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("hat"), "hat", "Haitian Creole"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("heb"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("heb"), "heb", "Hebrew"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("her"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("her"), "her", "Herero"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hgm"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("hgm"), "hgm", "Khoekhoe"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hif"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("hif"), "hif", "Fiji Hindi"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hin"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("hin"), "hin", "Hindi"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hmo"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("hmo"), "hmo", "Hiri Motu"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hrv"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("hrv"), "hrv", "Croatian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hun"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("hun"), "hun", "Hungarian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hye"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("hye"), "hye", "Armenian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ind"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ind"), "ind", "Indonesian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("isl"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("isl"), "isl", "Icelandic"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ita"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ita"), "ita", "Italian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("jam"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("jam"), "jam", "Jamaican Patois"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("jpn"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("jpn"), "jpn", "Japanese"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kat"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("kat"), "kat", "Georgian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kaz"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("kaz"), "kaz", "Kazakh"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kck"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("kck"), "kck", "Kalanga"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("khi"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("khi"), "khi", "Khoisan"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("khm"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("khm"), "khm", "Khmer"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kin"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("kin"), "kin", "Kinyarwanda"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kir"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("kir"), "kir", "Kyrgyz"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kon"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("kon"), "kon", "Kikongo"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kor"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("kor"), "kor", "Korean"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kwn"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("kwn"), "kwn", "Kwangali"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lao"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("lao"), "lao", "Lao"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lat"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("lat"), "lat", "Latin"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lav"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("lav"), "lav", "Latvian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lin"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("lin"), "lin", "Lingala"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lit"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("lit"), "lit", "Lithuanian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("loz"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("loz"), "loz", "Lozi"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ltz"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ltz"), "ltz", "Luxembourgish"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lua"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("lua"), "lua", "Tshiluba"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mah"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("mah"), "mah", "Marshallese"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mfe"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("mfe"), "mfe", "Mauritian Creole"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mkd"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("mkd"), "mkd", "Macedonian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mlg"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("mlg"), "mlg", "Malagasy"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mlt"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("mlt"), "mlt", "Maltese"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mon"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("mon"), "mon", "Mongolian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mri"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("mri"), "mri", "Māori"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("msa"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("msa"), "msa", "Malay"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mya"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("mya"), "mya", "Burmese"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nau"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nau"), "nau", "Nauru"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nbl"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nbl"), "nbl", "Southern Ndebele"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ndc"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ndc"), "ndc", "Ndau"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nde"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nde"), "nde", "Northern Ndebele"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ndo"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ndo"), "ndo", "Ndonga"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nep"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nep"), "nep", "Nepali"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nld"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nld"), "nld", "Dutch"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nno"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nno"), "nno", "Norwegian Nynorsk"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nob"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nob"), "nob", "Norwegian Bokmål"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nso"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nso"), "nso", "Northern Sotho"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nya"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nya"), "nya", "Chewa"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nzs"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("nzs"), "nzs", "New Zealand Sign Language"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("pau"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("pau"), "pau", "Palauan"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("pol"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("pol"), "pol", "Polish"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("por"), "por", "Portuguese"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("pov"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("pov"), "pov", "Upper Guinea Creole"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("prs"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("prs"), "prs", "Dari"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("pus"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("pus"), "pus", "Pashto"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("que"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("que"), "que", "Quechua"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("roh"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("roh"), "roh", "Romansh"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ron"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ron"), "ron", "Romanian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("run"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("run"), "run", "Kirundi"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("rus"), "rus", "Russian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sag"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("sag"), "sag", "Sango"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sin"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("sin"), "sin", "Sinhala"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("slk"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("slk"), "slk", "Slovak"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("slv"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("slv"), "slv", "Slovene"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("smi"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("smi"), "smi", "Sami"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("smo"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("smo"), "smo", "Samoan"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sna"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("sna"), "sna", "Shona"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("som"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("som"), "som", "Somali"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sot"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("sot"), "sot", "Sotho"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("spa"), "spa", "Spanish"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sqi"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("sqi"), "sqi", "Albanian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("srp"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("srp"), "srp", "Serbian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ssw"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ssw"), "ssw", "Swazi"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("swa"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("swa"), "swa", "Swahili"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("swe"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("swe"), "swe", "Swedish"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tam"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tam"), "tam", "Tamil"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tet"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tet"), "tet", "Tetum"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tgk"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tgk"), "tgk", "Tajik"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tha"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tha"), "tha", "Thai"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tir"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tir"), "tir", "Tigrinya"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("toi"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("toi"), "toi", "Tonga"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ton"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ton"), "ton", "Tongan"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tpi"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tpi"), "tpi", "Tok Pisin"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tsn"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tsn"), "tsn", "Tswana"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tso"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tso"), "tso", "Tsonga"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tuk"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tuk"), "tuk", "Turkmen"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tur"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tur"), "tur", "Turkish"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tvl"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("tvl"), "tvl", "Tuvaluan"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ukr"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ukr"), "ukr", "Ukrainian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("urd"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("urd"), "urd", "Urdu"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("uzb"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("uzb"), "uzb", "Uzbek"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ven"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("ven"), "ven", "Venda"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("vie"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("vie"), "vie", "Vietnamese"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("xho"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("xho"), "xho", "Xhosa"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zdj"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("zdj"), "zdj", "Comorian"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zho"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("zho"), "zho", "Chinese"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zib"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("zib"), "zib", "Zimbabwean Sign Language"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zul"):
            result.append(Language(LanguageCodeConversionUtilities().get_iso639_1_code_from_iso639_3("zul"), "zul", "Zulu"))

        return result
