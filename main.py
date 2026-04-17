import os
import json
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from contextlib import asynccontextmanager

from curl_cffi.requests import AsyncSession
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SGT = ZoneInfo("Asia/Singapore")
ACTIVITY_ID = "YLONatwvqJfikKOmB5N9U"
BASE_URL = "https://activesg.gov.sg/api/trpc/schedule.listAvailable"
CONCURRENCY = 12
REFRESH_INTERVAL_MINUTES = 10

VENUES = [
    {"id": "d1LKU6XBvvhYccrUbpvqF", "name": "Admiralty Primary School Hall", "address": "11 Woodlands Circle", "type": "DUS"},
    {"id": "7bg9Z7WtSvoLMpgxWGjTs", "name": "Ahmad Ibrahim Secondary School Hall", "address": "751 Yishun Avenue 7", "type": "DUS"},
    {"id": "1H7SSWewlpNYu9cmoXPn2", "name": "Anchor Green Primary School Hall", "address": "31 Anchorvale Drive", "type": "DUS"},
    {"id": "zmOAv5FPai8EuPpHBvmi2", "name": "Ang Mo Kio Primary School Hall", "address": "20 Ang Mo Kio Avenue 3", "type": "DUS"},
    {"id": "9zE1soYz9gKof24042MyX", "name": "Beacon Primary School Hall", "address": "36 Bukit Panjang Ring Road", "type": "DUS"},
    {"id": "063L3ZyshZUjdw8xxgUpK", "name": "Beatty Secondary School Hall", "address": "1 Toa Payoh North", "type": "DUS"},
    {"id": "PgIZQ3UXAZU2wnH1dcFc6", "name": "Bedok Green Primary School Hall", "address": "1 Bedok South Avenue 2", "type": "DUS"},
    {"id": "5TIAp1oDwn8B1grH4hoyi", "name": "Bedok South Secondary School Hall", "address": "1 Jalan Langgar Bedok", "type": "DUS"},
    {"id": "niow1h8bvTWqvEjuooABc", "name": "Bendemeer Primary School Hall", "address": "91 Bendemeer Road", "type": "DUS"},
    {"id": "t9aTrkSIyYRuRo1Ucd3Xv", "name": "Bendemeer Secondary School Hall", "address": "1 St. Wilfred Road", "type": "DUS"},
    {"id": "GdiZXcMkIKELrCkd90qBP", "name": "Bishan Clubhouse", "address": "3 Bishan Street 14", "type": "SRC"},
    {"id": "LpiaS3dnMUXa39CrtTm9w", "name": "Bishan Sport Hall", "address": "5 Bishan Street 14", "type": "SRC"},
    {"id": "wfqNsxOYnCEBQ0kk5ENjq", "name": "Blangah Rise Primary School Hall", "address": "91 Telok Blangah Heights", "type": "DUS"},
    {"id": "eqzbNMrlMOTaSzDvEF05p", "name": "Boon Lay Secondary School Hall", "address": "11 Jurong West Street 65", "type": "DUS"},
    {"id": "DS2Y95tMEksERLSJfBSBz", "name": "Bowen Secondary School Hall", "address": "2 Lorong Napiri", "type": "DUS"},
    {"id": "wpSdUk0uledoInNjK3Kaw", "name": "Bukit Canberra Sport Hall", "address": "21 Canberra Link", "type": "SRC"},
    {"id": "WYfbYK8b8mvlTx7iiCIJp", "name": "Bukit Gombak Sport Hall", "address": "810 Bukit Batok West Avenue 5", "type": "SRC"},
    {"id": "ZReBsLW8QTkzuFD1vyFkX", "name": "Bukit Panjang Government High School Hall", "address": "7 Choa Chu Kang Avenue 4", "type": "DUS"},
    {"id": "AkB5NpkMVL7HCmB6DLppX", "name": "Bukit Panjang Primary School Hall", "address": "109 Cashew Road", "type": "DUS"},
    {"id": "jTPGVh1bbKq70nuvjqvR4", "name": "Bukit Timah Primary School Hall", "address": "111 Lorong Kismis", "type": "DUS"},
    {"id": "rzOCKx6ezbKcGKQWjSHlN", "name": "Bukit View Secondary School Hall", "address": "16 Bukit Batok Street 21", "type": "DUS"},
    {"id": "EhVMAAEMSQPdrpKw4yIaD", "name": "Canberra Primary School Hall", "address": "21 Admiralty Drive", "type": "DUS"},
    {"id": "2IUHiBUcoNimux7lmUt9h", "name": "Canberra Secondary School Hall", "address": "51 Sembawang Drive", "type": "DUS"},
    {"id": "hy4Hsg4gHPM3y42YHZyL6", "name": "Cantonment Primary School Hall", "address": "1 Cantonment Close", "type": "DUS"},
    {"id": "Us0MaNzoJ6XwGGq2PY98h", "name": "Casuarina Primary School Hall", "address": "30 Pasir Ris Street 41", "type": "DUS"},
    {"id": "AxDehUxuPrlYSmWBAR3lc", "name": "Cedar Primary School Hall", "address": "15 Cedar Avenue", "type": "DUS"},
    {"id": "IftVzycvPKY3HYuyLhOYe", "name": "Changkat Changi Secondary School Hall", "address": "23 Simei Street 3", "type": "DUS"},
    {"id": "I5qnyIxLbwQYfZ1D6487A", "name": "Changkat Primary School Hall", "address": "11 Simei Street 3", "type": "DUS"},
    {"id": "jP33ehBA3lDjp34Lq7dEd", "name": "Choa Chu Kang Sport Hall", "address": "1 Choa Chu Kang Street 53", "type": "SRC"},
    {"id": "liiH4YYsu0f3tlzWgC8I7", "name": "Christ Church Secondary School Hall", "address": "20 Woodlands Drive 17", "type": "DUS"},
    {"id": "bbyJ7E5oIPvgA5J7jYNjN", "name": "Chua Chu Kang Secondary School Hall", "address": "31 Teck Whye Crescent", "type": "DUS"},
    {"id": "nqi0R5foGPNhRJnVhbzlS", "name": "Clementi Primary School Hall", "address": "8 Clementi Avenue 3", "type": "DUS"},
    {"id": "fU1NDT1wfMMSGcB2GUPst", "name": "Clementi Sport Hall", "address": "518 Clementi Avenue 3", "type": "SRC"},
    {"id": "b3M3CTm1v4G0rpXK16X6t", "name": "Clementi Town Secondary School Hall", "address": "10 Clementi Avenue 3", "type": "DUS"},
    {"id": "u0aa06DkimDKERs98iY4J", "name": "Concord Primary School Hall", "address": "3 Choa Chu Kang Avenue 4", "type": "DUS"},
    {"id": "S1a100KWjvY7ofteyu0fV", "name": "Crescent Girls' School Hall", "address": "357 Tanglin Road", "type": "DUS"},
    {"id": "CQT4YYAq7wPkHGOuziyvg", "name": "Dazhong Primary School Hall", "address": "35 Bukit Batok Street 31", "type": "DUS"},
    {"id": "a3jznoZlsfyJrl43Tbnog", "name": "Delta Sport Hall", "address": "900 Tiong Bahru Road", "type": "SRC"},
    {"id": "hK0lleSHLFmTTDEfLt627", "name": "Deyi Secondary School Hall", "address": "1 Ang Mo Kio Street 42", "type": "DUS"},
    {"id": "nTNUP5QWvkDFpWtbfue6R", "name": "Dunman High School Hall", "address": "10 Tanjong Rhu Road", "type": "DUS"},
    {"id": "5r8EUJDjosfkaF8qqezOU", "name": "East Spring Primary School Hall", "address": "31 Tampines Street 33", "type": "DUS"},
    {"id": "N2yRAN8hyCnQcEnZzPOOY", "name": "Edgefield Primary School Hall", "address": "41 Edgefield Plains", "type": "DUS"},
    {"id": "7z00lbn6Rqy3w4C46HLYf", "name": "Edgefield Secondary School Hall", "address": "36 Punggol Field", "type": "DUS"},
    {"id": "Lz8NJiVKy0IDBs7afQnwj", "name": "Elias Park Primary School Hall", "address": "11 Pasir Ris Street 52", "type": "DUS"},
    {"id": "PoDnMDAYOJPodLWuv8Gxp", "name": "Endeavour Primary School Hall", "address": "10 Admiralty Link", "type": "DUS"},
    {"id": "S37sThPNt4FIIVVnf4rZF", "name": "Eunoia Junior College Hall", "address": "2 Sin Ming Place", "type": "DUS"},
    {"id": "mZ647YYImQ69PjoUNwR9C", "name": "Evergreen Primary School Hall", "address": "31 Woodlands Circle", "type": "DUS"},
    {"id": "WHa3066PaItBKX5ZwvueP", "name": "Farrer Park Primary School Hall", "address": "2 Farrer Park Road", "type": "DUS"},
    {"id": "O0tvwIrzxdBw1jcWmjp7q", "name": "Fengshan Primary School Hall", "address": "307 Bedok North Road", "type": "DUS"},
    {"id": "1KTMl9mhDvBeR0xRoHA9a", "name": "Fern Green Primary School Hall", "address": "70 Fernvale Link", "type": "DUS"},
    {"id": "shhtJZhaNDmhhGmyznREq", "name": "First Toa Payoh Primary School Hall", "address": "7 Lorong 8 Toa Payoh", "type": "DUS"},
    {"id": "XD2qpAuXSv8yrvMgKxczH", "name": "Frontier Primary School Hall", "address": "20 Jurong West Street 61", "type": "DUS"},
    {"id": "K7yb8O3NAWIWjXRBfl911", "name": "Fuhua Secondary School Hall", "address": "5 Jurong West Street 41", "type": "DUS"},
    {"id": "XsuSgDDoI8aKGowjzD0aS", "name": "Gan Eng Seng Primary School Hall", "address": "100 Redhill Close", "type": "DUS"},
    {"id": "pSb2HypfjPg8TmbY3U1vZ", "name": "Gongshang Primary School Hall", "address": "1 Tampines Street 42", "type": "DUS"},
    {"id": "Qt0Viuhpm748aQSdYC2jU", "name": "Greendale Primary School Hall", "address": "50 Edgedale Plains", "type": "DUS"},
    {"id": "9SZuSjvI6tyRvV76JPvq6", "name": "Greenridge Secondary School Hall", "address": "31 Gangsa Road", "type": "DUS"},
    {"id": "cPasd6r3T4OmhU8tYyocx", "name": "Greenwood Primary School Hall", "address": "11 Woodlands Drive 62", "type": "DUS"},
    {"id": "2vQVXKogKPojlagjzNxeX", "name": "Heartbeat @ Bedok ActiveSG Sport Hall", "address": "11 Bedok North Street 1", "type": "SRC"},
    {"id": "C8ukgfnOznV5fC203rB2A", "name": "Henry Park Primary School Hall", "address": "1 Holland Grove Road", "type": "DUS"},
    {"id": "hzrR3kvk8qcNWKRxkvUkb", "name": "Hougang Secondary School Hall", "address": "2 Hougang Street 93", "type": "DUS"},
    {"id": "7Gkwfqhh4iShnyRIZBs2W", "name": "Hua Yi Secondary School Hall", "address": "60 Jurong West Street 42", "type": "DUS"},
    {"id": "AJ13GOe1e0Tg6RCjS2ZcM", "name": "Innova Primary School Hall", "address": "80 Woodlands Drive 17", "type": "DUS"},
    {"id": "BZAkV6o3rmqHMFgGgfPQa", "name": "Jiemin Primary School Hall", "address": "2 Yishun Street 71", "type": "DUS"},
    {"id": "zrRY1f5GItJnx6rWeK0IL", "name": "Jing Shan Primary School Hall", "address": "5 Ang Mo Kio Street 52", "type": "DUS"},
    {"id": "oN4FezUSD6tOmATK2CLaY", "name": "Junyuan Secondary School Hall", "address": "11 Tampines Street 84", "type": "DUS"},
    {"id": "vrkrAMmmGiSIaj7FEMcjx", "name": "Jurong East Sport Hall", "address": "21 Jurong East Street 31", "type": "SRC"},
    {"id": "IzBcR11fYSeByAUYgp5v6", "name": "Jurong Secondary School Hall", "address": "31 Yuan Ching Road", "type": "DUS"},
    {"id": "iQYIzofibpiGOEHMDZTXr", "name": "Jurong West Sport Hall", "address": "20 Jurong West Street 93", "type": "SRC"},
    {"id": "nmnGRpU0164zksMKaYrlH", "name": "Jurongville Secondary School Hall", "address": "202 Jurong East Avenue 1", "type": "DUS"},
    {"id": "kiyKUyVTnvoQTNWVFT4LH", "name": "Keming Primary School Hall", "address": "90 Bukit Batok East Avenue 6", "type": "DUS"},
    {"id": "kOnZuc48plvOq7IthMY2U", "name": "Kuo Chuan Presbyterian Primary School Hall", "address": "8 Bishan Street 13", "type": "DUS"},
    {"id": "AYfq2dsBbG3q71PK4nOEf", "name": "Lakeside Primary School Hall", "address": "161 Corporation Walk", "type": "DUS"},
    {"id": "mkiyzkeIi9xLpa7bVT5lV", "name": "Lianhua Primary School Hall", "address": "2 Bukit Batok Street 52", "type": "DUS"},
    {"id": "wkP0xH10TgRzCtxYN6f0S", "name": "Loyang View Secondary School Hall", "address": "12 Pasir Ris Street 11", "type": "DUS"},
    {"id": "Vpp2LXTBGVEWe6rgRDeve", "name": "Marsiling Primary School Hall", "address": "31 Woodlands Centre Road", "type": "DUS"},
    {"id": "Jrqeq5n0xbmdniQTcUplu", "name": "Marsiling Secondary School Hall", "address": "12 Marsiling Road", "type": "DUS"},
    {"id": "wSigiNiu1ozPZPM74lovp", "name": "Mayflower Secondary School Hall", "address": "2 Ang Mo Kio Street 21", "type": "DUS"},
    {"id": "NZcfdXsDnvyDZyodX2QaN", "name": "Meridian Primary School Hall", "address": "20 Pasir Ris Street 71", "type": "DUS"},
    {"id": "UAeAo7CCXS8viX5UnapTG", "name": "Meridian Secondary School Hall", "address": "31 Pasir Ris Street 51", "type": "DUS"},
    {"id": "kEBJKrx1USi4BvQxwMMHs", "name": "MOE (Evans) Sport Hall", "address": "21 Evans Road", "type": "SRC"},
    {"id": "Ub9LlzrSwKKNuhDglA0mU", "name": "Naval Base Secondary School Hall", "address": "901 Yishun Ring Road", "type": "DUS"},
    {"id": "GvuqOzOuzHQclAIeVHGCj", "name": "New Town Secondary School Hall", "address": "1020 Dover Road", "type": "DUS"},
    {"id": "MxokJ4BUcmoTlHPmUyFIx", "name": "North View Primary School Hall", "address": "210 Yishun Avenue 6", "type": "DUS"},
    {"id": "1sPQYX9V5NpYIfQSIvv6r", "name": "North Vista Primary School Hall", "address": "20 Compassvale Link", "type": "DUS"},
    {"id": "5ozMPpwgFvTb6jWaHhUwU", "name": "North Vista Secondary School Hall", "address": "11 Rivervale Link", "type": "DUS"},
    {"id": "bJkfBR1JpkU2Tz42uBJ7d", "name": "Northland Primary School Hall", "address": "15 Yishun Avenue 4", "type": "DUS"},
    {"id": "jv4V4CoTt4zuzCwYh3rRX", "name": "Northland Secondary School Hall", "address": "3 Yishun Street 22", "type": "DUS"},
    {"id": "TJB5eRejKVw8Iz1xMKjXP", "name": "Northoaks Primary School Hall", "address": "61 Sembawang Drive", "type": "DUS"},
    {"id": "osTnHplt9s99S9CGfprMX", "name": "Oasis Primary School Hall", "address": "71 Edgefield Plains", "type": "DUS"},
    {"id": "nqBpgnMrPN8u5LLfvyN2T", "name": "Our Tampines Hub - Community Auditorium", "address": "1 Tampines Walk", "type": "SRC"},
    {"id": "QAG9aSOv28TZ8lnurRqtA", "name": "Park View Primary School Hall", "address": "60 Pasir Ris Drive 1", "type": "DUS"},
    {"id": "92y0epudFNS0wHbSdYZSq", "name": "Pasir Ris Crest Secondary School Hall", "address": "11 Pasir Ris Street 41", "type": "DUS"},
    {"id": "Zgl7HQ7kn1abhxuCN7VFp", "name": "Pasir Ris Secondary School Hall", "address": "390 Tampines Street 21", "type": "DUS"},
    {"id": "TbIGpVpUxV6SZrxp9tPkB", "name": "Pasir Ris Sport Hall", "address": "120 Pasir Ris Central", "type": "SRC"},
    {"id": "V0cHEdFG8rbptwBMI8yGd", "name": "Peicai Secondary School Hall", "address": "10 Serangoon Avenue 4", "type": "DUS"},
    {"id": "94bmiFQAdLVfla9P4Slf2", "name": "Peirce Secondary School Hall", "address": "10 Sin Ming Walk", "type": "DUS"},
    {"id": "1bPUPjQLm6sCem8ewVJPW", "name": "Peiying Primary School Hall", "address": "651 Yishun Ring Road", "type": "DUS"},
    {"id": "Fe4pq9qbZZkwHPYyWqRN8", "name": "Poi Ching School Hall", "address": "21 Tampines Street 71", "type": "DUS"},
    {"id": "tckWqoLb1K2UBagZpBqB4", "name": "Punggol Secondary School Hall", "address": "51 Edgefield Plains", "type": "DUS"},
    {"id": "fOf6EXbnJolxlMpVu8rqV", "name": "Punggol View Primary School Hall", "address": "9 Punggol Place", "type": "DUS"},
    {"id": "VZMrUxulVPVG24gl7Xrnx", "name": "Qifa Primary School Hall", "address": "50 West Coast Avenue", "type": "DUS"},
    {"id": "PQV0sZtKKATgkm0mE7sj4", "name": "Qihua Primary School Hall", "address": "5 Woodlands Street 81", "type": "DUS"},
    {"id": "leFoNGWfouhGjXYbR27EH", "name": "Queenstown Primary School Hall", "address": "310 Margaret Drive", "type": "DUS"},
    {"id": "5OuHTQesKmt5vJ0hZ0gRE", "name": "Queensway Secondary School Hall", "address": "2A Margaret Drive", "type": "DUS"},
    {"id": "ELqczOCMqgGTO68hTrVD0", "name": "Radin Mas Primary School Hall", "address": "1 Bukit Purmei Avenue", "type": "DUS"},
    {"id": "p9fLGIN8JxS0irlxyBwXZ", "name": "Red Swastika School Hall", "address": "350 Bedok North Avenue 3", "type": "DUS"},
    {"id": "90m811nMHjVf4iGGkoPkf", "name": "Riverside Secondary School Hall", "address": "3 Woodlands Street 81", "type": "DUS"},
    {"id": "l7Nko7IX9xdfx3DiaCtZ4", "name": "Rivervale Primary School Hall", "address": "80 Rivervale Drive", "type": "DUS"},
    {"id": "JMJsnnXCzfV7wkG2fCU4N", "name": "Sembawang Primary School Hall", "address": "10 Sembawang Drive", "type": "DUS"},
    {"id": "cWLPCOP0DaRp91TswPcbH", "name": "Seng Kang Primary School Hall", "address": "21 Compassvale Walk", "type": "DUS"},
    {"id": "eYMEyuJQ37svFGs7lRjXD", "name": "Seng Kang Secondary School Hall", "address": "10 Compassvale Lane", "type": "DUS"},
    {"id": "RjmwZ5DpXxk9rUEXcP1Eq", "name": "Sengkang Green Primary School Hall", "address": "15 Fernvale Road", "type": "DUS"},
    {"id": "cRyHuTcU77VZY7Er3jVf5", "name": "Sengkang Sport Hall", "address": "57 Anchorvale Road", "type": "SRC"},
    {"id": "JEBGvnHbjLScZCVrgAorv", "name": "Senja-Cashew Sport Hall", "address": "101 Bukit Panjang Road", "type": "SRC"},
    {"id": "HOBvXHvooY9higfh69TVj", "name": "Serangoon Garden Secondary School Hall", "address": "21 Serangoon North Avenue 1", "type": "DUS"},
    {"id": "3DEYLIkm07HzOjfurjKvC", "name": "Serangoon Secondary School Hall", "address": "11 Upper Serangoon View", "type": "DUS"},
    {"id": "lKEsT2QFlC9IvEZBD4SYr", "name": "Shuqun Primary School Hall", "address": "8 Jurong West Street 51", "type": "DUS"},
    {"id": "859QPd8kzWT2vhgK5xlFd", "name": "South View Primary School Hall", "address": "6 Choa Chu Kang Central", "type": "DUS"},
    {"id": "XXjIDkenq2PJCl0K9Z0QP", "name": "St. Anthony's Primary School Hall", "address": "30 Bukit Batok Street 32", "type": "DUS"},
    {"id": "RBC3BhHXlonpOAHS8vVYH", "name": "St. Gabriel's Secondary School Hall", "address": "24 Serangoon Avenue 1", "type": "DUS"},
    {"id": "hYycEG6ZKDzU9hPtylTnO", "name": "Swiss Cottage Secondary School Hall", "address": "3 Bukit Batok Street 34", "type": "DUS"},
    {"id": "9tXy1KidVs30boQrZL9UJ", "name": "Teck Ghee Primary School Hall", "address": "1 Ang Mo Kio Street 32", "type": "DUS"},
    {"id": "9woSUBifmxK6x5JNtUUYU", "name": "Townsville Primary School Hall", "address": "3 Ang Mo Kio Avenue 10", "type": "DUS"},
    {"id": "lPVLkQadHo9kcrsVzXn0w", "name": "Unity Primary School Hall", "address": "21 Choa Chu Kang Crescent", "type": "DUS"},
    {"id": "F3xRj0oJrtsATkGAjjExT", "name": "Unity Secondary School Hall", "address": "20 Choa Chu Kang Street 62", "type": "DUS"},
    {"id": "9bkrZugmsZepQ2jtTajzm", "name": "Waterway Primary School Hall", "address": "70 Punggol Drive", "type": "DUS"},
    {"id": "Nyj8pYIPzftWajtf8Kh7b", "name": "Wellington Primary School Hall", "address": "10 Wellington Circle", "type": "DUS"},
    {"id": "OnP973cyRwtiEV383oTO5", "name": "West View Primary School Hall", "address": "31 Senja Road", "type": "DUS"},
    {"id": "QT8qwI8IX05TghAKm2cL1", "name": "Westwood Secondary School Hall", "address": "11 Jurong West Street 25", "type": "DUS"},
    {"id": "US6TJ1M2qrDBEIXuEBbrT", "name": "Whitley Secondary School Hall", "address": "30 Bishan Street 24", "type": "DUS"},
    {"id": "Qulnp10Fos2i45rlgrA5b", "name": "Woodgrove Primary School Hall", "address": "2 Woodlands Drive", "type": "DUS"},
    {"id": "ZYCSb8V69HUhNJeDKsEJf", "name": "Woodlands Secondary School Hall", "address": "11 Marsiling Road", "type": "DUS"},
    {"id": "OzrxvbMIJ0qQEw9h0suQT", "name": "Woodlands Sport Hall", "address": "2 Woodlands Street 12", "type": "SRC"},
    {"id": "IRzXPAeprtFuFudllhREU", "name": "Xinghua Primary School Hall", "address": "45 Hougang Avenue 1", "type": "DUS"},
    {"id": "rhK3pSR5ifFrB2AVCMOeK", "name": "Yio Chu Kang Primary School Hall", "address": "1 Hougang Street 51", "type": "DUS"},
    {"id": "nMIUcV8GPzzfSkcxPCrIN", "name": "Yio Chu Kang Secondary School Hall", "address": "3063 Ang Mo Kio Avenue 5", "type": "DUS"},
    {"id": "pYMh2B4kDjs6JEE5SoxbJ", "name": "Yio Chu Kang Sport Hall", "address": "200 Ang Mo Kio Avenue 9", "type": "SRC"},
    {"id": "ojB243CSdOOmCDy6JZlae", "name": "Yishun Primary School Hall", "address": "500 Yishun Ring Road", "type": "DUS"},
    {"id": "nm8H0TYFkiiOWvx5YqZB8", "name": "Yishun Secondary School Hall", "address": "4 Yishun Street 71", "type": "DUS"},
    {"id": "gwkeAKobIqSCOXA6OgULY", "name": "Yishun Sport Hall", "address": "101 Yishun Avenue 1", "type": "SRC"},
    {"id": "P2fLTWSMzdMj3ZI2V1wVy", "name": "Yishun Town Secondary School Hall", "address": "6 Yishun Street 21", "type": "DUS"},
    {"id": "vW0Nt7VfFelL2kKdKIx2p", "name": "Yuan Ching Secondary School Hall", "address": "103 Yuan Ching Road", "type": "DUS"},
    {"id": "sKQu9UyewFBDNeWqqJlil", "name": "Yuhua Primary School Hall", "address": "158 Jurong East Street 24", "type": "DUS"},
    {"id": "hk36GXwN2zUdZuB8Ylxt5", "name": "Zhonghua Primary School Hall", "address": "12 Serangoon Avenue 4", "type": "DUS"},
    {"id": "8xQCe0Lzl4RXK40l4ZLU7", "name": "Zhonghua Secondary School Hall", "address": "13 Serangoon Avenue 3", "type": "DUS"},
]

# ── Cache ─────────────────────────────────────────────────────────────────────

cache: dict = {"data": {}, "last_refreshed": None, "is_refreshing": False, "error": None}

def ts_to_sgt(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=SGT).strftime("%H:%M")

from typing import Optional
def get_proxy() -> Optional[str]:
    full = os.environ.get("PROXY_URL")
    if full:
        return full
    host = os.environ.get("PROXY_HOST")
    port = os.environ.get("PROXY_PORT")
    user = os.environ.get("PROXY_USER")
    pwd  = os.environ.get("PROXY_PASS")
    if host and port:
        if user and pwd:
            return f"http://{user}:{pwd}@{host}:{port}"
        return f"http://{host}:{port}"
    return None

# Warn if no proxy on startup (cloud IPs often blocked)
if not get_proxy():
    log.warning("No proxy configured! ActiveSG may block requests from cloud server IPs.")
    log.warning("Set PROXY_URL or PROXY_HOST/PORT env vars to use a proxy.")

# ── Fetcher ───────────────────────────────────────────────────────────────────

async def fetch_venue(session: AsyncSession, venue: dict, sem: asyncio.Semaphore, retry: int = 2) -> Optional[dict]:
    async with sem:
        for attempt in range(retry + 1):
            try:
                payload = json.dumps({"json": {"venueId": venue["id"], "activityId": ACTIVITY_ID}})
                r = await session.get(BASE_URL, params={"input": payload}, timeout=30)
                if r.status_code == 200:
                    data = r.json()
                    raw = data.get("result", {}).get("data", {}).get("json", [])
                    return {"venue": venue, "slots": raw}
                elif r.status_code in (429, 503, 502, 520):
                    # Rate limited or temporary error - retry
                    if attempt < retry:
                        wait = 2 ** attempt  # exponential backoff
                        log.warning(f"HTTP {r.status_code} for {venue['name']}, retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                    log.warning(f"HTTP {r.status_code} for {venue['name']} after {retry} retries")
                else:
                    log.warning(f"HTTP {r.status_code} for {venue['name']}")
                    return None
            except asyncio.TimeoutError:
                if attempt < retry:
                    wait = 2 ** attempt
                    log.warning(f"Timeout for {venue['name']}, retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                log.warning(f"Timeout for {venue['name']} after {retry} retries")
                return None
            except Exception as e:
                log.warning(f"Error fetching {venue['name']}: {type(e).__name__}: {str(e)[:100]}")
                return None
        return None

async def refresh_cache():
    if cache["is_refreshing"]:
        return
    cache["is_refreshing"] = True
    log.info("Starting cache refresh...")
    start = datetime.now(SGT)
    new_data: dict = {}

    proxy = get_proxy()
    if proxy:
        masked = proxy.split("@")[-1] if "@" in proxy else proxy
        log.info(f"Using proxy: {masked}")
    else:
        log.info("No proxy configured — using direct connection")

    try:
        proxy_dict = {"http": proxy, "https": proxy} if proxy else None
        sem = asyncio.Semaphore(CONCURRENCY)
        async with AsyncSession(impersonate="chrome120", proxies=proxy_dict) as session:
            tasks = [fetch_venue(session, v, sem) for v in VENUES]
            results = await asyncio.gather(*tasks)

        ok = 0
        for result in results:
            if not result:
                continue
            ok += 1
            venue = result["venue"]
            for entry in result["slots"]:
                date_str, slot_info = entry[0], entry[1]
                if slot_info.get("type") != "instant":
                    continue
                timeslots = []
                for ts in slot_info.get("timeslots", []):
                    timeslots.append({
                        "start": ts_to_sgt(ts["start"]),
                        "end": ts_to_sgt(ts["end"]),
                        "courts": len(ts.get("subvenues", [])),
                        "is_peak": ts.get("isPeak", False),
                        "price": ts.get("rates", [{}])[0].get("price", "0"),
                    })
                if timeslots:
                    new_data.setdefault(date_str, []).append({
                        "id": venue["id"], "name": venue["name"],
                        "address": venue["address"], "type": venue["type"],
                        "timeslots": timeslots,
                    })

        cache["data"] = new_data
        cache["last_refreshed"] = datetime.now(SGT).isoformat()
        cache["error"] = None
        elapsed = (datetime.now(SGT) - start).total_seconds()
        log.info(f"Cache refreshed in {elapsed:.1f}s — {ok}/{len(VENUES)} venues ok, {len(new_data)} dates cached")

    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)[:200]}"
        cache["error"] = error_msg
        log.error(f"Cache refresh failed: {error_msg}")
        log.error(traceback.format_exc())
    finally:
        cache["is_refreshing"] = False

# ── App lifecycle ─────────────────────────────────────────────────────────────

scheduler = AsyncIOScheduler(timezone=str(SGT))

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(refresh_cache, "interval", minutes=REFRESH_INTERVAL_MINUTES)
    scheduler.start()
    asyncio.create_task(refresh_cache())
    yield
    scheduler.shutdown()

app = FastAPI(title="ActiveSG Badminton Slot Finder", lifespan=lifespan)

# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/slots")
async def get_slots(
    date: str = Query(...),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
):
    day_data = cache["data"].get(date, [])
    results = []
    for venue in day_data:
        if type and venue["type"] != type.upper():
            continue
        timeslots = venue["timeslots"]
        if start:
            timeslots = [t for t in timeslots if t["start"] >= start]
        if end:
            timeslots = [t for t in timeslots if t["start"] < end]
        if timeslots:
            results.append({**venue, "timeslots": timeslots})
    results.sort(key=lambda x: x["name"])
    return {"date": date, "results": results, "total_venues": len(results),
            "last_refreshed": cache["last_refreshed"], "is_refreshing": cache["is_refreshing"],
            "error": cache["error"]}

@app.get("/api/status")
async def get_status():
    proxy = get_proxy()
    masked_proxy = None
    if proxy:
        masked_proxy = proxy.split("@")[-1] if "@" in proxy else "configured"
    return {
        "last_refreshed": cache["last_refreshed"],
        "is_refreshing": cache["is_refreshing"],
        "dates_cached": sorted(cache["data"].keys()),
        "total_venues": len(VENUES),
        "error": cache["error"],
        "refresh_interval_minutes": REFRESH_INTERVAL_MINUTES,
        "proxy_configured": masked_proxy is not None,
        "proxy_host": masked_proxy,
    }

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/refresh")
async def trigger_refresh():
    asyncio.create_task(refresh_cache())
    return {"message": "Refresh triggered"}

@app.get("/api/diag")
async def diagnostics():
    """Diagnostic endpoint to test connectivity and see what's failing."""
    import platform
    proxy = get_proxy()
    results = {
        "python_version": platform.python_version(),
        "proxy_configured": proxy is not None,
        "cache_status": {
            "last_refreshed": cache["last_refreshed"],
            "is_refreshing": cache["is_refreshing"],
            "error": cache["error"],
            "dates_cached": len(cache["data"]),
        }
    }

    # Test a single venue fetch
    test_venue = VENUES[0]  # Admiralty Primary School
    try:
        proxy_dict = {"http": proxy, "https": proxy} if proxy else None
        async with AsyncSession(impersonate="chrome120", proxies=proxy_dict) as session:
            payload = json.dumps({"json": {"venueId": test_venue["id"], "activityId": ACTIVITY_ID}})
            r = await session.get(BASE_URL, params={"input": payload}, timeout=30)
            results["test_fetch"] = {
                "venue": test_venue["name"],
                "status_code": r.status_code,
                "success": r.status_code == 200,
                "has_data": False,
            }
            if r.status_code == 200:
                data = r.json()
                raw = data.get("result", {}).get("data", {}).get("json", [])
                results["test_fetch"]["has_data"] = len(raw) > 0
                results["test_fetch"]["dates_found"] = len(raw)
    except Exception as e:
        results["test_fetch"] = {
            "venue": test_venue["name"],
            "error": f"{type(e).__name__}: {str(e)[:200]}",
            "success": False,
        }

    return results

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")
