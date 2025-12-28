# The content of this file is generated.
from .Country import Country
from .Language import Language
from .LanguageUtilities import LanguageUtilities
from .LanguageCodeConversionUtilities import LanguageCodeConversionUtilities


class CountryData:
    def get_all_countries(self) -> list[Country]:
        result:list[Country] = []
        language_utilities: LanguageUtilities = LanguageUtilities(None)

        languages_for_AF: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("prs"):
            languages_for_AF.append(language_utilities.get_language_from_code_iso639_3("prs"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("pus"):
            languages_for_AF.append(language_utilities.get_language_from_code_iso639_3("pus"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tuk"):
            languages_for_AF.append(language_utilities.get_language_from_code_iso639_3("tuk"))
        result.append(Country("Afghanistan", "Islamic Republic of Afghanistan", "AF", languages_for_AF))
        
        languages_for_AL: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sqi"):
            languages_for_AL.append(language_utilities.get_language_from_code_iso639_3("sqi"))
        result.append(Country("Albania", "Republic of Albania", "AL", languages_for_AL))
        
        languages_for_DZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_DZ.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Algeria", "People's Democratic Republic of Algeria", "DZ", languages_for_DZ))
        
        languages_for_AD: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("cat"):
            languages_for_AD.append(language_utilities.get_language_from_code_iso639_3("cat"))
        result.append(Country("Andorra", "Principality of Andorra", "AD", languages_for_AD))
        
        languages_for_AO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_AO.append(language_utilities.get_language_from_code_iso639_3("por"))
        result.append(Country("Angola", "Republic of Angola", "AO", languages_for_AO))
        
        languages_for_AG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_AG.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Antigua and Barbuda", "Antigua and Barbuda", "AG", languages_for_AG))
        
        languages_for_AR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("grn"):
            languages_for_AR.append(language_utilities.get_language_from_code_iso639_3("grn"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_AR.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Argentina", "Argentine Republic", "AR", languages_for_AR))
        
        languages_for_AM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hye"):
            languages_for_AM.append(language_utilities.get_language_from_code_iso639_3("hye"))
        result.append(Country("Armenia", "Republic of Armenia", "AM", languages_for_AM))
        
        languages_for_AU: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_AU.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Australia", "Commonwealth of Australia", "AU", languages_for_AU))
        
        languages_for_AT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bar"):
            languages_for_AT.append(language_utilities.get_language_from_code_iso639_3("bar"))
        result.append(Country("Austria", "Republic of Austria", "AT", languages_for_AT))
        
        languages_for_AZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("aze"):
            languages_for_AZ.append(language_utilities.get_language_from_code_iso639_3("aze"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            languages_for_AZ.append(language_utilities.get_language_from_code_iso639_3("rus"))
        result.append(Country("Azerbaijan", "Republic of Azerbaijan", "AZ", languages_for_AZ))
        
        languages_for_BS: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_BS.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Bahamas", "Commonwealth of the Bahamas", "BS", languages_for_BS))
        
        languages_for_BH: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_BH.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Bahrain", "Kingdom of Bahrain", "BH", languages_for_BH))
        
        languages_for_BD: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ben"):
            languages_for_BD.append(language_utilities.get_language_from_code_iso639_3("ben"))
        result.append(Country("Bangladesh", "People's Republic of Bangladesh", "BD", languages_for_BD))
        
        languages_for_BB: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_BB.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Barbados", "Barbados", "BB", languages_for_BB))
        
        languages_for_BY: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bel"):
            languages_for_BY.append(language_utilities.get_language_from_code_iso639_3("bel"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            languages_for_BY.append(language_utilities.get_language_from_code_iso639_3("rus"))
        result.append(Country("Belarus", "Republic of Belarus", "BY", languages_for_BY))
        
        languages_for_BE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("deu"):
            languages_for_BE.append(language_utilities.get_language_from_code_iso639_3("deu"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_BE.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nld"):
            languages_for_BE.append(language_utilities.get_language_from_code_iso639_3("nld"))
        result.append(Country("Belgium", "Kingdom of Belgium", "BE", languages_for_BE))
        
        languages_for_BZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bjz"):
            languages_for_BZ.append(language_utilities.get_language_from_code_iso639_3("bjz"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_BZ.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_BZ.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Belize", "Belize", "BZ", languages_for_BZ))
        
        languages_for_BJ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_BJ.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Benin", "Republic of Benin", "BJ", languages_for_BJ))
        
        languages_for_BT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("dzo"):
            languages_for_BT.append(language_utilities.get_language_from_code_iso639_3("dzo"))
        result.append(Country("Bhutan", "Kingdom of Bhutan", "BT", languages_for_BT))
        
        languages_for_BO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("aym"):
            languages_for_BO.append(language_utilities.get_language_from_code_iso639_3("aym"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("grn"):
            languages_for_BO.append(language_utilities.get_language_from_code_iso639_3("grn"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("que"):
            languages_for_BO.append(language_utilities.get_language_from_code_iso639_3("que"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_BO.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Bolivia", "Plurinational State of Bolivia", "BO", languages_for_BO))
        
        languages_for_BA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bos"):
            languages_for_BA.append(language_utilities.get_language_from_code_iso639_3("bos"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hrv"):
            languages_for_BA.append(language_utilities.get_language_from_code_iso639_3("hrv"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("srp"):
            languages_for_BA.append(language_utilities.get_language_from_code_iso639_3("srp"))
        result.append(Country("Bosnia and Herzegovina", "Bosnia and Herzegovina", "BA", languages_for_BA))
        
        languages_for_BW: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_BW.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tsn"):
            languages_for_BW.append(language_utilities.get_language_from_code_iso639_3("tsn"))
        result.append(Country("Botswana", "Republic of Botswana", "BW", languages_for_BW))
        
        languages_for_BR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_BR.append(language_utilities.get_language_from_code_iso639_3("por"))
        result.append(Country("Brazil", "Federative Republic of Brazil", "BR", languages_for_BR))
        
        languages_for_BN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("msa"):
            languages_for_BN.append(language_utilities.get_language_from_code_iso639_3("msa"))
        result.append(Country("Brunei", "Nation of Brunei, Abode of Peace", "BN", languages_for_BN))
        
        languages_for_BG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bul"):
            languages_for_BG.append(language_utilities.get_language_from_code_iso639_3("bul"))
        result.append(Country("Bulgaria", "Republic of Bulgaria", "BG", languages_for_BG))
        
        languages_for_BF: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_BF.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Burkina Faso", "Burkina Faso", "BF", languages_for_BF))
        
        languages_for_BI: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_BI.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("run"):
            languages_for_BI.append(language_utilities.get_language_from_code_iso639_3("run"))
        result.append(Country("Burundi", "Republic of Burundi", "BI", languages_for_BI))
        
        languages_for_KH: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("khm"):
            languages_for_KH.append(language_utilities.get_language_from_code_iso639_3("khm"))
        result.append(Country("Cambodia", "Kingdom of Cambodia", "KH", languages_for_KH))
        
        languages_for_CM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_CM.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_CM.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Cameroon", "Republic of Cameroon", "CM", languages_for_CM))
        
        languages_for_CA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_CA.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_CA.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Canada", "Canada", "CA", languages_for_CA))
        
        languages_for_CV: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_CV.append(language_utilities.get_language_from_code_iso639_3("por"))
        result.append(Country("Cape Verde", "Republic of Cabo Verde", "CV", languages_for_CV))
        
        languages_for_CF: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_CF.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sag"):
            languages_for_CF.append(language_utilities.get_language_from_code_iso639_3("sag"))
        result.append(Country("Central African Republic", "Central African Republic", "CF", languages_for_CF))
        
        languages_for_TD: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_TD.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_TD.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Chad", "Republic of Chad", "TD", languages_for_TD))
        
        languages_for_CL: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_CL.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Chile", "Republic of Chile", "CL", languages_for_CL))
        
        languages_for_CN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zho"):
            languages_for_CN.append(language_utilities.get_language_from_code_iso639_3("zho"))
        result.append(Country("China", "People's Republic of China", "CN", languages_for_CN))
        
        languages_for_CO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_CO.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Colombia", "Republic of Colombia", "CO", languages_for_CO))
        
        languages_for_KM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_KM.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_KM.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zdj"):
            languages_for_KM.append(language_utilities.get_language_from_code_iso639_3("zdj"))
        result.append(Country("Comoros", "Union of the Comoros", "KM", languages_for_KM))
        
        languages_for_CG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_CG.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kon"):
            languages_for_CG.append(language_utilities.get_language_from_code_iso639_3("kon"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lin"):
            languages_for_CG.append(language_utilities.get_language_from_code_iso639_3("lin"))
        result.append(Country("Congo", "Republic of the Congo", "CG", languages_for_CG))
        
        languages_for_CR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_CR.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Costa Rica", "Republic of Costa Rica", "CR", languages_for_CR))
        
        languages_for_HR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hrv"):
            languages_for_HR.append(language_utilities.get_language_from_code_iso639_3("hrv"))
        result.append(Country("Croatia", "Republic of Croatia", "HR", languages_for_HR))
        
        languages_for_CU: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_CU.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Cuba", "Republic of Cuba", "CU", languages_for_CU))
        
        languages_for_CY: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ell"):
            languages_for_CY.append(language_utilities.get_language_from_code_iso639_3("ell"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tur"):
            languages_for_CY.append(language_utilities.get_language_from_code_iso639_3("tur"))
        result.append(Country("Cyprus", "Republic of Cyprus", "CY", languages_for_CY))
        
        languages_for_CZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ces"):
            languages_for_CZ.append(language_utilities.get_language_from_code_iso639_3("ces"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("slk"):
            languages_for_CZ.append(language_utilities.get_language_from_code_iso639_3("slk"))
        result.append(Country("Czechia", "Czech Republic", "CZ", languages_for_CZ))
        
        languages_for_CD: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_CD.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kon"):
            languages_for_CD.append(language_utilities.get_language_from_code_iso639_3("kon"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lin"):
            languages_for_CD.append(language_utilities.get_language_from_code_iso639_3("lin"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lua"):
            languages_for_CD.append(language_utilities.get_language_from_code_iso639_3("lua"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("swa"):
            languages_for_CD.append(language_utilities.get_language_from_code_iso639_3("swa"))
        result.append(Country("DR Congo", "Democratic Republic of the Congo", "CD", languages_for_CD))
        
        languages_for_DK: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("dan"):
            languages_for_DK.append(language_utilities.get_language_from_code_iso639_3("dan"))
        result.append(Country("Denmark", "Kingdom of Denmark", "DK", languages_for_DK))
        
        languages_for_DJ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_DJ.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_DJ.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Djibouti", "Republic of Djibouti", "DJ", languages_for_DJ))
        
        languages_for_DM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_DM.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Dominica", "Commonwealth of Dominica", "DM", languages_for_DM))
        
        languages_for_DO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_DO.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Dominican Republic", "Dominican Republic", "DO", languages_for_DO))
        
        languages_for_EC: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_EC.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Ecuador", "Republic of Ecuador", "EC", languages_for_EC))
        
        languages_for_EG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_EG.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Egypt", "Arab Republic of Egypt", "EG", languages_for_EG))
        
        languages_for_SV: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_SV.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("El Salvador", "Republic of El Salvador", "SV", languages_for_SV))
        
        languages_for_GQ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_GQ.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_GQ.append(language_utilities.get_language_from_code_iso639_3("por"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_GQ.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Equatorial Guinea", "Republic of Equatorial Guinea", "GQ", languages_for_GQ))
        
        languages_for_ER: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_ER.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_ER.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tir"):
            languages_for_ER.append(language_utilities.get_language_from_code_iso639_3("tir"))
        result.append(Country("Eritrea", "State of Eritrea", "ER", languages_for_ER))
        
        languages_for_EE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("est"):
            languages_for_EE.append(language_utilities.get_language_from_code_iso639_3("est"))
        result.append(Country("Estonia", "Republic of Estonia", "EE", languages_for_EE))
        
        languages_for_SZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_SZ.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ssw"):
            languages_for_SZ.append(language_utilities.get_language_from_code_iso639_3("ssw"))
        result.append(Country("Eswatini", "Kingdom of Eswatini", "SZ", languages_for_SZ))
        
        languages_for_ET: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("amh"):
            languages_for_ET.append(language_utilities.get_language_from_code_iso639_3("amh"))
        result.append(Country("Ethiopia", "Federal Democratic Republic of Ethiopia", "ET", languages_for_ET))
        
        languages_for_FJ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_FJ.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fij"):
            languages_for_FJ.append(language_utilities.get_language_from_code_iso639_3("fij"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hif"):
            languages_for_FJ.append(language_utilities.get_language_from_code_iso639_3("hif"))
        result.append(Country("Fiji", "Republic of Fiji", "FJ", languages_for_FJ))
        
        languages_for_FI: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fin"):
            languages_for_FI.append(language_utilities.get_language_from_code_iso639_3("fin"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("swe"):
            languages_for_FI.append(language_utilities.get_language_from_code_iso639_3("swe"))
        result.append(Country("Finland", "Republic of Finland", "FI", languages_for_FI))
        
        languages_for_FR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_FR.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("France", "French Republic", "FR", languages_for_FR))
        
        languages_for_GA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_GA.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Gabon", "Gabonese Republic", "GA", languages_for_GA))
        
        languages_for_GM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_GM.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Gambia", "Republic of the Gambia", "GM", languages_for_GM))
        
        languages_for_GE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kat"):
            languages_for_GE.append(language_utilities.get_language_from_code_iso639_3("kat"))
        result.append(Country("Georgia", "Georgia", "GE", languages_for_GE))
        
        languages_for_DE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("deu"):
            languages_for_DE.append(language_utilities.get_language_from_code_iso639_3("deu"))
        result.append(Country("Germany", "Federal Republic of Germany", "DE", languages_for_DE))
        
        languages_for_GH: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_GH.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Ghana", "Republic of Ghana", "GH", languages_for_GH))
        
        languages_for_GR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ell"):
            languages_for_GR.append(language_utilities.get_language_from_code_iso639_3("ell"))
        result.append(Country("Greece", "Hellenic Republic", "GR", languages_for_GR))
        
        languages_for_GD: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_GD.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Grenada", "Grenada", "GD", languages_for_GD))
        
        languages_for_GT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_GT.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Guatemala", "Republic of Guatemala", "GT", languages_for_GT))
        
        languages_for_GN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_GN.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Guinea", "Republic of Guinea", "GN", languages_for_GN))
        
        languages_for_GW: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_GW.append(language_utilities.get_language_from_code_iso639_3("por"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("pov"):
            languages_for_GW.append(language_utilities.get_language_from_code_iso639_3("pov"))
        result.append(Country("Guinea-Bissau", "Republic of Guinea-Bissau", "GW", languages_for_GW))
        
        languages_for_GY: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_GY.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Guyana", "Co-operative Republic of Guyana", "GY", languages_for_GY))
        
        languages_for_HT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_HT.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hat"):
            languages_for_HT.append(language_utilities.get_language_from_code_iso639_3("hat"))
        result.append(Country("Haiti", "Republic of Haiti", "HT", languages_for_HT))
        
        languages_for_HN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_HN.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Honduras", "Republic of Honduras", "HN", languages_for_HN))
        
        languages_for_HU: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hun"):
            languages_for_HU.append(language_utilities.get_language_from_code_iso639_3("hun"))
        result.append(Country("Hungary", "Hungary", "HU", languages_for_HU))
        
        languages_for_IS: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("isl"):
            languages_for_IS.append(language_utilities.get_language_from_code_iso639_3("isl"))
        result.append(Country("Iceland", "Iceland", "IS", languages_for_IS))
        
        languages_for_IN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_IN.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hin"):
            languages_for_IN.append(language_utilities.get_language_from_code_iso639_3("hin"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tam"):
            languages_for_IN.append(language_utilities.get_language_from_code_iso639_3("tam"))
        result.append(Country("India", "Republic of India", "IN", languages_for_IN))
        
        languages_for_ID: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ind"):
            languages_for_ID.append(language_utilities.get_language_from_code_iso639_3("ind"))
        result.append(Country("Indonesia", "Republic of Indonesia", "ID", languages_for_ID))
        
        languages_for_IR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fas"):
            languages_for_IR.append(language_utilities.get_language_from_code_iso639_3("fas"))
        result.append(Country("Iran", "Islamic Republic of Iran", "IR", languages_for_IR))
        
        languages_for_IQ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_IQ.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("arc"):
            languages_for_IQ.append(language_utilities.get_language_from_code_iso639_3("arc"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ckb"):
            languages_for_IQ.append(language_utilities.get_language_from_code_iso639_3("ckb"))
        result.append(Country("Iraq", "Republic of Iraq", "IQ", languages_for_IQ))
        
        languages_for_IE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_IE.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("gle"):
            languages_for_IE.append(language_utilities.get_language_from_code_iso639_3("gle"))
        result.append(Country("Ireland", "Republic of Ireland", "IE", languages_for_IE))
        
        languages_for_IL: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_IL.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("heb"):
            languages_for_IL.append(language_utilities.get_language_from_code_iso639_3("heb"))
        result.append(Country("Israel", "State of Israel", "IL", languages_for_IL))
        
        languages_for_IT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ita"):
            languages_for_IT.append(language_utilities.get_language_from_code_iso639_3("ita"))
        result.append(Country("Italy", "Italian Republic", "IT", languages_for_IT))
        
        languages_for_CI: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_CI.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Ivory Coast", "Republic of Côte d'Ivoire", "CI", languages_for_CI))
        
        languages_for_JM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_JM.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("jam"):
            languages_for_JM.append(language_utilities.get_language_from_code_iso639_3("jam"))
        result.append(Country("Jamaica", "Jamaica", "JM", languages_for_JM))
        
        languages_for_JP: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("jpn"):
            languages_for_JP.append(language_utilities.get_language_from_code_iso639_3("jpn"))
        result.append(Country("Japan", "Japan", "JP", languages_for_JP))
        
        languages_for_JO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_JO.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Jordan", "Hashemite Kingdom of Jordan", "JO", languages_for_JO))
        
        languages_for_KZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kaz"):
            languages_for_KZ.append(language_utilities.get_language_from_code_iso639_3("kaz"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            languages_for_KZ.append(language_utilities.get_language_from_code_iso639_3("rus"))
        result.append(Country("Kazakhstan", "Republic of Kazakhstan", "KZ", languages_for_KZ))
        
        languages_for_KE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_KE.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("swa"):
            languages_for_KE.append(language_utilities.get_language_from_code_iso639_3("swa"))
        result.append(Country("Kenya", "Republic of Kenya", "KE", languages_for_KE))
        
        languages_for_KI: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_KI.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("gil"):
            languages_for_KI.append(language_utilities.get_language_from_code_iso639_3("gil"))
        result.append(Country("Kiribati", "Independent and Sovereign Republic of Kiribati", "KI", languages_for_KI))
        
        languages_for_KW: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_KW.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Kuwait", "State of Kuwait", "KW", languages_for_KW))
        
        languages_for_KG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kir"):
            languages_for_KG.append(language_utilities.get_language_from_code_iso639_3("kir"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            languages_for_KG.append(language_utilities.get_language_from_code_iso639_3("rus"))
        result.append(Country("Kyrgyzstan", "Kyrgyz Republic", "KG", languages_for_KG))
        
        languages_for_LA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lao"):
            languages_for_LA.append(language_utilities.get_language_from_code_iso639_3("lao"))
        result.append(Country("Laos", "Lao People's Democratic Republic", "LA", languages_for_LA))
        
        languages_for_LV: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lav"):
            languages_for_LV.append(language_utilities.get_language_from_code_iso639_3("lav"))
        result.append(Country("Latvia", "Republic of Latvia", "LV", languages_for_LV))
        
        languages_for_LB: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_LB.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_LB.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Lebanon", "Lebanese Republic", "LB", languages_for_LB))
        
        languages_for_LS: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_LS.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sot"):
            languages_for_LS.append(language_utilities.get_language_from_code_iso639_3("sot"))
        result.append(Country("Lesotho", "Kingdom of Lesotho", "LS", languages_for_LS))
        
        languages_for_LR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_LR.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Liberia", "Republic of Liberia", "LR", languages_for_LR))
        
        languages_for_LY: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_LY.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Libya", "State of Libya", "LY", languages_for_LY))
        
        languages_for_LI: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("deu"):
            languages_for_LI.append(language_utilities.get_language_from_code_iso639_3("deu"))
        result.append(Country("Liechtenstein", "Principality of Liechtenstein", "LI", languages_for_LI))
        
        languages_for_LT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lit"):
            languages_for_LT.append(language_utilities.get_language_from_code_iso639_3("lit"))
        result.append(Country("Lithuania", "Republic of Lithuania", "LT", languages_for_LT))
        
        languages_for_LU: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("deu"):
            languages_for_LU.append(language_utilities.get_language_from_code_iso639_3("deu"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_LU.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ltz"):
            languages_for_LU.append(language_utilities.get_language_from_code_iso639_3("ltz"))
        result.append(Country("Luxembourg", "Grand Duchy of Luxembourg", "LU", languages_for_LU))
        
        languages_for_MG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_MG.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mlg"):
            languages_for_MG.append(language_utilities.get_language_from_code_iso639_3("mlg"))
        result.append(Country("Madagascar", "Republic of Madagascar", "MG", languages_for_MG))
        
        languages_for_MW: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_MW.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nya"):
            languages_for_MW.append(language_utilities.get_language_from_code_iso639_3("nya"))
        result.append(Country("Malawi", "Republic of Malawi", "MW", languages_for_MW))
        
        languages_for_MY: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_MY.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("msa"):
            languages_for_MY.append(language_utilities.get_language_from_code_iso639_3("msa"))
        result.append(Country("Malaysia", "Malaysia", "MY", languages_for_MY))
        
        languages_for_MV: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("div"):
            languages_for_MV.append(language_utilities.get_language_from_code_iso639_3("div"))
        result.append(Country("Maldives", "Republic of the Maldives", "MV", languages_for_MV))
        
        languages_for_ML: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_ML.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Mali", "Republic of Mali", "ML", languages_for_ML))
        
        languages_for_MT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_MT.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mlt"):
            languages_for_MT.append(language_utilities.get_language_from_code_iso639_3("mlt"))
        result.append(Country("Malta", "Republic of Malta", "MT", languages_for_MT))
        
        languages_for_MH: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_MH.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mah"):
            languages_for_MH.append(language_utilities.get_language_from_code_iso639_3("mah"))
        result.append(Country("Marshall Islands", "Republic of the Marshall Islands", "MH", languages_for_MH))
        
        languages_for_MR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_MR.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Mauritania", "Islamic Republic of Mauritania", "MR", languages_for_MR))
        
        languages_for_MU: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_MU.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_MU.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mfe"):
            languages_for_MU.append(language_utilities.get_language_from_code_iso639_3("mfe"))
        result.append(Country("Mauritius", "Republic of Mauritius", "MU", languages_for_MU))
        
        languages_for_MX: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_MX.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Mexico", "United Mexican States", "MX", languages_for_MX))
        
        languages_for_FM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_FM.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Micronesia", "Federated States of Micronesia", "FM", languages_for_FM))
        
        languages_for_MD: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ron"):
            languages_for_MD.append(language_utilities.get_language_from_code_iso639_3("ron"))
        result.append(Country("Moldova", "Republic of Moldova", "MD", languages_for_MD))
        
        languages_for_MC: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_MC.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Monaco", "Principality of Monaco", "MC", languages_for_MC))
        
        languages_for_MN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mon"):
            languages_for_MN.append(language_utilities.get_language_from_code_iso639_3("mon"))
        result.append(Country("Mongolia", "Mongolia", "MN", languages_for_MN))
        
        languages_for_ME: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("cnr"):
            languages_for_ME.append(language_utilities.get_language_from_code_iso639_3("cnr"))
        result.append(Country("Montenegro", "Montenegro", "ME", languages_for_ME))
        
        languages_for_MA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_MA.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ber"):
            languages_for_MA.append(language_utilities.get_language_from_code_iso639_3("ber"))
        result.append(Country("Morocco", "Kingdom of Morocco", "MA", languages_for_MA))
        
        languages_for_MZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_MZ.append(language_utilities.get_language_from_code_iso639_3("por"))
        result.append(Country("Mozambique", "Republic of Mozambique", "MZ", languages_for_MZ))
        
        languages_for_MM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mya"):
            languages_for_MM.append(language_utilities.get_language_from_code_iso639_3("mya"))
        result.append(Country("Myanmar", "Republic of the Union of Myanmar", "MM", languages_for_MM))
        
        languages_for_NA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("afr"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("afr"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("deu"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("deu"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("her"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("her"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hgm"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("hgm"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kwn"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("kwn"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("loz"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("loz"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ndo"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("ndo"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tsn"):
            languages_for_NA.append(language_utilities.get_language_from_code_iso639_3("tsn"))
        result.append(Country("Namibia", "Republic of Namibia", "NA", languages_for_NA))
        
        languages_for_NR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_NR.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nau"):
            languages_for_NR.append(language_utilities.get_language_from_code_iso639_3("nau"))
        result.append(Country("Nauru", "Republic of Nauru", "NR", languages_for_NR))
        
        languages_for_NP: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nep"):
            languages_for_NP.append(language_utilities.get_language_from_code_iso639_3("nep"))
        result.append(Country("Nepal", "Federal Democratic Republic of Nepal", "NP", languages_for_NP))
        
        languages_for_NL: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nld"):
            languages_for_NL.append(language_utilities.get_language_from_code_iso639_3("nld"))
        result.append(Country("Netherlands", "Kingdom of the Netherlands", "NL", languages_for_NL))
        
        languages_for_NZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_NZ.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mri"):
            languages_for_NZ.append(language_utilities.get_language_from_code_iso639_3("mri"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nzs"):
            languages_for_NZ.append(language_utilities.get_language_from_code_iso639_3("nzs"))
        result.append(Country("New Zealand", "New Zealand", "NZ", languages_for_NZ))
        
        languages_for_NI: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_NI.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Nicaragua", "Republic of Nicaragua", "NI", languages_for_NI))
        
        languages_for_NE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_NE.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Niger", "Republic of Niger", "NE", languages_for_NE))
        
        languages_for_NG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_NG.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Nigeria", "Federal Republic of Nigeria", "NG", languages_for_NG))
        
        languages_for_KP: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kor"):
            languages_for_KP.append(language_utilities.get_language_from_code_iso639_3("kor"))
        result.append(Country("North Korea", "Democratic People's Republic of Korea", "KP", languages_for_KP))
        
        languages_for_MK: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("mkd"):
            languages_for_MK.append(language_utilities.get_language_from_code_iso639_3("mkd"))
        result.append(Country("North Macedonia", "Republic of North Macedonia", "MK", languages_for_MK))
        
        languages_for_NO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nno"):
            languages_for_NO.append(language_utilities.get_language_from_code_iso639_3("nno"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nob"):
            languages_for_NO.append(language_utilities.get_language_from_code_iso639_3("nob"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("smi"):
            languages_for_NO.append(language_utilities.get_language_from_code_iso639_3("smi"))
        result.append(Country("Norway", "Kingdom of Norway", "NO", languages_for_NO))
        
        languages_for_OM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_OM.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Oman", "Sultanate of Oman", "OM", languages_for_OM))
        
        languages_for_PK: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_PK.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("urd"):
            languages_for_PK.append(language_utilities.get_language_from_code_iso639_3("urd"))
        result.append(Country("Pakistan", "Islamic Republic of Pakistan", "PK", languages_for_PK))
        
        languages_for_PW: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_PW.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("pau"):
            languages_for_PW.append(language_utilities.get_language_from_code_iso639_3("pau"))
        result.append(Country("Palau", "Republic of Palau", "PW", languages_for_PW))
        
        languages_for_PA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_PA.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Panama", "Republic of Panama", "PA", languages_for_PA))
        
        languages_for_PG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_PG.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("hmo"):
            languages_for_PG.append(language_utilities.get_language_from_code_iso639_3("hmo"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tpi"):
            languages_for_PG.append(language_utilities.get_language_from_code_iso639_3("tpi"))
        result.append(Country("Papua New Guinea", "Independent State of Papua New Guinea", "PG", languages_for_PG))
        
        languages_for_PY: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("grn"):
            languages_for_PY.append(language_utilities.get_language_from_code_iso639_3("grn"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_PY.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Paraguay", "Republic of Paraguay", "PY", languages_for_PY))
        
        languages_for_PE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("aym"):
            languages_for_PE.append(language_utilities.get_language_from_code_iso639_3("aym"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("que"):
            languages_for_PE.append(language_utilities.get_language_from_code_iso639_3("que"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_PE.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Peru", "Republic of Peru", "PE", languages_for_PE))
        
        languages_for_PH: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_PH.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fil"):
            languages_for_PH.append(language_utilities.get_language_from_code_iso639_3("fil"))
        result.append(Country("Philippines", "Republic of the Philippines", "PH", languages_for_PH))
        
        languages_for_PL: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("pol"):
            languages_for_PL.append(language_utilities.get_language_from_code_iso639_3("pol"))
        result.append(Country("Poland", "Republic of Poland", "PL", languages_for_PL))
        
        languages_for_PT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_PT.append(language_utilities.get_language_from_code_iso639_3("por"))
        result.append(Country("Portugal", "Portuguese Republic", "PT", languages_for_PT))
        
        languages_for_QA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_QA.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Qatar", "State of Qatar", "QA", languages_for_QA))
        
        languages_for_RO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ron"):
            languages_for_RO.append(language_utilities.get_language_from_code_iso639_3("ron"))
        result.append(Country("Romania", "Romania", "RO", languages_for_RO))
        
        languages_for_RU: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            languages_for_RU.append(language_utilities.get_language_from_code_iso639_3("rus"))
        result.append(Country("Russia", "Russian Federation", "RU", languages_for_RU))
        
        languages_for_RW: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_RW.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_RW.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kin"):
            languages_for_RW.append(language_utilities.get_language_from_code_iso639_3("kin"))
        result.append(Country("Rwanda", "Republic of Rwanda", "RW", languages_for_RW))
        
        languages_for_KN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_KN.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Saint Kitts and Nevis", "Federation of Saint Christopher and Nevis", "KN", languages_for_KN))
        
        languages_for_LC: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_LC.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Saint Lucia", "Saint Lucia", "LC", languages_for_LC))
        
        languages_for_VC: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_VC.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Saint Vincent and the Grenadines", "Saint Vincent and the Grenadines", "VC", languages_for_VC))
        
        languages_for_WS: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_WS.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("smo"):
            languages_for_WS.append(language_utilities.get_language_from_code_iso639_3("smo"))
        result.append(Country("Samoa", "Independent State of Samoa", "WS", languages_for_WS))
        
        languages_for_SM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ita"):
            languages_for_SM.append(language_utilities.get_language_from_code_iso639_3("ita"))
        result.append(Country("San Marino", "Most Serene Republic of San Marino", "SM", languages_for_SM))
        
        languages_for_SA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_SA.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Saudi Arabia", "Kingdom of Saudi Arabia", "SA", languages_for_SA))
        
        languages_for_SN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_SN.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Senegal", "Republic of Senegal", "SN", languages_for_SN))
        
        languages_for_RS: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("srp"):
            languages_for_RS.append(language_utilities.get_language_from_code_iso639_3("srp"))
        result.append(Country("Serbia", "Republic of Serbia", "RS", languages_for_RS))
        
        languages_for_SC: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("crs"):
            languages_for_SC.append(language_utilities.get_language_from_code_iso639_3("crs"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_SC.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_SC.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Seychelles", "Republic of Seychelles", "SC", languages_for_SC))
        
        languages_for_SL: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_SL.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Sierra Leone", "Republic of Sierra Leone", "SL", languages_for_SL))
        
        languages_for_SG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_SG.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("msa"):
            languages_for_SG.append(language_utilities.get_language_from_code_iso639_3("msa"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tam"):
            languages_for_SG.append(language_utilities.get_language_from_code_iso639_3("tam"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zho"):
            languages_for_SG.append(language_utilities.get_language_from_code_iso639_3("zho"))
        result.append(Country("Singapore", "Republic of Singapore", "SG", languages_for_SG))
        
        languages_for_SK: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("slk"):
            languages_for_SK.append(language_utilities.get_language_from_code_iso639_3("slk"))
        result.append(Country("Slovakia", "Slovak Republic", "SK", languages_for_SK))
        
        languages_for_SI: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("slv"):
            languages_for_SI.append(language_utilities.get_language_from_code_iso639_3("slv"))
        result.append(Country("Slovenia", "Republic of Slovenia", "SI", languages_for_SI))
        
        languages_for_SB: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_SB.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Solomon Islands", "Solomon Islands", "SB", languages_for_SB))
        
        languages_for_SO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_SO.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("som"):
            languages_for_SO.append(language_utilities.get_language_from_code_iso639_3("som"))
        result.append(Country("Somalia", "Federal Republic of Somalia", "SO", languages_for_SO))
        
        languages_for_ZA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("afr"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("afr"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nbl"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("nbl"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nso"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("nso"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sot"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("sot"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ssw"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("ssw"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tsn"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("tsn"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tso"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("tso"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ven"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("ven"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("xho"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("xho"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zul"):
            languages_for_ZA.append(language_utilities.get_language_from_code_iso639_3("zul"))
        result.append(Country("South Africa", "Republic of South Africa", "ZA", languages_for_ZA))
        
        languages_for_KR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kor"):
            languages_for_KR.append(language_utilities.get_language_from_code_iso639_3("kor"))
        result.append(Country("South Korea", "Republic of Korea", "KR", languages_for_KR))
        
        languages_for_SS: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_SS.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("South Sudan", "Republic of South Sudan", "SS", languages_for_SS))
        
        languages_for_ES: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_ES.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Spain", "Kingdom of Spain", "ES", languages_for_ES))
        
        languages_for_LK: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sin"):
            languages_for_LK.append(language_utilities.get_language_from_code_iso639_3("sin"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tam"):
            languages_for_LK.append(language_utilities.get_language_from_code_iso639_3("tam"))
        result.append(Country("Sri Lanka", "Democratic Socialist Republic of Sri Lanka", "LK", languages_for_LK))
        
        languages_for_SD: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_SD.append(language_utilities.get_language_from_code_iso639_3("ara"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_SD.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Sudan", "Republic of the Sudan", "SD", languages_for_SD))
        
        languages_for_SR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nld"):
            languages_for_SR.append(language_utilities.get_language_from_code_iso639_3("nld"))
        result.append(Country("Suriname", "Republic of Suriname", "SR", languages_for_SR))
        
        languages_for_SE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("swe"):
            languages_for_SE.append(language_utilities.get_language_from_code_iso639_3("swe"))
        result.append(Country("Sweden", "Kingdom of Sweden", "SE", languages_for_SE))
        
        languages_for_CH: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_CH.append(language_utilities.get_language_from_code_iso639_3("fra"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("gsw"):
            languages_for_CH.append(language_utilities.get_language_from_code_iso639_3("gsw"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ita"):
            languages_for_CH.append(language_utilities.get_language_from_code_iso639_3("ita"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("roh"):
            languages_for_CH.append(language_utilities.get_language_from_code_iso639_3("roh"))
        result.append(Country("Switzerland", "Swiss Confederation", "CH", languages_for_CH))
        
        languages_for_SY: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_SY.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Syria", "Syrian Arab Republic", "SY", languages_for_SY))
        
        languages_for_ST: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_ST.append(language_utilities.get_language_from_code_iso639_3("por"))
        result.append(Country("São Tomé and Príncipe", "Democratic Republic of São Tomé and Príncipe", "ST", languages_for_ST))
        
        languages_for_TJ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            languages_for_TJ.append(language_utilities.get_language_from_code_iso639_3("rus"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tgk"):
            languages_for_TJ.append(language_utilities.get_language_from_code_iso639_3("tgk"))
        result.append(Country("Tajikistan", "Republic of Tajikistan", "TJ", languages_for_TJ))
        
        languages_for_TZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_TZ.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("swa"):
            languages_for_TZ.append(language_utilities.get_language_from_code_iso639_3("swa"))
        result.append(Country("Tanzania", "United Republic of Tanzania", "TZ", languages_for_TZ))
        
        languages_for_TH: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tha"):
            languages_for_TH.append(language_utilities.get_language_from_code_iso639_3("tha"))
        result.append(Country("Thailand", "Kingdom of Thailand", "TH", languages_for_TH))
        
        languages_for_TL: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("por"):
            languages_for_TL.append(language_utilities.get_language_from_code_iso639_3("por"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tet"):
            languages_for_TL.append(language_utilities.get_language_from_code_iso639_3("tet"))
        result.append(Country("Timor-Leste", "Democratic Republic of Timor-Leste", "TL", languages_for_TL))
        
        languages_for_TG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_TG.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Togo", "Togolese Republic", "TG", languages_for_TG))
        
        languages_for_TO: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_TO.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ton"):
            languages_for_TO.append(language_utilities.get_language_from_code_iso639_3("ton"))
        result.append(Country("Tonga", "Kingdom of Tonga", "TO", languages_for_TO))
        
        languages_for_TT: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_TT.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Trinidad and Tobago", "Republic of Trinidad and Tobago", "TT", languages_for_TT))
        
        languages_for_TN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_TN.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Tunisia", "Tunisian Republic", "TN", languages_for_TN))
        
        languages_for_TM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            languages_for_TM.append(language_utilities.get_language_from_code_iso639_3("rus"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tuk"):
            languages_for_TM.append(language_utilities.get_language_from_code_iso639_3("tuk"))
        result.append(Country("Turkmenistan", "Turkmenistan", "TM", languages_for_TM))
        
        languages_for_TV: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_TV.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tvl"):
            languages_for_TV.append(language_utilities.get_language_from_code_iso639_3("tvl"))
        result.append(Country("Tuvalu", "Tuvalu", "TV", languages_for_TV))
        
        languages_for_TR: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tur"):
            languages_for_TR.append(language_utilities.get_language_from_code_iso639_3("tur"))
        result.append(Country("Türkiye", "Republic of Türkiye", "TR", languages_for_TR))
        
        languages_for_UG: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_UG.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("swa"):
            languages_for_UG.append(language_utilities.get_language_from_code_iso639_3("swa"))
        result.append(Country("Uganda", "Republic of Uganda", "UG", languages_for_UG))
        
        languages_for_UA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ukr"):
            languages_for_UA.append(language_utilities.get_language_from_code_iso639_3("ukr"))
        result.append(Country("Ukraine", "Ukraine", "UA", languages_for_UA))
        
        languages_for_AE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_AE.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("United Arab Emirates", "United Arab Emirates", "AE", languages_for_AE))
        
        languages_for_GB: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_GB.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("United Kingdom", "United Kingdom of Great Britain and Northern Ireland", "GB", languages_for_GB))
        
        languages_for_US: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_US.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("United States", "United States of America", "US", languages_for_US))
        
        languages_for_UY: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_UY.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Uruguay", "Oriental Republic of Uruguay", "UY", languages_for_UY))
        
        languages_for_UZ: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("rus"):
            languages_for_UZ.append(language_utilities.get_language_from_code_iso639_3("rus"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("uzb"):
            languages_for_UZ.append(language_utilities.get_language_from_code_iso639_3("uzb"))
        result.append(Country("Uzbekistan", "Republic of Uzbekistan", "UZ", languages_for_UZ))
        
        languages_for_VU: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bis"):
            languages_for_VU.append(language_utilities.get_language_from_code_iso639_3("bis"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_VU.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("fra"):
            languages_for_VU.append(language_utilities.get_language_from_code_iso639_3("fra"))
        result.append(Country("Vanuatu", "Republic of Vanuatu", "VU", languages_for_VU))
        
        languages_for_VA: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ita"):
            languages_for_VA.append(language_utilities.get_language_from_code_iso639_3("ita"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("lat"):
            languages_for_VA.append(language_utilities.get_language_from_code_iso639_3("lat"))
        result.append(Country("Vatican City", "Vatican City State", "VA", languages_for_VA))
        
        languages_for_VE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("spa"):
            languages_for_VE.append(language_utilities.get_language_from_code_iso639_3("spa"))
        result.append(Country("Venezuela", "Bolivarian Republic of Venezuela", "VE", languages_for_VE))
        
        languages_for_VN: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("vie"):
            languages_for_VN.append(language_utilities.get_language_from_code_iso639_3("vie"))
        result.append(Country("Vietnam", "Socialist Republic of Vietnam", "VN", languages_for_VN))
        
        languages_for_YE: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ara"):
            languages_for_YE.append(language_utilities.get_language_from_code_iso639_3("ara"))
        result.append(Country("Yemen", "Republic of Yemen", "YE", languages_for_YE))
        
        languages_for_ZM: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_ZM.append(language_utilities.get_language_from_code_iso639_3("eng"))
        result.append(Country("Zambia", "Republic of Zambia", "ZM", languages_for_ZM))
        
        languages_for_ZW: list[Language] = []
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("bwg"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("bwg"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("eng"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("eng"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("kck"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("kck"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("khi"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("khi"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ndc"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("ndc"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nde"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("nde"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("nya"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("nya"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sna"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("sna"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("sot"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("sot"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("toi"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("toi"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tsn"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("tsn"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("tso"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("tso"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("ven"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("ven"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("xho"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("xho"))
        if LanguageCodeConversionUtilities().iso639_3_code_is_supported("zib"):
            languages_for_ZW.append(language_utilities.get_language_from_code_iso639_3("zib"))
        result.append(Country("Zimbabwe", "Republic of Zimbabwe", "ZW", languages_for_ZW))
        

        return result
