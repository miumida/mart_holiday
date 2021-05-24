import logging
import re
import requests
import calendar
import voluptuous as vol
from bs4 import BeautifulSoup
from urllib import parse

import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_API_KEY, CONF_ICON)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

REQUIREMENTS = ['xmltodict==0.12.0', 'beautifulsoup4==4.4.0']

_LOGGER = logging.getLogger(__name__)

CONF_MARTS      = 'marts'
CONF_MART_KIND  = 'mart_kind'
CONF_MART_NAME  = 'name'
CONF_MART_CODE  = 'mart_code'
CONF_AREA       = 'area'

EMART_BSE_URL = 'https://emartapp.emart.com/menu/holiday_ajax.do?areaCd={}&year={}&month={}' 
LMART_BSE_URL = 'http://company.lottemart.com/bc/branch/storeinfo.json?brnchCd={}'
HOMEPLUS_BSE_URL = 'http://corporate.homeplus.co.kr/STORE/HyperMarket_view.aspx?sn={}&ind=HOMEPLUS'
HOMEPLUS_EXPRESS_BSE_URL = 'http://corporate.homeplus.co.kr/STORE/HyperMarket_Express_view.aspx?sn={}&ind=EXPRESS'
GSSUPER_BSE_URL = 'http://gsthefresh.gsretail.com/thefresh/ko/market-info/find-storelist?searchShopName={}'

# E마트 지역 코드
_EMART_AREA_CD = {
  '서울' : 'A',
  '인천' : 'C',
  '경기' : 'I',
  '대전' : 'F',
  '세종' : 'Q',
  '충청' : 'N',
  '대구' : 'D',
  '경상' : 'J',
  '울산' : 'G',
  '부산' : 'B',
  '전라' : 'L',
  '광주' : 'E',
  '강원' : 'H',
  '제주' : 'P',
}

# E마트 속성
_EMART_PROPERTIES = {
  'CODE':[None],
  'AREA':[None],
  'JIJUM_ID':[None],
  'NAME':[None],
  'TEL' :['mdi:cellphone'],

  'HOLIDAY_YEAR':[None],
  'HOLIDAY_MONTH':[None],

  'HOLIDAY_DAY2_YMD':['mdi:calendar'],
  'HOLIDAY_DAY1_YMD':['mdi:calendar'],
  'HOLIDAY_DAY3_YMD':['mdi:calendar'],

  'HOLIDAY_DAY1':['mdi:calendar'],
  'HOLIDAY_DAY2':['mdi:calendar'],
  'HOLIDAY_DAY3':['mdi:calendar'],

  'HOLIDAY_DAY1_YOIL':['mdi:calendar'],
  'HOLIDAY_DAY2_YOIL':['mdi:calendar'],
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
}

DEFAULT_MART_NAME = 'mart'
DEFAULT_MART_ICON = 'mdi:store'
DEFAULT_MART_ALPHA_ICON = 'mdi:alpha-{}-box'
DEFAULT_MART_CODE = '-'
DEFAULT_AREA = ''

COMM_DATE_FORMAT = '{}-{}-{}'

MIN_TIME_BETWEEN_API_UPDATES    = timedelta(seconds=14400) #4시간 마다
MIN_TIME_BETWEEN_SENSOR_UPDATES = timedelta(seconds=14400) #4시간 마다

ATTR_NAME = 'name'
ATTR_ID   = 'id'
ATTR_TEL  = 'tel'
ATTR_ADDR = 'address'

ATTR_HOLIDAY = 'holiday'
ATTR_HOLIDAY_1 = 'holiday_1'
ATTR_HOLIDAY_2 = 'holiday_2'
ATTR_HOLIDAY_3 = 'holiday_3'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MARTS): vol.All(cv.ensure_list, [{
        vol.Required(CONF_MART_KIND): cv.string,
        vol.Optional(CONF_NAME, default = DEFAULT_MART_NAME): cv.string,
        vol.Optional(CONF_ICON, default = DEFAULT_MART_ICON): cv.string,
        vol.Optional(CONF_MART_CODE, default = DEFAULT_MART_CODE): cv.string,
        vol.Optional(CONF_AREA, default = DEFAULT_AREA): cv.string,
    }]),
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    name  = config.get(CONF_NAME)
    marts = config.get(CONF_MARTS)

    sensors = []

    for mart in marts:
        if mart[CONF_MART_KIND] == 'e':
            try:
                eAPI    = EMartAPI( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_MART_CODE], mart[CONF_AREA] )
                eSensor = EMartSensor( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_ICON], mart[CONF_MART_CODE], eAPI )
                eSensor.update()
                sensors += [eSensor]
            except Exception as ex:
                _LOGGER.error('Failed to update EMart API status Error: %s', ex)

        if mart[CONF_MART_KIND] == 'l':
            try:
                lotteAPI    = LotteMartAPI( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_MART_CODE] )
                lotteSensor = LotteMartSensor( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_ICON], mart[CONF_MART_CODE], lotteAPI )
                lotteSensor.update()
                sensors += [lotteSensor]
            except Exception as ex:
                _LOGGER.error('Failed to update LotteMart API status Error: %s', ex)

        if mart[CONF_MART_KIND] == 'h':
            try:
                homeplusAPI    = HomeplusAPI( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_MART_CODE] )
                homeplusSensor = HomeplusSensor( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_ICON], mart[CONF_MART_CODE], homeplusAPI )
                homeplusSensor.update()
                sensors += [homeplusSensor]
            except Exception as ex:
                _LOGGER.error('Failed to update Homeplus API status Error: %s', ex)

        if mart[CONF_MART_KIND] == 'c':
            try:
                costcoAPI     = CostcoAPI( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_MART_CODE] )
                costcoSensor  = CostcoSensor( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_ICON], mart[CONF_MART_CODE], costcoAPI )
                costcoSensor.update()
                sensors += [costcoSensor]
            except Exception as ex:
                _LOGGER.error('Failed to update Costco API status Error: %s', ex)

        if mart[CONF_MART_KIND] == 'g':
            try:
                gssuperAPI      = GssuperAPI( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_MART_CODE])
                gssuperSensor   = GssuperSensor( mart[CONF_MART_KIND], mart[CONF_MART_NAME], mart[CONF_ICON], mart[CONF_MART_CODE], gssuperAPI)
                gssuperSensor.update()
                sensors += [gssuperSensor]
            except Exception as ex:
                _LOGGER.error('Failed to update GS SuperMart API status Error: %s', ex)

    add_entities(sensors, True)


def viewState(val):
    if val == '-':
        return '-'
    else:
        return '{}일'.format(val)

#이마트 날짜형식 변환
def ConvertEmartToComm(val):
    if len(val) == 8:
        return COMM_DATE_FORMAT.format( val[:4], val[4:6], val[-2:] )
    else:
        return val


#롯데마트 날짜 형식 변환
def ConvertLmartToComm(val):
    dt = datetime.now()

    pYear  = dt.strftime("%Y")
    pMonth = dt.strftime("%m")

    tmp = val.split('/')

    try:
        #01/01 형식이 아닌 01월 01일 형식을 위한 처리
        if len(tmp) == 1:
            tmp32 = val.split(" ")
            if len(tmp32) > 1:
                tmp32[0] = tmp32[0].replace("월", "")
                tmp32[1] = tmp32[1].replace("일", "")

                #월이 1자리인 경우, 자리수 맞춤
                if len(tmp32[0]) == 1:
                    tmp32[0] = '0' + tmp32[0]

                if ( pMonth == '12' and tmp32[0] == '01' ):
                    pYear = str(int(pYear) + 1)
                rslt = COMM_DATE_FORMAT.format(pYear, tmp32[0], tmp32[1])
                return rslt

            if len(tmp32) == 1:
                val = val.replace("월", "월 ")

                tmpNone =  val.split(" ")
                if len(tmpNone) > 1:
                    tmpNone[0] = tmpNone[0].replace("월", "")
                    tmpNone[1] = tmpNone[1].replace("일", "")

                if len(tmpNone[0]) == 1:
                     tmpNone[0] = '0' + tmpNone[0]

                     if ( pMonth == '12' and tmpNone[0] == '01' ):
                         pYear = str(int(pYear) + 1)
                     rslt = COMM_DATE_FORMAT.format(pYear, tmpNone[0], tmpNone[1])
                     return rslt
        elif len(tmp) == 2:
            if len(tmp[0]) == 1:
                tmp[0] = '0' + tmp[0]
            if len(tmp[1]) == 1:
                tmp[1] = '0' + tmp[1]
            rslt = COMM_DATE_FORMAT.format(pYear, tmp[0], tmp[1])
            return rslt

        #현재는 12월이고 val이 1월이면 현재년도+1
        if ( pMonth == '12' and tmp[0] == '01' ):
            pYear =  str(int(pYear) + 1)

        rslt = COMM_DATE_FORMAT.format(pYear, tmp[0], tmp[1])
        return rslt
    except Exception as ex:
        _LOGGER.error('Failed to update ConvertLmartToComm() status Error: %s', ex)

    return val;

#GS슈퍼마켓 날짜 형식 변환
def ConvertGssuperToComm(val):
    """MM월 DD일을 날짜값으로 변경"""  
    if val is None:
        return None

    dt = datetime.now()
    try:
        vMonth = datetime.strptime(val, "%m월 %d일").month
        if vMonth < dt.month:
            return repr(dt.year+1)+"-"+val.replace("월 ", "-").replace("일", "")
        else:
            return repr(dt.year)+"-"+val.replace("월 ", "-").replace("일", "")
    except:
        return None


# 문자 YYYY-MM-DD를 datetime으로 형변환
def Comm2Date(val):
    tmp = val.split("-")

    if len(tmp) > 1:
        return datetime(year=int(tmp[0]), month=int(tmp[1]), day=int(tmp[2]))
    else:
        return None

class EMartAPI:
    """EMart API."""
    def __init__(self, mart_kind, name, mart_code, area):
        """Initialize the EMart API."""
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self._area      = area
        self.result     = {}

    @Throttle(MIN_TIME_BETWEEN_API_UPDATES)
    def update(self):
        """Update function for updating api information."""
        try:
            dt = datetime.now()

            pYear  = dt.strftime("%Y")
            pMonth = dt.strftime("%m")

            url = EMART_BSE_URL
            url = url.format(self._area, pYear, pMonth)

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            #param 정보 추출
            param = response.json()['param']

            #년도
            rYear      = param.get('year', '-')
            rYearPlus  = param.get('yearPlus', '-')
            rYearMinus = param.get('yearMinus', '-')

            #월
            rMonth      = param.get('month', '-')
            rMonthPlus  = param.get('monthPlus', '-')
            rMonthMinus = param.get('monthMinus', '-')

            #dateList 정보 추출
            emartJijum = response.json()['dateList']

            emart_dict = {}
            emart_dict_tmp = {}

            nowDt = dt.strftime("%d") #str(dt.day)

            bNext = False

            for item in emartJijum:
                if self._mart_code != item['JIJUM_ID']: continue

                nextOffday = nowDt

                holiday1 = item['HOLIDAY_DAY1']
                holiday2 = item['HOLIDAY_DAY2']
                holiday3 = item['HOLIDAY_DAY3']

                maxHoliday = max(holiday1, holiday2, holiday3)

                if nowDt > maxHoliday:
                    bNext = True

                    emart_dict_tmp[item['JIJUM_ID']] = {
                        'jijum_id': item['JIJUM_ID'],
                        'name'    : item['NAME'],
                        'area'    : item['AREA'],
                        'tel'     : item['TEL'],

                        'holiday_1' : ConvertEmartToComm(item['HOLIDAY_DAY1_YMD']),
                        'holiday_2' : ConvertEmartToComm(item['HOLIDAY_DAY2_YMD']),
                        'holiday_3' : ConvertEmartToComm(item['HOLIDAY_DAY3_YMD']),

                        'year'        : pYear,
                        'month'       : pMonth,
                        'next_holiday' : '-'
                    }

                    break

                nextOffday = max(nowDt, holiday1)

                if holiday1 >= nowDt:
                    nextOffday = holiday1

                if ( nowDt > holiday1 and nowDt <= holiday2 ):
                    nextOffday = holiday2

                if ( nowDt > holiday2 and nowDt <= holiday3 ):
                    nextOffday = holiday3

                if nowDt  > maxHoliday:
                    nextOffday = '-'

                emart_dict[item['JIJUM_ID']] = {
                    'jijum_id': item['JIJUM_ID'],
                    'name'    : item['NAME'],
                    'area'    : item['AREA'],
                    'tel'     : item['TEL'],

                    'holiday_1' : ConvertEmartToComm(item['HOLIDAY_DAY1_YMD']),
                    'holiday_2' : ConvertEmartToComm(item['HOLIDAY_DAY2_YMD']),
                    'holiday_3' : ConvertEmartToComm(item['HOLIDAY_DAY3_YMD']),

                    'year'        : pYear,
                    'month'       : pMonth,
                    'next_holiday' : nextOffday
                }

                if nowDt > maxHoliday:
                    break

            if bNext:
                url = EMART_BSE_URL
                url = url.format(self._area, rYearPlus, rMonthPlus)

                response = requests.get(url, timeout=10)
                response.raise_for_status()

                emartJijumN = response.json()['dateList']

                for item in emartJijumN:
                    if self._mart_code != item['JIJUM_ID']: continue

                    holiday1 = item['HOLIDAY_DAY1']
                    holiday2 = item['HOLIDAY_DAY2']
                    holiday3 = item['HOLIDAY_DAY3']

                    nextOffday = holiday1

                    emart_dict[item['JIJUM_ID']] = {
                        'jijum_id': item['JIJUM_ID'],
                        'name'    : item['NAME'],
                        'area'    : item['AREA'],
                        'tel'     : item['TEL'],

                        'holiday_1' : ConvertEmartToComm(item['HOLIDAY_DAY1_YMD']),
                        'holiday_2' : ConvertEmartToComm(item['HOLIDAY_DAY2_YMD']),
                        'holiday_3' : ConvertEmartToComm(item['HOLIDAY_DAY3_YMD']),

                        'year'         : rYearPlus,
                        'month'        : rMonthPlus,
                        'next_holiday' : nextOffday
                    }

            if len(emart_dict) == 0:
                emart_dict = emart_dict_tmp

            self.result = emart_dict
            #_LOGGER.debug('EMart API Request Result: %s', self.result)
        except Exception as ex:
            _LOGGER.error('Failed to update EMart API status Error: %s', ex)
            raise

class EMartSensor(Entity):
    def __init__(self, mart_kind, name, icon, mart_code,  api):
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self._api       = api
        self._icon      = icon
        self._state     = None
        self.marts      = {}

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if not self._name:
            return '{}'.format(self._mart_kind)
        return '이마트({})'.format(self._name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return DEFAULT_MART_ALPHA_ICON.format(self._mart_kind)

    @property
    def state(self):
        """Return the state of the sensor."""
        next_offday = '-'
        for key in self.marts:
            next_offday = self.marts[key].get('next_holiday', '-')
            if next_offday != '-':
                next_offday = COMM_DATE_FORMAT.format(self.marts[key].get('year', '-'), self.marts[key].get('month','-'), next_offday)
        return next_offday

    @Throttle(MIN_TIME_BETWEEN_SENSOR_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        self._api.update()
        marts_dict = self._api.result

        self.marts = marts_dict

    @property
    def device_state_attributes(self):
        """Attributes."""
        return self.marts[self._mart_code]


class LotteMartAPI:
    """LotteMart API."""
    def __init__(self, mart_kind, name, brnchCd):
        """Initialize the Mart Holiday API."""
        self._mart_kind = mart_kind
        self._name      = name
        self._brnchCd   = brnchCd
        self.result     = {}

    @Throttle(MIN_TIME_BETWEEN_API_UPDATES)
    def update(self):
        """Update function for updating api information."""
        try:
            dt = datetime.now()

            pYear  = dt.strftime("%Y")
            pMonth = dt.strftime("%m")

            url = LMART_BSE_URL
            url = url.format(self._brnchCd)

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            lmart = response.json()['data']

            lmart_dict ={}

            holidate = lmart['holiDate']

            # 00/00 처리
            r = re.compile("\d{1,2}/\d{1,2}")
            rtn = r.findall(holidate)

            # 00월 00일 처리
            if len(rtn) == 0:
                rk = re.compile("\d+월 \d+일")
                rtn = rk.findall(holidate)

            # 00월00일 처리
            if len(rtn) == 0:
                rk = re.compile("\d+월\d+일")
                rtn = rk.findall(holidate)

            lmart_dict[self._brnchCd]= {
                'id'       : self._brnchCd,
                'name'     : lmart['strNm'],

                'holidate' : lmart['holiDate'],
                'holiday_1' : ConvertLmartToComm(rtn[0]),
                'holiday_2' : ConvertLmartToComm(rtn[1])
            }

            self.result = lmart_dict
            #_LOGGER.debug('LotteMart API Request Result: %s', self.result)
        except Exception as ex:
            _LOGGER.error('Failed to update LotteMart API status Error: %s', ex)
            raise

class LotteMartSensor(Entity):
    def __init__(self, mart_kind, name, icon, brnchCd, api):
        self._mart_kind = mart_kind
        self._name      = name
        self._brnchCd   = brnchCd
        self._holidate  = None
        self._api   = api
        self._icon  = icon
        self._state = None
        self.marts  = {}

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._brnchCd)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if not self._name:
            return '{}'.format(self._mart_kind)
        return '롯데마트({})'.format(self._name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return DEFAULT_MART_ALPHA_ICON.format(self._mart_kind)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._holidate

    @property
    def attribution(self):
        """Return the attribution."""
        return 'Powered by miumida'

    @Throttle(MIN_TIME_BETWEEN_SENSOR_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        self._api.update()
        marts_dict = self._api.result

        self.marts = marts_dict

        dt = datetime.now()
        nowDt = dt.strftime("%d")

        holiday_1 = self.marts.get(self._brnchCd,{}).get('holiday_1','-')
        holiday_2 = self.marts.get(self._brnchCd,{}).get('holiday_2','-')

        dt_holiday_1 = Comm2Date(holiday_1)
        dt_holiday_2 = Comm2Date(holiday_2)

        holidate = holiday_1 if dt <= dt_holiday_1 + timedelta(days=1) else holiday_2

        self._holidate = holidate

    @property
    def device_state_attributes(self):
        """Attributes."""
        return self.marts.get(self._brnchCd,{})

class HomeplusAPI:
    """Homeplus API."""
    def __init__(self, mart_kind, name, mart_code):
        """Initialize the Mart Holiday API."""
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self.result     = {}

    @Throttle(MIN_TIME_BETWEEN_API_UPDATES)
    def update(self):
        """Update function for updating api information."""
        try:
            dt = datetime.now()

            pYear  = dt.strftime("%Y")
            pMonth = dt.strftime("%m")

            url = HOMEPLUS_BSE_URL
            url = url.format(self._mart_code)

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            page = response.content.decode('utf8')

            mart_dict ={}

            soup = BeautifulSoup(page, 'html.parser')
            storeDetail = soup.find(id="store_detail01")

            tds = storeDetail.find_all("td")

            addr     = tds[0].get_text().strip()
            holiday  = tds[1].get_text().strip()
            tel      = tds[2].get_text().strip()
            opertime = tds[3].get_text().strip()

            #휴무일 추출 : 2019-03-24 형태의 값만 추출한다.
            r = re.compile("\d{4}-\d{2}-\d{2}")

            rtn = r.findall(holiday)

            if len(rtn) > 0:
                holiday = min(rtn)

            mart_dict[self._mart_code]= {
                'id'       : self._mart_code,
                'name'     : self._name,

                'holiday'  : holiday,
                'address'  : addr,
                'opertime' : opertime,
                'tel'      : tel
            }

						# 휴무이을 딕셔너리에 추가
            cnt = 1
            for tmp in rtn:
                mart_dict[self._mart_code].update( {'holiday_{}'.format(str(cnt)):tmp} )
                cnt += 1

            self.result = mart_dict
            #_LOGGER.debug('Homeplus API Request Result: %s', self.result)
        except Exception as ex:
            _LOGGER.error('Failed to update Homeplus API status Error: %s', ex)
            raise

class HomeplusSensor(Entity):
    def __init__(self, mart_kind, name, icon, mart_code, api):
        self._mart_kind  = mart_kind
        self._name       = name
        self._mart_code  = mart_code
        self._holidate   = None
        self._api   = api
        self._icon  = icon
        self._state = None
        self.marts  = {}

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if not self._name:
            return '{}'.format(self._mart_kind)
        return '홈플러스({})'.format(self._name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return DEFAULT_MART_ALPHA_ICON.format(self._mart_kind)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._holidate

    @property
    def attribution(self):
        """Return the attribution."""
        return 'Powered by miumida'

    @Throttle(MIN_TIME_BETWEEN_SENSOR_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return
        self._api.update()
        marts_dict = self._api.result

        self.marts = marts_dict

        holiday = self.marts.get(self._mart_code,{}).get('holiday', '-')

        self._holidate = '-' if holiday == '' else holiday

#    @property
#    def device_state_attributes(self):
#        """Attributes."""
#        return self.marts.get(self._mart_code,{})

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data={}

        data[ATTR_ID]   = self.marts.get(self._mart_code,{}).get('id', '-')
        data[ATTR_NAME] = self.marts.get(self._mart_code,{}).get('name', '-')
        data[ATTR_TEL]  = self.marts.get(self._mart_code,{}).get('tel', '-')

        data[ATTR_HOLIDAY]   = self.marts.get(self._mart_code,{}).get('holiday', '-')
        data[ATTR_HOLIDAY_1] = self.marts.get(self._mart_code,{}).get('holiday_1', '-')
        data[ATTR_HOLIDAY_2] = self.marts.get(self._mart_code,{}).get('holiday_2', '-')

        return data

class CostcoAPI:
    """Costco API."""
    def __init__(self, mart_kind, name, mart_code):
        """Initialize the Mart Holiday API."""
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self.result     = {}

    @Throttle(MIN_TIME_BETWEEN_API_UPDATES)
    def update(self):
        """Update function for updating api information."""
        try:
            dt = datetime.now()

            pYear  = dt.strftime("%Y")
            pMonth = dt.strftime("%m")

            nowDt = dt.strftime("%d")

            mart_dict ={}

            monthInfo = calendar.monthrange(int(pYear), int(pMonth))

            data_1st = datetime(year=int(pYear), month=int(pMonth), day=1)

            costco_nm = _COSTCO_STORES[self._mart_code][0]
            costco_1st_holiday = _COSTCO_STORES[self._mart_code][1]
            costco_2nd_holiday = _COSTCO_STORES[self._mart_code][2]

            #둘째주
            addCnt_1st = 0;
            addCnt_2nd = 0;

            if monthInfo[0] != costco_1st_holiday:
                for i in range(1,7):
                    data_accu = data_1st + timedelta(days=i)
                    if costco_1st_holiday == data_accu.weekday():
                        diff =  data_accu - data_1st
                        addCnt_1st = diff.days

            if monthInfo[0] != costco_2nd_holiday:
                if costco_1st_holiday == costco_2nd_holiday:
                    addCnt_2nd = addCnt_1st
                else:
                    for i in range(1,7):
                        data_accu = data_1st + timedelta(days=i)
                        if costco_2nd_holiday == data_accu.weekday():
                            diff =  data_accu - data_1st
                            addCnt_2nd = diff.days

            month_tmp_1 = []
            i = addCnt_1st;
            while i < monthInfo[1]:
                if i > monthInfo[1]:
                    break;

                tmp = data_1st + timedelta(days=i)

                month_tmp_1.append(tmp)

                i = i + 7;

            #넷째주
#            addCnt_2nd = 0;

#            if monthInfo[0] != costco_2nd_holiday:
#                addCnt_2nd = 7 - monthInfo[0] + costco_2nd_holiday

            month_tmp_2 = []
            i = addCnt_2nd;
            while i < monthInfo[1]:
                if i > monthInfo[1]:
                    break;

                tmp = data_1st + timedelta(days=i)

                month_tmp_2.append(tmp)

                i = i + 7;

            #휴무일
            holiday_1 = month_tmp_1[1]
            holiday_2 = month_tmp_2[3]

            #가까운 휴무일 지정
            holidate = holiday_1 if holiday_1.strftime("%d") >= nowDt else holiday_2

            mart_dict[self._mart_code]= {
                'id'       : self._mart_code,
                'name'     : self._name,

                'holidate'   : holidate.strftime("%Y-%m-%d"),
                'holiday_1'  : holiday_1.strftime("%Y-%m-%d"),
                'holiday_2'  : holiday_2.strftime("%Y-%m-%d"),
            }

            self.result = mart_dict

        except Exception as ex:
            _LOGGER.error('Failed to update Costco API status Error: %s', ex)
            raise


class CostcoSensor(Entity):
    def __init__(self, mart_kind, name, icon, mart_code, api):
        self._mart_kind  = mart_kind
        self._name       = name
        self._mart_code  = mart_code
        self._holidate   = None
        self._api   = api
        self._icon  = icon
        self._state = None
        self.marts  = {}

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if not self._name:
            return '{}'.format(self._mart_kind)
        return '코스트코({})'.format(self._name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return DEFAULT_MART_ALPHA_ICON.format(self._mart_kind)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._holidate

    @property
    def attribution(self):
        """Return the attribution."""
        return 'Powered by miumida'

    @Throttle(MIN_TIME_BETWEEN_SENSOR_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return
        self._api.update()
        marts_dict = self._api.result

        self.marts = marts_dict

        self._holidate = self.marts.get(self._mart_code,{}).get('holidate', '-')

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data={}

        data[ATTR_ID]   = self.marts.get(self._mart_code,{}).get('id', '-')
        data[ATTR_NAME] = self.marts.get(self._mart_code,{}).get('name', '-')

        data[ATTR_HOLIDAY_1] = self.marts.get(self._mart_code,{}).get('holiday_1', '-')
        data[ATTR_HOLIDAY_2] = self.marts.get(self._mart_code,{}).get('holiday_2', '-')

        return data

class GssuperAPI:
    """Gs Supermarket API"""
    def __init__(self, mart_kind, name, mart_code):
        """Initialize the Mart Holiday API"""
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self.result     = {}

    @Throttle(MIN_TIME_BETWEEN_API_UPDATES)
    def update(self):
        """Update function for updating api information."""
        try:

            url = GSSUPER_BSE_URL.format(parse.quote(self._name))

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            results = response.json()['results']

            gssuper_dict = {}

            for itm in results:
                if itm['shopCode'] != self._mart_code:
                    continue

                gssuper_dict[itm['shopCode']] = {
                    'id'        :  itm['shopCode'],
                    'name'      : itm['shopName'],
                    'tel'       : itm['phone'],
                    'address'   : itm['address'],

                    'holiday_1' : ConvertGssuperToComm(itm['closedDate1']),
                    'holiday_2' : ConvertGssuperToComm(itm['closedDate2']),
                    'holiday_3' : ConvertGssuperToComm(itm['closedDate3']),
                    'holiday_4' : ConvertGssuperToComm(itm['closedDate4']),
                }

#            if itm['shopName'] != self._name:
#                _LOGGER.info(self._name+'의 마트 코드가 정확하지 않습니다. 입력값: '+self._name+'검색값: '+ itm['shopName'])
#            if itm['shopCode'] != self._mart_code:
#                raise Exception('마트 이름이 정확하지 않습니다.')

            self.result = gssuper_dict

        except Exception as ex:
            _LOGGER.error('Failed to update GS SuperMart API status Error: %s', ex)
            raise

class GssuperSensor(Entity):
    def __init__(self, mart_kind, name, icon, mart_code, api):
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self._api       = api
        self._icon  = icon
        self._state = None
        self.marts  = {}

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return 'GS슈퍼마켓({})'.format(self._name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return DEFAULT_MART_ALPHA_ICON.format(self._mart_kind)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def attribution(self):
        """Return the attribution."""
        return 'Modified by 별명짓기귀찮음'

    @Throttle(MIN_TIME_BETWEEN_SENSOR_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        self._api.update()
        self.marts = self._api.result

        dt = datetime.now()

        try:
            hol_2 = datetime.strptime(self.marts[self._mart_code]['holiday_2'], "%Y-%m-%d")
            hol_1 = datetime.strptime(self.marts[self._mart_code]['holiday_1'], "%Y-%m-%d")

            if dt > hol_2 + timedelta(days=1):
                self._state = None
            elif dt > hol_1 + timedelta(days=1):
                self._state = self.marts[self._mart_code]['holiday_2']
            else:
                self._state = self.marts[self._mart_code]['holiday_1']
        except:
            self._state = None

    @property
    def device_state_attributes(self):
        """Attributes."""
        return self.marts[self._mart_code]
