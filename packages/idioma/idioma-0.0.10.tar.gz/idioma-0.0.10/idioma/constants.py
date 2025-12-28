DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

DEFAULT_CLIENT_SERVICE_URLS = (
    'translate.google.com',
)

DEFAULT_FALLBACK_SERVICE_URLS = (
    'translate.googleapis.com',
)

DEFAULT_SERVICE_URLS = (
    'translate.google.ac', 'translate.google.ad', 'translate.google.ae',
    'translate.google.al', 'translate.google.am', 'translate.google.as',
    'translate.google.at', 'translate.google.az', 'translate.google.ba',
    'translate.google.be', 'translate.google.bf', 'translate.google.bg',
    'translate.google.bi', 'translate.google.bj', 'translate.google.bs',
    'translate.google.bt', 'translate.google.by', 'translate.google.ca',
    'translate.google.cat', 'translate.google.cc', 'translate.google.cd',
    'translate.google.cf', 'translate.google.cg', 'translate.google.ch',
    'translate.google.ci', 'translate.google.cl', 'translate.google.cm',
    'translate.google.cn', 'translate.google.co.ao', 'translate.google.co.bw',
    'translate.google.co.ck', 'translate.google.co.cr',
    'translate.google.co.id',
    'translate.google.co.il', 'translate.google.co.in',
    'translate.google.co.jp',
    'translate.google.co.ke', 'translate.google.co.kr',
    'translate.google.co.ls',
    'translate.google.co.ma', 'translate.google.co.mz',
    'translate.google.co.nz',
    'translate.google.co.th', 'translate.google.co.tz',
    'translate.google.co.ug',
    'translate.google.co.uk', 'translate.google.co.uz',
    'translate.google.co.ve',
    'translate.google.co.vi', 'translate.google.co.za',
    'translate.google.co.zm',
    'translate.google.co.zw', 'translate.google.com.af',
    'translate.google.com.ag',
    'translate.google.com.ai', 'translate.google.com.ar',
    'translate.google.com.au',
    'translate.google.com.bd', 'translate.google.com.bh',
    'translate.google.com.bn',
    'translate.google.com.bo', 'translate.google.com.br',
    'translate.google.com.bz',
    'translate.google.com.co', 'translate.google.com.cu',
    'translate.google.com.cy',
    'translate.google.com.do', 'translate.google.com.ec',
    'translate.google.com.eg',
    'translate.google.com.et', 'translate.google.com.fj',
    'translate.google.com.gh',
    'translate.google.com.gi', 'translate.google.com.gt',
    'translate.google.com.hk',
    'translate.google.com.jm', 'translate.google.com.kh',
    'translate.google.com.kw',
    'translate.google.com.lb', 'translate.google.com.ly',
    'translate.google.com.mm',
    'translate.google.com.mt', 'translate.google.com.mx',
    'translate.google.com.my',
    'translate.google.com.na', 'translate.google.com.ng',
    'translate.google.com.ni',
    'translate.google.com.np', 'translate.google.com.om',
    'translate.google.com.pa',
    'translate.google.com.pe', 'translate.google.com.pg',
    'translate.google.com.ph',
    'translate.google.com.pk', 'translate.google.com.pr',
    'translate.google.com.py',
    'translate.google.com.qa', 'translate.google.com.sa',
    'translate.google.com.sb',
    'translate.google.com.sg', 'translate.google.com.sl',
    'translate.google.com.sv',
    'translate.google.com.tj', 'translate.google.com.tr',
    'translate.google.com.tw',
    'translate.google.com.ua', 'translate.google.com.uy',
    'translate.google.com.vc',
    'translate.google.com.vn', 'translate.google.com', 'translate.google.cv',
    'translate.google.cz', 'translate.google.de', 'translate.google.dj',
    'translate.google.dk', 'translate.google.dm', 'translate.google.dz',
    'translate.google.ee', 'translate.google.es', 'translate.google.eu',
    'translate.google.fi', 'translate.google.fm', 'translate.google.fr',
    'translate.google.ga', 'translate.google.ge', 'translate.google.gf',
    'translate.google.gg', 'translate.google.gl', 'translate.google.gm',
    'translate.google.gp', 'translate.google.gr', 'translate.google.gy',
    'translate.google.hn', 'translate.google.hr', 'translate.google.ht',
    'translate.google.hu', 'translate.google.ie', 'translate.google.im',
    'translate.google.io', 'translate.google.iq', 'translate.google.is',
    'translate.google.it', 'translate.google.je', 'translate.google.jo',
    'translate.google.kg', 'translate.google.ki', 'translate.google.kz',
    'translate.google.la', 'translate.google.li', 'translate.google.lk',
    'translate.google.lt', 'translate.google.lu', 'translate.google.lv',
    'translate.google.md', 'translate.google.me', 'translate.google.mg',
    'translate.google.mk', 'translate.google.ml', 'translate.google.mn',
    'translate.google.ms', 'translate.google.mu', 'translate.google.mv',
    'translate.google.mw', 'translate.google.ne', 'translate.google.nf',
    'translate.google.nl', 'translate.google.no', 'translate.google.nr',
    'translate.google.nu', 'translate.google.pl', 'translate.google.pn',
    'translate.google.ps', 'translate.google.pt', 'translate.google.ro',
    'translate.google.rs', 'translate.google.ru', 'translate.google.rw',
    'translate.google.sc', 'translate.google.se', 'translate.google.sh',
    'translate.google.si', 'translate.google.sk', 'translate.google.sm',
    'translate.google.sn', 'translate.google.so', 'translate.google.sr',
    'translate.google.st', 'translate.google.td', 'translate.google.tg',
    'translate.google.tk', 'translate.google.tl', 'translate.google.tm',
    'translate.google.tn', 'translate.google.to', 'translate.google.tt',
    'translate.google.us', 'translate.google.vg', 'translate.google.vu',
    'translate.google.ws')

SPECIAL_CASES = {
    'ee': 'et',
}

LANGUAGES = {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'he': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'or': 'odia',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'ug': 'uyghur',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu',
}

PRIMARY_COUNTRY = {
    'af': 'ZA',  # Afrikaans - South Africa
    'sq': 'AL',  # Albanian - Albania
    'am': 'ET',  # Amharic - Ethiopia
    'ar': 'SA',  # Arabic - Saudi Arabia
    'hy': 'AM',  # Armenian - Armenia
    'az': 'AZ',  # Azerbaijani - Azerbaijan
    'eu': 'ES',  # Basque - Spain
    'be': 'BY',  # Belarusian - Belarus
    'bn': 'BD',  # Bengali - Bangladesh
    'bs': 'BA',  # Bosnian - Bosnia and Herzegovina
    'bg': 'BG',  # Bulgarian - Bulgaria
    'ca': 'ES',  # Catalan - Spain
    'ceb': 'PH',  # Cebuano - Philippines
    'ny': 'MW',  # Chichewa - Malawi
    'zh-cn': 'CN',  # Chinese (Simplified) - China
    'zh-tw': 'TW',  # Chinese (Traditional) - Taiwan
    'co': 'FR',  # Corsican - France
    'hr': 'HR',  # Croatian - Croatia
    'cs': 'CZ',  # Czech - Czech Republic
    'da': 'DK',  # Danish - Denmark
    'nl': 'NL',  # Dutch - Netherlands
    'en': 'US',  # English - United States
    'eo': None,  # Esperanto - No primary country
    'et': 'EE',  # Estonian - Estonia
    'tl': 'PH',  # Filipino - Philippines
    'fi': 'FI',  # Finnish - Finland
    'fr': 'FR',  # French - France
    'fy': 'NL',  # Frisian - Netherlands
    'gl': 'ES',  # Galician - Spain
    'ka': 'GE',  # Georgian - Georgia
    'de': 'DE',  # German - Germany
    'el': 'GR',  # Greek - Greece
    'gu': 'IN',  # Gujarati - India
    'ht': 'HT',  # Haitian Creole - Haiti
    'ha': 'NG',  # Hausa - Nigeria
    'haw': 'US',  # Hawaiian - United States (Hawaii)
    'iw': 'IL',  # Hebrew - Israel
    'he': 'IL',  # Hebrew - Israel
    'hi': 'IN',  # Hindi - India
    'hmn': 'LA',  # Hmong - Laos
    'hu': 'HU',  # Hungarian - Hungary
    'is': 'IS',  # Icelandic - Iceland
    'ig': 'NG',  # Igbo - Nigeria
    'id': 'ID',  # Indonesian - Indonesia
    'ga': 'IE',  # Irish - Ireland
    'it': 'IT',  # Italian - Italy
    'ja': 'JP',  # Japanese - Japan
    'jw': 'ID',  # Javanese - Indonesia
    'kn': 'IN',  # Kannada - India
    'kk': 'KZ',  # Kazakh - Kazakhstan
    'km': 'KH',  # Khmer - Cambodia
    'ko': 'KR',  # Korean - South Korea
    'ku': 'IQ',  # Kurdish (Kurmanji) - Iraq
    'ky': 'KG',  # Kyrgyz - Kyrgyzstan
    'lo': 'LA',  # Lao - Laos
    'la': 'VA',  # Latin - Vatican City
    'lv': 'LV',  # Latvian - Latvia
    'lt': 'LT',  # Lithuanian - Lithuania
    'lb': 'LU',  # Luxembourgish - Luxembourg
    'mk': 'MK',  # Macedonian - North Macedonia
    'mg': 'MG',  # Malagasy - Madagascar
    'ms': 'MY',  # Malay - Malaysia
    'ml': 'IN',  # Malayalam - India
    'mt': 'MT',  # Maltese - Malta
    'mi': 'NZ',  # Maori - New Zealand
    'mr': 'IN',  # Marathi - India
    'mn': 'MN',  # Mongolian - Mongolia
    'my': 'MM',  # Myanmar (Burmese) - Myanmar
    'ne': 'NP',  # Nepali - Nepal
    'no': 'NO',  # Norwegian - Norway
    'or': 'IN',  # Odia - India
    'ps': 'AF',  # Pashto - Afghanistan
    'fa': 'IR',  # Persian - Iran
    'pl': 'PL',  # Polish - Poland
    'pt': 'BR',  # Portuguese - Brazil
    'pa': 'IN',  # Punjabi - India
    'ro': 'RO',  # Romanian - Romania
    'ru': 'RU',  # Russian - Russia
    'sm': 'WS',  # Samoan - Samoa
    'gd': 'GB',  # Scots Gaelic - United Kingdom (Scotland)
    'sr': 'RS',  # Serbian - Serbia
    'st': 'LS',  # Sesotho - Lesotho
    'sn': 'ZW',  # Shona - Zimbabwe
    'sd': 'PK',  # Sindhi - Pakistan
    'si': 'LK',  # Sinhala - Sri Lanka
    'sk': 'SK',  # Slovak - Slovakia
    'sl': 'SI',  # Slovenian - Slovenia
    'so': 'SO',  # Somali - Somalia
    'es': 'ES',  # Spanish - Spain
    'su': 'ID',  # Sundanese - Indonesia
    'sw': 'KE',  # Swahili - Kenya
    'sv': 'SE',  # Swedish - Sweden
    'tg': 'TJ',  # Tajik - Tajikistan
    'ta': 'IN',  # Tamil - India
    'te': 'IN',  # Telugu - India
    'th': 'TH',  # Thai - Thailand
    'tr': 'TR',  # Turkish - Turkey
    'uk': 'UA',  # Ukrainian - Ukraine
    'ur': 'PK',  # Urdu - Pakistan
    'ug': 'CN',  # Uyghur - China
    'uz': 'UZ',  # Uzbek - Uzbekistan
    'vi': 'VN',  # Vietnamese - Vietnam
    'cy': 'GB',  # Welsh - United Kingdom (Wales)
    'xh': 'ZA',  # Xhosa - South Africa
    'yi': None,  # Yiddish - No primary country
    'yo': 'NG',  # Yoruba - Nigeria
    'zu': 'ZA'  # Zulu - South Africa
}

LANGCODES = dict(map(reversed, LANGUAGES.items()))
DEFAULT_RAISE_EXCEPTION = False
DUMMY_DATA = [[["", None, None, 0]], None, "en", None,
              None, None, 1, None, [["en"], None, [1], ["en"]]]
