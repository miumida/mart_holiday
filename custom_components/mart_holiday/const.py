DOMAIN   = 'mart_holiday'
PLATFORM = 'sensor'
SW_VERSION = '1.1.15'
MANUFACT   = 'miumida'
MODEL = '대형마트 휴무일'

_MART_KIND = {
    'e' : 'E마트',
    'l' : '롯데마트',
    'h' : 'Homeplus',
    'c' : 'Costco',
    'g' : 'GS슈퍼마켓',
}

CONF_MART_KIND = 'mart_kind'
CONF_MART_CODE = 'mart_code'
CONF_NAME = 'name'
CONF_AREA = 'area'

_AREA = {
    'N/A': 'N/A',
    'A' : '서울',
    'C' : '인천',
    'I' : '경기',
    'F' : '대전',
    'Q' : '세종',
    'N' : '충청',
    'D' : '대구',
    'J' : '경상',
    'G' : '울산',
    'B' : '부산',
    'L' : '전라',
    'E' : '광주',
    'H' : '강원',
    'P' : '제주',
}

#COSTCO 매장별 휴무일
_COSTCO_STORES = {
  '01': ['대전점',          6, 6],
  '02': ['대구점',          6, 6],
  '03': ['세종점',          6, 6],
  '04': ['대구 혁신도시점', 6, 6],
  '05': ['천안점',          6, 6],
  '06': ['부산점',          6, 6],
  '07': ['울산점',          2, 6],
  '08': ['공세점',          6, 6],
  '09': ['양재점',          6, 6],
  '10': ['광명점',          6, 6],
  '11': ['하남점',          6, 6],
  '12': ['송도점',          6, 6],
  '13': ['양평점',          6, 6],
  '14': ['상봉점',          6, 6],
  '15': ['일산점',          2, 2],
  '16': ['의정부점',        6, 6],
  '17': ['김해점',          6, 6],
  '18': ['고척점',          6, 6],
}

LMART_SEARCH_URL = "http://company.lottemart.com/shop/shop_search_type.asp?schArea=&schType=01&schWord={}"
LMART_BSE_URL = 'http://company.lottemart.com/bc/branch/storeinfo.json?brnchCd={}'

EMART_BSE_URL = 'https://emartapp.emart.com/menu/holiday_ajax.do?areaCd={}&year={}&month={}'
EMART_IMSI_URL = 'https://emartapp.emart.com/branch/view.do?id={}'

HOMEPLUS_BSE_URL = 'http://corporate.homeplus.co.kr/STORE/HyperMarket_view.aspx?sn={}&ind=HOMEPLUS'
HOMEPLUS_EXPRESS_BSE_URL = 'http://corporate.homeplus.co.kr/STORE/HyperMarket_Express_view.aspx?sn={}&ind=EXPRESS'

GSSUPER_BSE_URL = 'http://gsthefresh.gsretail.com/thefresh/ko/market-info/find-storelist?searchShopName={}'

