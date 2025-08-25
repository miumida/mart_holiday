DOMAIN     = 'mart_holiday'
PLATFORM   = [ "sensor" ]
SW_VERSION = '1.4.0'
MANUFACT   = 'miumida'
MODEL      = '대형마트 휴무일'

_MART_KIND = {
    'e' : 'E마트',
    'l' : '롯데마트',
    'h' : 'Homeplus',
    'c' : 'Costco',
    'g' : 'GS슈퍼마켓',
}

_MART_URL = {
    'e' : 'https://emartapp.emart.com/branch/view.do?id={}',
    'l' : 'http://company.lottemart.com/shop/shop_search_type.asp?schArea=&schType=01&schWord={}',
    'h' : 'https://my.homeplus.co.kr/store/store_detail?storId={}',
    'c' : '',
    'g' : 'http://gsthefresh.gsretail.com/thefresh/ko/market-info/find-storelist?searchShopName={}',
}

_MART_NAME = {
    'e' : 'E마트({})',
    'l' : '롯데마트({})',
    'h' : 'Homeplus({})',
    'c' : 'Costco({})',
    'g' : 'GS슈퍼마켓({})',
}

CONF_MART_KIND = 'mart_kind'
CONF_MART_CODE = 'mart_code'
CONF_NAME = 'name'
CONF_AREA = 'area'

DEFAULT_MART_ALPHA_ICON = 'mdi:alpha-{}-box'

ATTR_NAME = 'name'
ATTR_ID   = 'id'
ATTR_TEL  = 'tel'
ATTR_ADDR = 'address'

ATTR_HOLIDAY = 'holiday'
ATTR_HOLIDAY_1 = 'holiday_1'
ATTR_HOLIDAY_2 = 'holiday_2'
ATTR_HOLIDAY_3 = 'holiday_3'
ATTR_HOLIDAY_4 = 'holiday_4'

ATTR_NEXT_HOLIDAY = 'next_holiday'
ATTR_HOLIDATE = 'holidate'

ATTR_BUSSINESS_HOURS = 'bussiness_hours'
ATTR_OPERTIME = 'opertime'

ATTR_DAYOFF = 'day-off'

#COSTCO 매장별 휴무일
_COSTCO_STORES = {
  '01': ['대전점',          6, 6],
  '02': ['대구점',          6, 6],
  '03': ['세종점',          6, 6],
  '04': ['대구 혁신도시점',  6, 6],
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
  '19': ['청라점',          6, 6],
}

LMART_SEARCH_URL = "http://company.lottemart.com/shop/shop_search_type.asp?schArea=&schType=01&schWord={}"
LMART_BSE_URL = 'http://company.lottemart.com/bc/branch/storeinfo.json?brnchCd={}'

EMART_IMSI_URL = 'https://emartapp.emart.com/branch/view.do?id={}'

HOMEPLUS_BSE_URL = 'http://corporate.homeplus.co.kr/STORE/HyperMarket_view.aspx?sn={}&ind=HOMEPLUS'
HOMEPLUS_EXPRESS_BSE_URL = 'http://corporate.homeplus.co.kr/STORE/HyperMarket_Express_view.aspx?sn={}&ind=EXPRESS'

GSSUPER_BSE_URL = 'http://gsthefresh.gsretail.com/thefresh/ko/market-info/find-storelist?searchShopName={}'
