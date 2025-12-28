import random
import time
class mustafatik:
    def __init__(self):
        self.devices = {
            # Samsung Galaxy A Series (50 جهاز)
            "SM-A015F": "Samsung", "SM-A015G": "Samsung", "SM-A015M": "Samsung", "SM-A015T": "Samsung", "SM-A015U": "Samsung",
            "SM-A025F": "Samsung", "SM-A025G": "Samsung", "SM-A025M": "Samsung", "SM-A025U": "Samsung", "SM-A025V": "Samsung",
            "SM-A035F": "Samsung", "SM-A035G": "Samsung", "SM-A035M": "Samsung", "SM-A035T": "Samsung", "SM-A035U": "Samsung",
            "SM-A045F": "Samsung", "SM-A045G": "Samsung", "SM-A045M": "Samsung", "SM-A045T": "Samsung", "SM-A045U": "Samsung",
            "SM-A055F": "Samsung", "SM-A055G": "Samsung", "SM-A055M": "Samsung", "SM-A055U": "Samsung", "SM-A055V": "Samsung",
            "SM-A065F": "Samsung", "SM-A065G": "Samsung", "SM-A065M": "Samsung", "SM-A065U": "Samsung", "SM-A065V": "Samsung",
            "SM-A075F": "Samsung", "SM-A075G": "Samsung", "SM-A075M": "Samsung", "SM-A075U": "Samsung", "SM-A075V": "Samsung",
            "SM-A085F": "Samsung", "SM-A085G": "Samsung", "SM-A085M": "Samsung", "SM-A085U": "Samsung", "SM-A085V": "Samsung",
            "SM-A095F": "Samsung", "SM-A095G": "Samsung", "SM-A095M": "Samsung", "SM-A095U": "Samsung", "SM-A095V": "Samsung",
            "SM-A105F": "Samsung", "SM-A105G": "Samsung", "SM-A105M": "Samsung", "SM-A105N": "Samsung", "SM-A105U": "Samsung",
            
            # Samsung Galaxy S Series (50 جهاز)
            "SM-S901E": "Samsung", "SM-S901U": "Samsung", "SM-S901W": "Samsung", "SM-S901N": "Samsung", "SM-S9010": "Samsung",
            "SM-S906E": "Samsung", "SM-S906U": "Samsung", "SM-S906W": "Samsung", "SM-S906N": "Samsung", "SM-S9060": "Samsung",
            "SM-S911B": "Samsung", "SM-S911U": "Samsung", "SM-S911W": "Samsung", "SM-S911N": "Samsung", "SM-S9110": "Samsung",
            "SM-S916B": "Samsung", "SM-S916U": "Samsung", "SM-S916W": "Samsung", "SM-S916N": "Samsung", "SM-S9160": "Samsung",
            "SM-S918B": "Samsung", "SM-S918U": "Samsung", "SM-S918W": "Samsung", "SM-S918N": "Samsung", "SM-S9180": "Samsung",
            "SM-G990E": "Samsung", "SM-G990U": "Samsung", "SM-G990W": "Samsung", "SM-G990N": "Samsung", "SM-G9900": "Samsung",
            "SM-G991B": "Samsung", "SM-G991U": "Samsung", "SM-G991W": "Samsung", "SM-G991N": "Samsung", "SM-G9910": "Samsung",
            "SM-G998B": "Samsung", "SM-G998U": "Samsung", "SM-G998W": "Samsung", "SM-G998N": "Samsung", "SM-G9980": "Samsung",
            "SM-G999B": "Samsung", "SM-G999U": "Samsung", "SM-G999W": "Samsung", "SM-G999N": "Samsung", "SM-G9990": "Samsung",
            
            # Samsung Galaxy M Series (50 جهاز)
            "SM-M015F": "Samsung", "SM-M015G": "Samsung", "SM-M015M": "Samsung", "SM-M015U": "Samsung", "SM-M015V": "Samsung",
            "SM-M025F": "Samsung", "SM-M025G": "Samsung", "SM-M025M": "Samsung", "SM-M025U": "Samsung", "SM-M025V": "Samsung",
            "SM-M035F": "Samsung", "SM-M035G": "Samsung", "SM-M035M": "Samsung", "SM-M035U": "Samsung", "SM-M035V": "Samsung",
            "SM-M045F": "Samsung", "SM-M045G": "Samsung", "SM-M045M": "Samsung", "SM-M045U": "Samsung", "SM-M045V": "Samsung",
            "SM-M055F": "Samsung", "SM-M055G": "Samsung", "SM-M055M": "Samsung", "SM-M055U": "Samsung", "SM-M055V": "Samsung",
            "SM-M065F": "Samsung", "SM-M065G": "Samsung", "SM-M065M": "Samsung", "SM-M065U": "Samsung", "SM-M065V": "Samsung",
            "SM-M075F": "Samsung", "SM-M075G": "Samsung", "SM-M075M": "Samsung", "SM-M075U": "Samsung", "SM-M075V": "Samsung",
            "SM-M085F": "Samsung", "SM-M085G": "Samsung", "SM-M085M": "Samsung", "SM-M085U": "Samsung", "SM-M085V": "Samsung",
            "SM-M095F": "Samsung", "SM-M095G": "Samsung", "SM-M095M": "Samsung", "SM-M095U": "Samsung", "SM-M095V": "Samsung",
            "SM-M105F": "Samsung", "SM-M105G": "Samsung", "SM-M105M": "Samsung", "SM-M105U": "Samsung", "SM-M105V": "Samsung",
            
            # Samsung Galaxy Z/Fold Series (30 جهاز)
            "SM-F711B": "Samsung", "SM-F711U": "Samsung", "SM-F711W": "Samsung", "SM-F711N": "Samsung", "SM-F7110": "Samsung",
            "SM-F721B": "Samsung", "SM-F721U": "Samsung", "SM-F721W": "Samsung", "SM-F721N": "Samsung", "SM-F7210": "Samsung",
            "SM-F731B": "Samsung", "SM-F731U": "Samsung", "SM-F731W": "Samsung", "SM-F731N": "Samsung", "SM-F7310": "Samsung",
            "SM-F936B": "Samsung", "SM-F936U": "Samsung", "SM-F936W": "Samsung", "SM-F936N": "Samsung", "SM-F9360": "Samsung",
            "SM-F946B": "Samsung", "SM-F946U": "Samsung", "SM-F946W": "Samsung", "SM-F946N": "Samsung", "SM-F9460": "Samsung",
            "SM-F956B": "Samsung", "SM-F956U": "Samsung", "SM-F956W": "Samsung", "SM-F956N": "Samsung", "SM-F9560": "Samsung",
            
            # Xiaomi Redmi Note Series (100 جهاز)
            "2201116SG": "Xiaomi", "2201116SI": "Xiaomi", "2201116SR": "Xiaomi", "2201116ST": "Xiaomi", "2201116SU": "Xiaomi",
            "2201117TG": "Xiaomi", "2201117TI": "Xiaomi", "2201117TR": "Xiaomi", "2201117TU": "Xiaomi", "2201117TV": "Xiaomi",
            "22031116BG": "Xiaomi", "22031116BI": "Xiaomi", "22031116BR": "Xiaomi", "22031116BU": "Xiaomi", "22031116BV": "Xiaomi",
            "22041211AC": "Xiaomi", "22041211AG": "Xiaomi", "22041211AI": "Xiaomi", "22041211AR": "Xiaomi", "22041211AU": "Xiaomi",
            "2109119DG": "Xiaomi", "2109119DI": "Xiaomi", "2109119DR": "Xiaomi", "2109119DU": "Xiaomi", "2109119DV": "Xiaomi",
            "2107113SG": "Xiaomi", "2107113SI": "Xiaomi", "2107113SR": "Xiaomi", "2107113SU": "Xiaomi", "2107113SV": "Xiaomi",
            "21061110AG": "Xiaomi", "21061110AI": "Xiaomi", "21061110AR": "Xiaomi", "21061110AU": "Xiaomi", "21061110AV": "Xiaomi",
            "21051110C": "Xiaomi", "21051110G": "Xiaomi", "21051110I": "Xiaomi", "21051110R": "Xiaomi", "21051110U": "Xiaomi",
            "2009119DG": "Xiaomi", "2009119DI": "Xiaomi", "2009119DR": "Xiaomi", "2009119DU": "Xiaomi", "2009119DV": "Xiaomi",
            "2007113SG": "Xiaomi", "2007113SI": "Xiaomi", "2007113SR": "Xiaomi", "2007113SU": "Xiaomi", "2007113SV": "Xiaomi",
            "23076RN4DG": "Xiaomi", "23076RN4DI": "Xiaomi", "23076RN4DR": "Xiaomi", "23076RN4DU": "Xiaomi", "23076RN4DV": "Xiaomi",
            "23077RABDG": "Xiaomi", "23077RABDI": "Xiaomi", "23077RABDR": "Xiaomi", "23077RABDU": "Xiaomi", "23077RABDV": "Xiaomi",
            "23087RADEG": "Xiaomi", "23087RADEI": "Xiaomi", "23087RADER": "Xiaomi", "23087RADEU": "Xiaomi", "23087RADEV": "Xiaomi",
            "2312DRAABG": "Xiaomi", "2312DRAABI": "Xiaomi", "2312DRAABR": "Xiaomi", "2312DRAABU": "Xiaomi", "2312DRAABV": "Xiaomi",
            "23117RK66G": "Xiaomi", "23117RK66I": "Xiaomi", "23117RK66R": "Xiaomi", "23117RK66U": "Xiaomi", "23117RK66V": "Xiaomi",
            "23128RN77G": "Xiaomi", "23128RN77I": "Xiaomi", "23128RN77R": "Xiaomi", "23128RN77U": "Xiaomi", "23128RN77V": "Xiaomi",
            "23129RN77G": "Xiaomi", "23129RN77I": "Xiaomi", "23129RN77R": "Xiaomi", "23129RN77U": "Xiaomi", "23129RN77V": "Xiaomi",
            "24031PN0DG": "Xiaomi", "24031PN0DI": "Xiaomi", "24031PN0DR": "Xiaomi", "24031PN0DU": "Xiaomi", "24031PN0DV": "Xiaomi",
            "24041PN6DG": "Xiaomi", "24041PN6DI": "Xiaomi", "24041PN6DR": "Xiaomi", "24041PN6DU": "Xiaomi", "24041PN6DV": "Xiaomi",
            
            # Xiaomi Mi Series (50 جهاز)
            "M2101K6G": "Xiaomi", "M2101K6I": "Xiaomi", "M2101K6R": "Xiaomi", "M2101K6U": "Xiaomi", "M2101K6V": "Xiaomi",
            "M2102J20SG": "Xiaomi", "M2102J20SI": "Xiaomi", "M2102J20SR": "Xiaomi", "M2102J20SU": "Xiaomi", "M2102J20SV": "Xiaomi",
            "M2103K19G": "Xiaomi", "M2103K19I": "Xiaomi", "M2103K19R": "Xiaomi", "M2103K19U": "Xiaomi", "M2103K19V": "Xiaomi",
            "M2012K11AG": "Xiaomi", "M2012K11AI": "Xiaomi", "M2012K11AR": "Xiaomi", "M2012K11AU": "Xiaomi", "M2012K11AV": "Xiaomi",
            "M2203J22G": "Xiaomi", "M2203J22I": "Xiaomi", "M2203J22R": "Xiaomi", "M2203J22U": "Xiaomi", "M2203J22V": "Xiaomi",
            "M2204J19G": "Xiaomi", "M2204J19I": "Xiaomi", "M2204J19R": "Xiaomi", "M2204J19U": "Xiaomi", "M2204J19V": "Xiaomi",
            "M2303C44G": "Xiaomi", "M2303C44I": "Xiaomi", "M2303C44R": "Xiaomi", "M2303C44U": "Xiaomi", "M2303C44V": "Xiaomi",
            "M2304F10G": "Xiaomi", "M2304F10I": "Xiaomi", "M2304F10R": "Xiaomi", "M2304F10U": "Xiaomi", "M2304F10V": "Xiaomi",
            "M2305F10G": "Xiaomi", "M2305F10I": "Xiaomi", "M2305F10R": "Xiaomi", "M2305F10U": "Xiaomi", "M2305F10V": "Xiaomi",
            "M2403K21G": "Xiaomi", "M2403K21I": "Xiaomi", "M2403K21R": "Xiaomi", "M2403K21U": "Xiaomi", "M2403K21V": "Xiaomi",
            
            # Xiaomi Poco Series (50 جهاز)
            "2201116PG": "Xiaomi", "2201116PI": "Xiaomi", "2201116PR": "Xiaomi", "2201116PU": "Xiaomi", "2201116PV": "Xiaomi",
            "22021211PG": "Xiaomi", "22021211PI": "Xiaomi", "22021211PR": "Xiaomi", "22021211PU": "Xiaomi", "22021211PV": "Xiaomi",
            "22031116PG": "Xiaomi", "22031116PI": "Xiaomi", "22031116PR": "Xiaomi", "22031116PU": "Xiaomi", "22031116PV": "Xiaomi",
            "22041211PG": "Xiaomi", "22041211PI": "Xiaomi", "22041211PR": "Xiaomi", "22041211PU": "Xiaomi", "22041211PV": "Xiaomi",
            "23046PNC9G": "Xiaomi", "23046PNC9I": "Xiaomi", "23046PNC9R": "Xiaomi", "23046PNC9U": "Xiaomi", "23046PNC9V": "Xiaomi",
            "23049PCD8G": "Xiaomi", "23049PCD8I": "Xiaomi", "23049PCD8R": "Xiaomi", "23049PCD8U": "Xiaomi", "23049PCD8V": "Xiaomi",
            "23117RK66G": "Xiaomi", "23117RK66I": "Xiaomi", "23117RK66R": "Xiaomi", "23117RK66U": "Xiaomi", "23117RK66V": "Xiaomi",
            "23129PN77G": "Xiaomi", "23129PN77I": "Xiaomi", "23129PN77R": "Xiaomi", "23129PN77U": "Xiaomi", "23129PN77V": "Xiaomi",
            "24030PM87G": "Xiaomi", "24030PM87I": "Xiaomi", "24030PM87R": "Xiaomi", "24030PM87U": "Xiaomi", "24030PM87V": "Xiaomi",
            "24041PNC9G": "Xiaomi", "24041PNC9I": "Xiaomi", "24041PNC9R": "Xiaomi", "24041PNC9U": "Xiaomi", "24041PNC9V": "Xiaomi",
            
            # Realme C/Numbers Series (100 جهاز)
            "RMX3085": "Realme", "RMX3081": "Realme", "RMX3082": "Realme", "RMX3083": "Realme", "RMX3084": "Realme",
            "RMX3092": "Realme", "RMX3091": "Realme", "RMX3093": "Realme", "RMX3094": "Realme", "RMX3095": "Realme",
            "RMX3311": "Realme", "RMX3312": "Realme", "RMX3313": "Realme", "RMX3314": "Realme", "RMX3315": "Realme",
            "RMX3370": "Realme", "RMX3371": "Realme", "RMX3372": "Realme", "RMX3373": "Realme", "RMX3374": "Realme",
            "RMX3461": "Realme", "RMX3462": "Realme", "RMX3463": "Realme", "RMX3464": "Realme", "RMX3465": "Realme",
            "RMX3472": "Realme", "RMX3471": "Realme", "RMX3473": "Realme", "RMX3474": "Realme", "RMX3475": "Realme",
            "RMX3491": "Realme", "RMX3492": "Realme", "RMX3493": "Realme", "RMX3494": "Realme", "RMX3495": "Realme",
            "RMX3501": "Realme", "RMX3502": "Realme", "RMX3503": "Realme", "RMX3504": "Realme", "RMX3505": "Realme",
            "RMX3521": "Realme", "RMX3522": "Realme", "RMX3523": "Realme", "RMX3524": "Realme", "RMX3525": "Realme",
            "RMX3611": "Realme", "RMX3612": "Realme", "RMX3613": "Realme", "RMX3614": "Realme", "RMX3615": "Realme",
            "RMX3621": "Realme", "RMX3622": "Realme", "RMX3623": "Realme", "RMX3624": "Realme", "RMX3625": "Realme",
            "RMX3630": "Realme", "RMX3631": "Realme", "RMX3632": "Realme", "RMX3633": "Realme", "RMX3634": "Realme",
            "RMX3700": "Realme", "RMX3701": "Realme", "RMX3702": "Realme", "RMX3703": "Realme", "RMX3704": "Realme",
            "RMX3710": "Realme", "RMX3711": "Realme", "RMX3712": "Realme", "RMX3713": "Realme", "RMX3714": "Realme",
            "RMX3720": "Realme", "RMX3721": "Realme", "RMX3722": "Realme", "RMX3723": "Realme", "RMX3724": "Realme",
            "RMX3730": "Realme", "RMX3731": "Realme", "RMX3732": "Realme", "RMX3733": "Realme", "RMX3734": "Realme",
            "RMX3740": "Realme", "RMX3741": "Realme", "RMX3742": "Realme", "RMX3743": "Realme", "RMX3744": "Realme",
            "RMX3750": "Realme", "RMX3751": "Realme", "RMX3752": "Realme", "RMX3753": "Realme", "RMX3754": "Realme",
            
            # Realme GT/Pro Series (50 جهاز)
            "RMX2201": "Realme", "RMX2202": "Realme", "RMX2203": "Realme", "RMX2204": "Realme", "RMX2205": "Realme",
            "RMX3301": "Realme", "RMX3302": "Realme", "RMX3303": "Realme", "RMX3304": "Realme", "RMX3305": "Realme",
            "RMX3360": "Realme", "RMX3361": "Realme", "RMX3362": "Realme", "RMX3363": "Realme", "RMX3364": "Realme",
            "RMX3370": "Realme", "RMX3371": "Realme", "RMX3372": "Realme", "RMX3373": "Realme", "RMX3374": "Realme",
            "RMX3381": "Realme", "RMX3382": "Realme", "RMX3383": "Realme", "RMX3384": "Realme", "RMX3385": "Realme",
            "RMX3392": "Realme", "RMX3393": "Realme", "RMX3394": "Realme", "RMX3395": "Realme", "RMX3396": "Realme",
            "RMX3400": "Realme", "RMX3401": "Realme", "RMX3402": "Realme", "RMX3403": "Realme", "RMX3404": "Realme",
            "RMX3410": "Realme", "RMX3411": "Realme", "RMX3412": "Realme", "RMX3413": "Realme", "RMX3414": "Realme",
            "RMX3420": "Realme", "RMX3421": "Realme", "RMX3422": "Realme", "RMX3423": "Realme", "RMX3424": "Realme",
            "RMX3430": "Realme", "RMX3431": "Realme", "RMX3432": "Realme", "RMX3433": "Realme", "RMX3434": "Realme",
            
            # Tecno Spark/Camon Series (100 جهاز)
            "TECNO KD7": "Tecno", "TECNO KD7a": "Tecno", "TECNO KD7b": "Tecno", "TECNO KD7c": "Tecno", "TECNO KD7d": "Tecno",
            "TECNO KG7": "Tecno", "TECNO KG7a": "Tecno", "TECNO KG7b": "Tecno", "TECNO KG7c": "Tecno", "TECNO KG7d": "Tecno",
            "TECNO KH7": "Tecno", "TECNO KH7a": "Tecno", "TECNO KH7b": "Tecno", "TECNO KH7c": "Tecno", "TECNO KH7d": "Tecno",
            "TECNO KI8": "Tecno", "TECNO KI8a": "Tecno", "TECNO KI8b": "Tecno", "TECNO KI8c": "Tecno", "TECNO KI8d": "Tecno",
            "TECNO KJ7": "Tecno", "TECNO KJ7a": "Tecno", "TECNO KJ7b": "Tecno", "TECNO KJ7c": "Tecno", "TECNO KJ7d": "Tecno",
            "TECNO KK7": "Tecno", "TECNO KK7a": "Tecno", "TECNO KK7b": "Tecno", "TECNO KK7c": "Tecno", "TECNO KK7d": "Tecno",
            "TECNO KL7": "Tecno", "TECNO KL7a": "Tecno", "TECNO KL7b": "Tecno", "TECNO KL7c": "Tecno", "TECNO KL7d": "Tecno",
            "TECNO KM7": "Tecno", "TECNO KM7a": "Tecno", "TECNO KM7b": "Tecno", "TECNO KM7c": "Tecno", "TECNO KM7d": "Tecno",
            "TECNO KN7": "Tecno", "TECNO KN7a": "Tecno", "TECNO KN7b": "Tecno", "TECNO KN7c": "Tecno", "TECNO KN7d": "Tecno",
            "TECNO KP7": "Tecno", "TECNO KP7a": "Tecno", "TECNO KP7b": "Tecno", "TECNO KP7c": "Tecno", "TECNO KP7d": "Tecno",
            "TECNO KQ7": "Tecno", "TECNO KQ7a": "Tecno", "TECNO KQ7b": "Tecno", "TECNO KQ7c": "Tecno", "TECNO KQ7d": "Tecno",
            "TECNO KR7": "Tecno", "TECNO KR7a": "Tecno", "TECNO KR7b": "Tecno", "TECNO KR7c": "Tecno", "TECNO KR7d": "Tecno",
            "TECNO KS7": "Tecno", "TECNO KS7a": "Tecno", "TECNO KS7b": "Tecno", "TECNO KS7c": "Tecno", "TECNO KS7d": "Tecno",
            "TECNO KT7": "Tecno", "TECNO KT7a": "Tecno", "TECNO KT7b": "Tecno", "TECNO KT7c": "Tecno", "TECNO KT7d": "Tecno",
            "TECNO KU7": "Tecno", "TECNO KU7a": "Tecno", "TECNO KU7b": "Tecno", "TECNO KU7c": "Tecno", "TECNO KU7d": "Tecno",
            "TECNO KV7": "Tecno", "TECNO KV7a": "Tecno", "TECNO KV7b": "Tecno", "TECNO KV7c": "Tecno", "TECNO KV7d": "Tecno",
            "TECNO KW7": "Tecno", "TECNO KW7a": "Tecno", "TECNO KW7b": "Tecno", "TECNO KW7c": "Tecno", "TECNO KW7d": "Tecno",
            "TECNO KX7": "Tecno", "TECNO KX7a": "Tecno", "TECNO KX7b": "Tecno", "TECNO KX7c": "Tecno", "TECNO KX7d": "Tecno",
            "TECNO KY7": "Tecno", "TECNO KY7a": "Tecno", "TECNO KY7b": "Tecno", "TECNO KY7c": "Tecno", "TECNO KY7d": "Tecno",
            
            # Tecno Pova/Phantom Series (50 جهاز)
            "TECNO LC7": "Tecno", "TECNO LC7a": "Tecno", "TECNO LC7b": "Tecno", "TECNO LC7c": "Tecno", "TECNO LC7d": "Tecno",
            "TECNO LD7": "Tecno", "TECNO LD7a": "Tecno", "TECNO LD7b": "Tecno", "TECNO LD7c": "Tecno", "TECNO LD7d": "Tecno",
            "TECNO LE7": "Tecno", "TECNO LE7a": "Tecno", "TECNO LE7b": "Tecno", "TECNO LE7c": "Tecno", "TECNO LE7d": "Tecno",
            "TECNO LF7": "Tecno", "TECNO LF7a": "Tecno", "TECNO LF7b": "Tecno", "TECNO LF7c": "Tecno", "TECNO LF7d": "Tecno",
            "TECNO LG7": "Tecno", "TECNO LG7a": "Tecno", "TECNO LG7b": "Tecno", "TECNO LG7c": "Tecno", "TECNO LG7d": "Tecno",
            "TECNO LH7": "Tecno", "TECNO LH7a": "Tecno", "TECNO LH7b": "Tecno", "TECNO LH7c": "Tecno", "TECNO LH7d": "Tecno",
            "TECNO LI7": "Tecno", "TECNO LI7a": "Tecno", "TECNO LI7b": "Tecno", "TECNO LI7c": "Tecno", "TECNO LI7d": "Tecno",
            "TECNO LJ7": "Tecno", "TECNO LJ7a": "Tecno", "TECNO LJ7b": "Tecno", "TECNO LJ7c": "Tecno", "TECNO LJ7d": "Tecno",
            "TECNO LK7": "Tecno", "TECNO LK7a": "Tecno", "TECNO LK7b": "Tecno", "TECNO LK7c": "Tecno", "TECNO LK7d": "Tecno",
            "TECNO LL7": "Tecno", "TECNO LL7a": "Tecno", "TECNO LL7b": "Tecno", "TECNO LL7c": "Tecno", "TECNO LL7d": "Tecno",
            
            # Infinix Hot/Note Series (100 جهاز)
            "Infinix X6511": "Infinix", "Infinix X6512": "Infinix", "Infinix X6513": "Infinix", "Infinix X6514": "Infinix", "Infinix X6515": "Infinix",
            "Infinix X6520": "Infinix", "Infinix X6521": "Infinix", "Infinix X6522": "Infinix", "Infinix X6523": "Infinix", "Infinix X6524": "Infinix",
            "Infinix X6530": "Infinix", "Infinix X6531": "Infinix", "Infinix X6532": "Infinix", "Infinix X6533": "Infinix", "Infinix X6534": "Infinix",
            "Infinix X6540": "Infinix", "Infinix X6541": "Infinix", "Infinix X6542": "Infinix", "Infinix X6543": "Infinix", "Infinix X6544": "Infinix",
            "Infinix X6550": "Infinix", "Infinix X6551": "Infinix", "Infinix X6552": "Infinix", "Infinix X6553": "Infinix", "Infinix X6554": "Infinix",
            "Infinix X6560": "Infinix", "Infinix X6561": "Infinix", "Infinix X6562": "Infinix", "Infinix X6563": "Infinix", "Infinix X6564": "Infinix",
            "Infinix X6570": "Infinix", "Infinix X6571": "Infinix", "Infinix X6572": "Infinix", "Infinix X6573": "Infinix", "Infinix X6574": "Infinix",
            "Infinix X6580": "Infinix", "Infinix X6581": "Infinix", "Infinix X6582": "Infinix", "Infinix X6583": "Infinix", "Infinix X6584": "Infinix",
            "Infinix X6590": "Infinix", "Infinix X6591": "Infinix", "Infinix X6592": "Infinix", "Infinix X6593": "Infinix", "Infinix X6594": "Infinix",
            "Infinix X6600": "Infinix", "Infinix X6601": "Infinix", "Infinix X6602": "Infinix", "Infinix X6603": "Infinix", "Infinix X6604": "Infinix",
            "Infinix X6610": "Infinix", "Infinix X6611": "Infinix", "Infinix X6612": "Infinix", "Infinix X6613": "Infinix", "Infinix X6614": "Infinix",
            "Infinix X6620": "Infinix", "Infinix X6621": "Infinix", "Infinix X6622": "Infinix", "Infinix X6623": "Infinix", "Infinix X6624": "Infinix",
            "Infinix X6630": "Infinix", "Infinix X6631": "Infinix", "Infinix X6632": "Infinix", "Infinix X6633": "Infinix", "Infinix X6634": "Infinix",
            "Infinix X6640": "Infinix", "Infinix X6641": "Infinix", "Infinix X6642": "Infinix", "Infinix X6643": "Infinix", "Infinix X6644": "Infinix",
            "Infinix X6650": "Infinix", "Infinix X6651": "Infinix", "Infinix X6652": "Infinix", "Infinix X6653": "Infinix", "Infinix X6654": "Infinix",
            "Infinix X6660": "Infinix", "Infinix X6661": "Infinix", "Infinix X6662": "Infinix", "Infinix X6663": "Infinix", "Infinix X6664": "Infinix",
            "Infinix X6670": "Infinix", "Infinix X6671": "Infinix", "Infinix X6672": "Infinix", "Infinix X6673": "Infinix", "Infinix X6674": "Infinix",
            "Infinix X6680": "Infinix", "Infinix X6681": "Infinix", "Infinix X6682": "Infinix", "Infinix X6683": "Infinix", "Infinix X6684": "Infinix",
            
            # Infinix Zero/Smart Series (50 جهاز)
            "Infinix X6810": "Infinix", "Infinix X6811": "Infinix", "Infinix X6812": "Infinix", "Infinix X6813": "Infinix", "Infinix X6814": "Infinix",
            "Infinix X6815": "Infinix", "Infinix X6816": "Infinix", "Infinix X6817": "Infinix", "Infinix X6818": "Infinix", "Infinix X6819": "Infinix",
            "Infinix X6820": "Infinix", "Infinix X6821": "Infinix", "Infinix X6822": "Infinix", "Infinix X6823": "Infinix", "Infinix X6824": "Infinix",
            "Infinix X6830": "Infinix", "Infinix X6831": "Infinix", "Infinix X6832": "Infinix", "Infinix X6833": "Infinix", "Infinix X6834": "Infinix",
            "Infinix X6840": "Infinix", "Infinix X6841": "Infinix", "Infinix X6842": "Infinix", "Infinix X6843": "Infinix", "Infinix X6844": "Infinix",
            "Infinix X6850": "Infinix", "Infinix X6851": "Infinix", "Infinix X6852": "Infinix", "Infinix X6853": "Infinix", "Infinix X6854": "Infinix",
            "Infinix X6860": "Infinix", "Infinix X6861": "Infinix", "Infinix X6862": "Infinix", "Infinix X6863": "Infinix", "Infinix X6864": "Infinix",
            "Infinix X6870": "Infinix", "Infinix X6871": "Infinix", "Infinix X6872": "Infinix", "Infinix X6873": "Infinix", "Infinix X6874": "Infinix",
            "Infinix X6880": "Infinix", "Infinix X6881": "Infinix", "Infinix X6882": "Infinix", "Infinix X6883": "Infinix", "Infinix X6884": "Infinix",
            "Infinix X6890": "Infinix", "Infinix X6891": "Infinix", "Infinix X6892": "Infinix", "Infinix X6893": "Infinix", "Infinix X6894": "Infinix",
            
            # iPhone iOS Devices (50 جهاز)
            "iPhone12,1": "Apple", "iPhone12,3": "Apple", "iPhone12,5": "Apple", "iPhone12,8": "Apple", "iPhone13,1": "Apple",
            "iPhone13,2": "Apple", "iPhone13,3": "Apple", "iPhone13,4": "Apple", "iPhone14,2": "Apple", "iPhone14,3": "Apple",
            "iPhone14,4": "Apple", "iPhone14,5": "Apple", "iPhone14,6": "Apple", "iPhone14,7": "Apple", "iPhone14,8": "Apple",
            "iPhone15,2": "Apple", "iPhone15,3": "Apple", "iPhone15,4": "Apple", "iPhone15,5": "Apple", "iPhone15,6": "Apple",
            "iPhone16,1": "Apple", "iPhone16,2": "Apple", "iPhone16,3": "Apple", "iPhone16,4": "Apple", "iPhone16,5": "Apple",
            "iPhone17,1": "Apple", "iPhone17,2": "Apple", "iPhone17,3": "Apple", "iPhone17,4": "Apple", "iPhone17,5": "Apple",
            "iPhone18,1": "Apple", "iPhone18,2": "Apple", "iPhone18,3": "Apple", "iPhone18,4": "Apple", "iPhone18,5": "Apple",
            "iPhone19,1": "Apple", "iPhone19,2": "Apple", "iPhone19,3": "Apple", "iPhone19,4": "Apple", "iPhone19,5": "Apple",
            "iPhone20,1": "Apple", "iPhone20,2": "Apple", "iPhone20,3": "Apple", "iPhone20,4": "Apple", "iPhone20,5": "Apple",
            "iPhone21,1": "Apple", "iPhone21,2": "Apple", "iPhone21,3": "Apple", "iPhone21,4": "Apple", "iPhone21,5": "Apple",
            
            # Oppo A/F Series (50 جهاز)
            "CPH2325": "Oppo", "CPH2326": "Oppo", "CPH2327": "Oppo", "CPH2328": "Oppo", "CPH2329": "Oppo",
            "CPH2333": "Oppo", "CPH2334": "Oppo", "CPH2335": "Oppo", "CPH2336": "Oppo", "CPH2337": "Oppo",
            "CPH2341": "Oppo", "CPH2342": "Oppo", "CPH2343": "Oppo", "CPH2344": "Oppo", "CPH2345": "Oppo",
            "CPH2349": "Oppo", "CPH2351": "Oppo", "CPH2352": "Oppo", "CPH2353": "Oppo", "CPH2354": "Oppo",
            "CPH2357": "Oppo", "CPH2358": "Oppo", "CPH2359": "Oppo", "CPH2360": "Oppo", "CPH2361": "Oppo",
            "CPH2365": "Oppo", "CPH2366": "Oppo", "CPH2367": "Oppo", "CPH2368": "Oppo", "CPH2369": "Oppo",
            "CPH2371": "Oppo", "CPH2372": "Oppo", "CPH2373": "Oppo", "CPH2374": "Oppo", "CPH2375": "Oppo",
            "CPH2377": "Oppo", "CPH2378": "Oppo", "CPH2379": "Oppo", "CPH2380": "Oppo", "CPH2381": "Oppo",
            "CPH2385": "Oppo", "CPH2386": "Oppo", "CPH2387": "Oppo", "CPH2388": "Oppo", "CPH2389": "Oppo",
            "CPH2391": "Oppo", "CPH2392": "Oppo", "CPH2393": "Oppo", "CPH2394": "Oppo", "CPH2395": "Oppo",
            
            # Vivo Y/V Series (50 جهاز)
            "V2202": "Vivo", "V2203": "Vivo", "V2204": "Vivo", "V2205": "Vivo", "V2206": "Vivo",
            "V2207": "Vivo", "V2208": "Vivo", "V2209": "Vivo", "V2210": "Vivo", "V2211": "Vivo",
            "V2212": "Vivo", "V2213": "Vivo", "V2214": "Vivo", "V2215": "Vivo", "V2216": "Vivo",
            "V2217": "Vivo", "V2218": "Vivo", "V2219": "Vivo", "V2220": "Vivo", "V2221": "Vivo",
            "V2222": "Vivo", "V2223": "Vivo", "V2224": "Vivo", "V2225": "Vivo", "V2226": "Vivo",
            "V2227": "Vivo", "V2228": "Vivo", "V2229": "Vivo", "V2230": "Vivo", "V2231": "Vivo",
            "V2232": "Vivo", "V2233": "Vivo", "V2234": "Vivo", "V2235": "Vivo", "V2236": "Vivo",
            "V2237": "Vivo", "V2238": "Vivo", "V2239": "Vivo", "V2240": "Vivo", "V2241": "Vivo",
            "V2242": "Vivo", "V2243": "Vivo", "V2244": "Vivo", "V2245": "Vivo", "V2246": "Vivo",
            "V2247": "Vivo", "V2248": "Vivo", "V2249": "Vivo", "V2250": "Vivo", "V2251": "Vivo",
            
            # Huawei P/Nova Series (50 جهاز)
            "JAD-AL50": "Huawei", "JAD-AL60": "Huawei", "JAD-AL70": "Huawei", "JAD-AL80": "Huawei", "JAD-AL90": "Huawei",
            "BAC-AL00": "Huawei", "BAC-AL10": "Huawei", "BAC-AL20": "Huawei", "BAC-AL30": "Huawei", "BAC-AL40": "Huawei",
            "CDY-AN00": "Huawei", "CDY-AN10": "Huawei", "CDY-AN20": "Huawei", "CDY-AN30": "Huawei", "CDY-AN40": "Huawei",
            "AQM-AL00": "Huawei", "AQM-AL10": "Huawei", "AQM-AL20": "Huawei", "AQM-AL30": "Huawei", "AQM-AL40": "Huawei",
            "NAM-AL00": "Huawei", "NAM-AL10": "Huawei", "NAM-AL20": "Huawei", "NAM-AL30": "Huawei", "NAM-AL40": "Huawei",
            "OXF-AN00": "Huawei", "OXF-AN10": "Huawei", "OXF-AN20": "Huawei", "OXF-AN30": "Huawei", "OXF-AN40": "Huawei",
            "TET-AN00": "Huawei", "TET-AN10": "Huawei", "TET-AN20": "Huawei", "TET-AN30": "Huawei", "TET-AN40": "Huawei",
            "NOH-AN00": "Huawei", "NOH-AN10": "Huawei", "NOH-AN20": "Huawei", "NOH-AN30": "Huawei", "NOH-AN40": "Huawei",
            "ANA-AN00": "Huawei", "ANA-AN10": "Huawei", "ANA-AN20": "Huawei", "ANA-AN30": "Huawei", "ANA-AN40": "Huawei",
            "JSC-AN00": "Huawei", "JSC-AN10": "Huawei", "JSC-AN20": "Huawei", "JSC-AN30": "Huawei", "JSC-AN40": "Huawei",
            
            # Nokia G/X Series (50 جهاز)
            "Nokia G10": "Nokia", "Nokia G11": "Nokia", "Nokia G12": "Nokia", "Nokia G13": "Nokia", "Nokia G14": "Nokia",
            "Nokia G20": "Nokia", "Nokia G21": "Nokia", "Nokia G22": "Nokia", "Nokia G23": "Nokia", "Nokia G24": "Nokia",
            "Nokia G30": "Nokia", "Nokia G31": "Nokia", "Nokia G32": "Nokia", "Nokia G33": "Nokia", "Nokia G34": "Nokia",
            "Nokia G40": "Nokia", "Nokia G41": "Nokia", "Nokia G42": "Nokia", "Nokia G43": "Nokia", "Nokia G44": "Nokia",
            "Nokia G50": "Nokia", "Nokia G51": "Nokia", "Nokia G52": "Nokia", "Nokia G53": "Nokia", "Nokia G54": "Nokia",
            "Nokia X10": "Nokia", "Nokia X11": "Nokia", "Nokia X12": "Nokia", "Nokia X13": "Nokia", "Nokia X14": "Nokia",
            "Nokia X20": "Nokia", "Nokia X21": "Nokia", "Nokia X22": "Nokia", "Nokia X23": "Nokia", "Nokia X24": "Nokia",
            "Nokia X30": "Nokia", "Nokia X31": "Nokia", "Nokia X32": "Nokia", "Nokia X33": "Nokia", "Nokia X34": "Nokia",
            "Nokia X40": "Nokia", "Nokia X41": "Nokia", "Nokia X42": "Nokia", "Nokia X43": "Nokia", "Nokia X44": "Nokia",
            "Nokia X50": "Nokia", "Nokia X51": "Nokia", "Nokia X52": "Nokia", "Nokia X53": "Nokia", "Nokia X54": "Nokia",
        }

        self.android_builds = {
            "11": "RP1A.201005.001",
            "12": "SP1A.210812.016",
            "13": "TP1A.220624.014",
            "14": "UP1A.231005.007"
        }

        self.ttnet_versions = [
            "7db357f9 2025-12-03",
            "6fae3210 2024-10-11"
        ]

        self.quic_versions = [
            "88e06013 2025-11-26",
            "9cde112a 2024-09-18"
        ]

    def _generate_device(self):
        device = random.choice(list(self.devices.keys()))
        brand = self.devices[device]

        android = random.choice(list(self.android_builds.keys()))
        build = self.android_builds[android]

        locale = random.choice(["ar", "en"])
        ttnet = random.choice(self.ttnet_versions)
        quic = random.choice(self.quic_versions)

        ua = (
            f"com.zhiliaoapp.musically/2024300030 "
            f"(Linux; U; Android {android}; {locale}; {device}; "
            f"Build/{build}; "
            f"Cronet/TTNetVersion:{ttnet} "
            f"QuicVersion:{quic})"
        )

        return {
            "device_type": device,
            "device_brand": brand,
            "os_version": android,
            "language": locale,
            "build": build,
            "user_agent": ua,
            "ts": str(int(time.time())),
            "_rticket": str(int(time.time() * 1000)),
            "device_id": str(random.randint(10**18, 10**19 - 1))
        }

    def updateParams(self, params: dict):
        self._device = self._generate_device()
        d = self._device

        params.update({
            "device_id": d["device_id"],
            "device_type": d["device_type"],
            "device_brand": d["device_brand"],
            "os_version": d["os_version"],
            "ts": d["ts"],
            "_rticket": d["_rticket"]
        })
        return params

    def updateHeaders(self, headers: dict):
        if not hasattr(self, "_device"):
            self._device = self._generate_device()

        headers.update({
            "User-Agent": self._device["user_agent"]
        })
        return headers
