# ------------------------------------------------------------------
# Import libs and modules
# ------------------------------------------------------------------
import asyncio
import re

# ------------------------------------------------------------------
# Stable & base coins
# ------------------------------------------------------------------

STABLECOINS_USD = [
    "USDT",   # TETHER — أَكْبَر وَأَشْهَر STABLECOIN (~1$) :CONTENTREFERENCE[OAICITE:1]{INDEX=1}
    "USDC",   # USD COIN — مُسْتَقِرَّة وَمَدْعُومَة بِأَصُول (~1$) :CONTENTREFERENCE[OAICITE:2]{INDEX=2}
    "BUSD",   # BINANCE USD — مُسْتَقِرَّة (~1$) :CONTENTREFERENCE[OAICITE:3]{INDEX=3}
    "DAI",    # DAI — مُسْتَقِرَّة لامَرْكَزِيَّة (~1$) :CONTENTREFERENCE[OAICITE:4]{INDEX=4}
    "TUSD",   # TRUEUSD — مُسْتَقِرَّة (~1$) :CONTENTREFERENCE[OAICITE:5]{INDEX=5}
    "USDP",   # PAX DOLLAR — مُسْتَقِرَّة (~1$) :CONTENTREFERENCE[OAICITE:6]{INDEX=6}
    "PYUSD",  # PAYPAL USD — مُسْتَقِرَّة (~1$) :CONTENTREFERENCE[OAICITE:7]{INDEX=7}
    "USDE",   # ETHENA USDE — مُسْتَقِرَّة (~1$) حَسْب القِيمَة السُّوقِيَّة :CONTENTREFERENCE[OAICITE:8]{INDEX=8}
    "USD1",   # WORLD LIBERTY USD — مُسْتَقِرَّة (~1$) :CONTENTREFERENCE[OAICITE:9]{INDEX=9}
    "FDUSD",  # FIRST DIGITAL USD — مُسْتَقِرَّة (~1$) :CONTENTREFERENCE[OAICITE:10]{INDEX=10}
    "RLUSD",  # RIPPLE USD — مُسْتَقِرَّة مَدْعُومَة (~1$) :CONTENTREFERENCE[OAICITE:11]{INDEX=11}
    "USDD",   # TRON DAO STABLECOIN (~1$, قَد يَكُون ALGORITHMIC) :CONTENTREFERENCE[OAICITE:12]{INDEX=12}
    "OUSD",   # ORIGIN DOLLAR (~1$, DEFI STABLE) :CONTENTREFERENCE[OAICITE:13]{INDEX=13}
    "USDX",   # USDX — STABLECOIN خَاص مِن بَعْض الشَبَكَات (~1$) :CONTENTREFERENCE[OAICITE:14]{INDEX=14}
    "MUSD",   # MSTALE USD (~1$, DEFI) :CONTENTREFERENCE[OAICITE:15]{INDEX=15}
    "VAI",    # VAI — STABLECOIN (~1$) مِن بَعْض الشَبَكَات :CONTENTREFERENCE[OAICITE:16]{INDEX=16}
    "CUSDC",  # CELO USD COIN (~1$) — نُسْخَة USDC عَلَى CELO BLOCKCHAIN :CONTENTREFERENCE[OAICITE:17]{INDEX=17}
    "SEP20_USDX", # نُسْخَة USDX عَلَى بَعْض الشَبَكَات :CONTENTREFERENCE[OAICITE:18]{INDEX=18}
    # إِضَافَات قَد لا تَكُون كَبِيرَة فِي السَّيُولَة لَكِنَّهَا تُعَدُّ مُسْتَقِرَّة بِمُحَاوَلَة الحِفَاظ عَلَى ~1$
    "RSV",    # RESERVE (قَد يَكُون جُزْءًا مِن بِنْيَة STABLECOLLATERAL) :CONTENTREFERENCE[OAICITE:19]{INDEX=19}
    "SUSD",   # SYNTH SUSD — مُسْتَقِرَّة (~1$) فِي نُظُم السِّينثِتِيكْس :CONTENTREFERENCE[OAICITE:20]{INDEX=20}
    "CUSD",   # CELO DOLLAR (~1$, تِقْنِيَّة DEFI) :CONTENTREFERENCE[OAICITE:21]{INDEX=21}
    "USNFT",  # بَعْض مَشَارِيع NFT تَرْبِط قِيمَة رُمُوزَهَا بِ 1$ — ضَعِيف السَّيُولَة :CONTENTREFERENCE[OAICITE:22]{INDEX=22}
    "BIF",    # بَعْض نُسَخ مُسْتَقِرَّة مَحَلِّيَّة فِي سَلاَسِل بَعِيدَة (~1$) :CONTENTREFERENCE[OAICITE:23]{INDEX=23}
    # بَقِيَّة الرُّمُوز ذُكِرَت فِي المُجْتَمَعَات كَـ “STABLECOINS” لَكِنَّ كَثِيرًا مِنْهَا لَيْسَ مَدْعُومًا بِنَفْس الثَّبَات
    "MUSD",   # MSTALE USD — STABLECOIN DEFI (~1$) :CONTENTREFERENCE[OAICITE:24]{INDEX=24}
    "USN",    # USN — STABLECOIN مُرْتَبِط بِ NEAR ECOSYSTEM (~1$) :CONTENTREFERENCE[OAICITE:25]{INDEX=25}
    "USBZ",   # STABLECOIN تَجْرِيبِي فِي بَعْض السَّلاَسِل (~1$) :CONTENTREFERENCE[OAICITE:26]{INDEX=26}
    "NUSD",   # STABLECOIN عَلَى بَعْض الشَبَكَات (~1$) :CONTENTREFERENCE[OAICITE:27]{INDEX=27}
    "USDQ",   # STABLECOIN فِي بَعْض الْمَنَصَّات (~1$) :CONTENTREFERENCE[OAICITE:28]{INDEX=28}
    "USDH",   # USDH — STABLECOIN عَلَى بَعْض الشَبَكَات (~1$) :CONTENTREFERENCE[OAICITE:29]{INDEX=29}
    "SEURO",  # عَادَةً مُسْتَقِرَّة مُقَابِل اليُورُو لَكِنَّهَا قَد تُبْنَى لِلقِيمَة (~1$) :CONTENTREFERENCE[OAICITE:30]{INDEX=30}
    "FRAX",   # FRAX — HYBRID STABLE (~≈1$) :CONTENTREFERENCE[OAICITE:31]{INDEX=31}
    "FEI",    # FEI USD — STABLECOIN لَكِنَّهُ قَد يَخْرُج عَنِ الـ PEG أَحْيَانًا :CONTENTREFERENCE[OAICITE:32]{INDEX=32}
    "HUSD",   # HUSD — STABLECOIN مَدْعُوم فِي بَعْض الْمَنَصَّات (~1$) :CONTENTREFERENCE[OAICITE:33]{INDEX=33}
    "USK",    # USK — STABLECOIN فِي بَعْض الْبَرُوتُوكُولَات (~1$) :CONTENTREFERENCE[OAICITE:34]{INDEX=34}
    "RISD",   # مَشْرُوع STABLECOIN أَقَل شُعْبِيَّة (~1$) :CONTENTREFERENCE[OAICITE:35]{INDEX=35}
    "USX",    # STABLECOIN مُرَكَّب (~1$) :CONTENTREFERENCE[OAICITE:36]{INDEX=36}
    "SEURO",  # STABLECOIN مُقَابِل اليُورُو لَكِنْ يَظْهَر فِي قَوَائِم STABLE (~1$) :CONTENTREFERENCE[OAICITE:37]{INDEX=37}
    "XUSD",   # XUSD — STABLECROSS (~1$) :CONTENTREFERENCE[OAICITE:38]{INDEX=38}
    "LUSD",   # LIQUITY USD — STABLE (~1$) :CONTENTREFERENCE[OAICITE:39]{INDEX=39}
    "HUSD",   # HUOBI USD — STABLE عَبْر بَعْض الْمَنَصَّات (~1$) :CONTENTREFERENCE[OAICITE:40]{INDEX=40}
    "PYRUSD", # رَمْز STABLE مُسْتَخْرَج فِي بَعْض السَّلاَسِل (~1$) :CONTENTREFERENCE[OAICITE:41]{INDEX=41}
]

# ------------------------------------------------------------------
# fix intervales and return them to ms
# ------------------------------------------------------------------

def fix_interval(frame: str):
    """
    Convert a time frame string (e.g., '5min', '1h') into milliseconds.
    :param frame: String containing number and unit (ms, s, min, h, d, w, M)
    :return: Tuple (milliseconds, unit_string)
    """
    # Mapping of units to (milliseconds, short label)
    units = {
        "ms": [1, "ms"],              # milliseconds
        "s": [1000, "s"],             # seconds
        "min": [60000, "m"],          # minutes
        "m": [60000, "m"],          # minutes
        "h": [3600000, "h"],          # hours
        "d": [86400000, "d"],         # days
        "w": [604800000, "w"],        # weeks
        "M": [2592000000, "M"],       # months (approximate)
    }

    # Match pattern like "15min", "1h", "500ms"
    match = re.match(r"(\d+)(ms|s|min|m|h|d|w|M)", frame)
    if not match:
        raise ValueError("The time frame is not correct")

    # Extract numeric value and unit
    value, unit = match.groups()

    # Convert value to milliseconds and return with unit label
    return int(value) * units[unit][0], str(value) + str(units[unit][1])


# ------------------------------------------------------------------
# create a multiple queue of messages by `asyncio.queue`
# ------------------------------------------------------------------

class QueueStream:
    def __init__(self):
        self.subscribes: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue : 
        q = asyncio.Queue()
        self.subscribes.append(q)
        return q

    def unsuscribe(self,sub) -> bool :
        if sub in self.subscribes:
            self.subscribes.remove(sub)
            return True
        else:
            return False
        
    async def put(self,msg:...):
        for sub in self.subscribes:
            await sub.put(msg)