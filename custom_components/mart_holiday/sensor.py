import logging
import re
import requests
import calendar
import voluptuous as vol
from bs4 import BeautifulSoup
from urllib import parse
import json

import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_API_KEY, CONF_ICON)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import DOMAIN, SW_VERSION, _COSTCO_STORES, CONF_MART_KIND, CONF_MART_CODE, CONF_NAME, CONF_AREA, MANUFACT, _AREA, LMART_SEARCH_URL, EMART_BSE_URL, EMART_IMSI_URL, LMART_BSE_URL, HOMEPLUS_BSE_URL, HOMEPLUS_EXPRESS_BSE_URL,GSSUPER_BSE_URL

_LOGGER = logging.getLogger(__name__)

CONF_MARTS      = 'marts'

DEFAULT_MART_ALPHA_ICON = 'mdi:alpha-{}-box'

COMM_DATE_FORMAT = '{}-{}-{}'

SCAN_INTERVAL = timedelta(seconds=14400)

ATTR_NAME = 'name'
ATTR_ID   = 'id'
ATTR_TEL  = 'tel'
ATTR_ADDR = 'address'

ATTR_HOLIDAY = 'holiday'
ATTR_HOLIDAY_1 = 'holiday_1'
ATTR_HOLIDAY_2 = 'holiday_2'
ATTR_HOLIDAY_3 = 'holiday_3'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MART_KIND): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_MART_CODE): cv.string,
})

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add a entity from a config_entry."""
    mart_kind = config_entry.data[CONF_MART_KIND]
    mart_code = config_entry.data[CONF_MART_CODE]
    mart_name = config_entry.data[CONF_NAME]

    sensors = []

    if mart_kind == 'e':
        try:
#            eAPI    = EMartAPI( hass, mart_kind, mart_name, mart_code, area )
            eAPI    = EMartImsiAPI( hass, mart_kind, mart_name, mart_code )
            eSensor = EMartSensor( mart_kind, mart_name, mart_code, eAPI )
            await eSensor.async_update()
            sensors += [eSensor]
        except Exception as ex:
            _LOGGER.error('Failed to update EMart API status Error: %s', ex)

    if mart_kind == 'l':
        try:
            lotteAPI    = LotteMartAPI( hass, mart_kind, mart_name, mart_code )
            lotteSensor = LotteMartSensor( mart_kind, mart_name, mart_code, lotteAPI )
            await lotteSensor.async_update()
            sensors += [lotteSensor]
        except Exception as ex:
            _LOGGER.error('Failed to update LotteMart API status Error: %s', ex)


    if mart_kind == 'h':
        try:
            homeplusAPI    = HomeplusAPI( hass, mart_kind, mart_name, mart_code )
            homeplusSensor = HomeplusSensor( mart_kind, mart_name, mart_code, homeplusAPI )
            await homeplusSensor.async_update()
            sensors += [homeplusSensor]
        except Exception as ex:
            _LOGGER.error('Failed to update Homeplus API status Error: %s', ex)


    if mart_kind == 'c':
        try:
            costcoAPI     = CostcoAPI( mart_kind, mart_name, mart_code )
            costcoSensor  = CostcoSensor( mart_kind, mart_name, mart_code, costcoAPI )
            costcoSensor.update()
            sensors += [costcoSensor]
        except Exception as ex:
            _LOGGER.error('Failed to update Costco API status Error: %s', ex)


    if mart_kind == 'g':
        try:
            gssuperAPI      = GssuperAPI( hass, mart_kind, mart_name, mart_code)
            gssuperSensor   = GssuperSensor( mart_kind, mart_name, mart_code, gssuperAPI)
            await gssuperSensor.async_update()
            sensors += [gssuperSensor]
        except Exception as ex:
            _LOGGER.error('Failed to update GS SuperMart API status Error: %s', ex)


    async_add_entities(sensors, True)


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
    if val is None:
        return '-'

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

                if len(tmp32[1]) == 1:
                    tmp32[1] = '0' + tmp32[1]

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

                if len(tmpNone[1]) == 1:
                     tmpNone[1] = '0' + tmpNone[1]

                if ( pMonth == '12' and tmpNone[0] == '01' ):
                     pYear = str(int(pYear) + 1)

                rslt = COMM_DATE_FORMAT.format(pYear, tmpNone[0], tmpNone[1])
                return rslt

            # 0.0 처리
            if len(tmp32) == 1:
                tmpNone =  val.split(".")
                if len(tmpNone) > 1:
                    tmpNone[0] = tmpNone[0]
                    tmpNone[1] = tmpNone[1]

                if len(tmpNone[1]) == 1:
                    tmpNone[1] = '0' + tmpNone[1]

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
    if val is None:
        return None

    tmp = val.split("-")

    if len(tmp) > 1:
        return datetime(year=int(tmp[0]), month=int(tmp[1]), day=int(tmp[2]))
    else:
        return None

class EMartAPI:
    """EMart API."""
    def __init__(self, hass, mart_kind, name, mart_code, area):
        """Initialize the EMart API."""
        self._hass      = hass
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self._area      = area
        self.result     = {}

    async def update(self):
        """Update function for updating api information."""
        try:
            dt = datetime.now()

            pYear  = dt.strftime("%Y")
            pMonth = dt.strftime("%m")

            url = EMART_BSE_URL
            url = url.format(self._area, pYear, pMonth)

            session = async_get_clientsession(self._hass)

            response = await session.get(url, timeout=30)
            response.raise_for_status()

            json_param = await response.json(content_type='text/html')

            #param 정보 추출
            param = json_param['param']

            #년도
            rYear      = param.get('year', '-')
            rYearPlus  = param.get('yearPlus', '-')
            rYearMinus = param.get('yearMinus', '-')

            #월
            rMonth      = param.get('month', '-')
            rMonthPlus  = param.get('monthPlus', '-')
            rMonthMinus = param.get('monthMinus', '-')

            #dateList 정보 추출
            emartJijum = json_param['dateList']

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

                session = async_get_clientsession(self._hass)

                response = await session.get(url, timeout=30)
                response.raise_for_status()

                json_param = await response.json(content_type='text/html')

                emartJijumN = json_param['dateList']

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

class EMartImsiAPI:
    """EMart API."""
    def __init__(self, hass, mart_kind, name, mart_code):
        """Initialize the EMart API."""
        self._hass      = hass
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self.result     = {}

    async def update(self):
        """Update function for updating api information."""
        try:
            dt = datetime.now()

            pYear  = dt.strftime("%Y")
            pMonth = dt.strftime("%m")

            url = EMART_IMSI_URL
            url = url.format(self._mart_code)

            session = async_get_clientsession(self._hass)

            response = await session.get(url, timeout=30)
            response.raise_for_status()

            html = await response.text()

            soup = BeautifulSoup(html, "lxml")

            contents = soup.find("dt", {"class": "icon-closed"}).find_next_siblings("dd")

            holi = contents[0].text.strip()

            r = re.compile("\d{1,2}\/\d{1,2}")
            rtn = r.findall(holi)

            holi1 = '-'
            holi2 = '-'
            holi3 = '-'

            if len(rtn) > 0:
                holi1 = rtn[0]

            if len(rtn) > 1:
                holi2 = rtn[1]

            if len(rtn) > 2:
                holi3 = rtn[2]

            emart_dict = {}

            nowDt = dt.strftime("%d")

            nextOffday = nowDt

            #param 정보 추출
            emart_dict[self._mart_code] = {
                        'jijum_id': self._mart_code,
                        'name'    : self._name,

                        'holiday_1' : ConvertLmartToComm(holi1) if len(rtn) > 0 else holi1,
                        'holiday_2' : ConvertLmartToComm(holi2) if len(rtn) > 1 else holi2,
                        'holiday_3' : ConvertLmartToComm(holi3) if len(rtn) > 2 else holi3,

                        'year'         : pYear,
                        'month'        : pMonth,
                        'next_holiday' : nextOffday
                    }

            self.result = emart_dict
            #_LOGGER.debug('EMart API Request Result: %s', self.result)
        except Exception as ex:
            _LOGGER.error('Failed to update EMart Imsi API status Error: %s', ex)
            raise




class EMartSensor(Entity):
    def __init__(self, mart_kind, name, mart_code,  api):
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self._entity_id = None

        self._api       = api

        self._holidate  = None

        self._state     = None
        self.marts      = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._entity_id is None:
            self._entity_id = 'mart_holiday_{}_{}'.format(self._mart_kind, self._mart_code)
            return self._entity_id
        return '이마트({})'.format(self._name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return DEFAULT_MART_ALPHA_ICON.format(self._mart_kind)

    @property
    def state(self):
        """Return the state of the sensor."""
#        next_offday = '-'
#        for key in self.marts:
#            next_offday = self.marts[key].get('next_holiday', '-')
#            if next_offday != '-':
#                next_offday = COMM_DATE_FORMAT.format(self.marts[key].get('year', '-'), self.marts[key].get('month','-'), next_offday)
#        return next_offday
        return self._holidate


    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api.update()
        marts_dict = self._api.result

        holiday_1 = marts_dict[self._mart_code].get('holiday_1', '')
        holiday_2 = marts_dict[self._mart_code].get('holiday_2', '')

        dt = datetime.now()

        if holiday_2 != '-':
            dt_holiday_1 = Comm2Date(holiday_1)
            dt_holiday_2 = Comm2Date(holiday_2)

            self._holidate = holiday_1 if dt <= dt_holiday_1 + timedelta(days=1) else holiday_2
        else:
            self._holidate = holiday_1

        #self._holidate = holidate

        #휴무일이 현재일자보다 이후면 '-'로 상태표시
        if ( self._holidate != '-' and dt > Comm2Date(self._holidate) ):
            self._holidate = '-'

        self.marts = marts_dict

    @property
    def extra_state_attributes (self):
        """Attributes."""
        return self.marts[self._mart_code]

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "connections": {(self._mart_kind, self._mart_code)},
            "identifiers": {
                (
                    DOMAIN,
                    self._mart_kind,
                    self._mart_code,
                )
            },
            "manufacturer": MANUFACT,
            "model": "대형마트 휴무일",
            "name": "대형마트 휴무일(E마트)",
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._mart_code),
            "DeviceEntryType": "service",
        }



class LotteMartAPI:
    """LotteMart API."""
    def __init__(self, hass, mart_kind, name, brnchCd):
        """Initialize the Mart Holiday API."""

        self._hass      = hass
        self._mart_kind = mart_kind
        self._name      = name
        self._brnchCd   = brnchCd
        self.result     = {}

    async def update(self):
        """Update function for updating api information."""
        try:
            dt = datetime.now()

            url = LMART_SEARCH_URL
            url = url.format(self._brnchCd)

            session = async_get_clientsession(self._hass)

            response = await session.post(url, timeout=30)
            response.raise_for_status()

            html = await response.text()

            soup = BeautifulSoup(html, "lxml")


            day_off = soup.select_one('span.day-off').text
            address = soup.select_one('div.address').text

            time = soup.select_one('span.time').text
            call = soup.select_one('span.call').text

            dict ={}

            holidate = day_off

            #_LOGGER.error(f'[{DOMAIN}] holidate, %s', holidate)

            # 00/00 처리
            r = re.compile("\d{1,2}\/\d{1,2}")
            rtn = r.findall(holidate)

            _LOGGER.debug(f'[{DOMAIN}] rtn, %s', len(rtn))

            dict[self._brnchCd]= {
                'id'       : self._brnchCd,
                'name'     : self._brnchCd,

                'address'  : address,
                'bussiness_hours'     : time,
                'tel'      : call,

                'holidate' :  holidate,
                'holiday_1' : ConvertLmartToComm(rtn[0]),
                'holiday_2' : (ConvertLmartToComm(rtn[1]) if len(rtn) > 1 else None)
            }

            self.result = dict
        except Exception as ex:
            _LOGGER.error('Failed to update LotteMart API status Error: %s', ex)
            raise

class LotteMartSensor(Entity):
    def __init__(self, mart_kind, name, brnchCd, api):
        self._mart_kind = mart_kind
        self._name      = name
        self._entity_id = None

        self._brnchCd   = brnchCd
        self._holidate  = None

        self._api   = api
        self._state = None
        self.marts  = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._brnchCd)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._entity_id is None:
            self._entity_id = 'mart_holiday_{}_{}'.format(self._mart_kind, self._brnchCd)
            return self._entity_id
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

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api.update()
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
    def extra_state_attributes (self):
        """Attributes."""
        return self.marts.get(self._brnchCd,{})

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "connections": {(self._mart_kind, self._brnchCd)},
            "identifiers": {
                (
                    DOMAIN,
                    self._mart_kind,
                    self._brnchCd,
                )
            },
            "manufacturer": MANUFACT,
            "model": "대형마트 휴무일",
            "name": "대형마트 휴무일(롯데마트)",
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._brnchCd),
            "DeviceEntryType": "service",
        }

class HomeplusAPI:
    """Homeplus API."""
    def __init__(self, hass, mart_kind, name, mart_code):
        """Initialize the Mart Holiday API."""
        self._hass      = hass
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self.result     = {}

    async def update(self):
        """Update function for updating api information."""
        try:
            dt = datetime.now()

            pYear  = dt.strftime("%Y")
            pMonth = dt.strftime("%m")

            url = HOMEPLUS_BSE_URL
            url = url.format(self._mart_code)

            session = async_get_clientsession(self._hass)

            response = await session.get(url, timeout=30)
            response.raise_for_status()

            page = await response.text()

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
    def __init__(self, mart_kind, name, mart_code, api):
        self._mart_kind  = mart_kind
        self._name       = name
        self._mart_code  = mart_code
        self._holidate   = None
        self._entity_id  = None

        self._api   = api

        self._state = None
        self.marts  = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._entity_id is None:
            self._entity_id = 'mart_holiday_{}_{}'.format(self._mart_kind, self._mart_code)
            return self._entity_id
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

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api.update()
        marts_dict = self._api.result

        self.marts = marts_dict

        holiday = self.marts.get(self._mart_code,{}).get('holiday', '-')

        self._holidate = '-' if holiday == '' else holiday

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

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "connections": {(self._mart_kind, self._mart_code)},
            "identifiers": {
                (
                    DOMAIN,
                    self._mart_kind,
                    self._mart_code,
                )
            },
            "manufacturer": MANUFACT,
            "model": "대형마트 휴무일",
            "name": "대형마트 휴무일(Homeplus)",
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._mart_code),
            "DeviceEntryType": "service",
        }



class CostcoAPI:
    """Costco API."""
    def __init__(self, mart_kind, name, mart_code):
        """Initialize the Mart Holiday API."""
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self.result     = {}

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
    def __init__(self, mart_kind, name, mart_code, api):
        self._mart_kind  = mart_kind
        self._name       = name
        self._mart_code  = mart_code
        self._holidate   = None
        self._entity_id  = None

        self._api   = api

        self._state = None
        self.marts  = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._entity_id is None:
            self._entity_id = 'mart_holiday_{}_{}'.format(self._mart_kind, self._mart_code)
            return self._entity_id
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

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "connections": {(self._mart_kind, self._mart_code)},
            "identifiers": {
                (
                    DOMAIN,
                    self._mart_kind,
                    self._mart_code,
                )
            },
            "manufacturer": MANUFACT,
            "model": "대형마트 휴무일",
            "name": "대형마트 휴무일(Costco)",
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._mart_code),
            "DeviceEntryType": "service",
        }


class GssuperAPI:
    """Gs Supermarket API"""
    def __init__(self, hass, mart_kind, name, mart_code):
        """Initialize the Mart Holiday API"""
        self._hass      = hass
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self.result     = {}

    async def update(self):
        """Update function for updating api information."""
        try:

            url = GSSUPER_BSE_URL.format(parse.quote(self._name))

            session = async_get_clientsession(self._hass)

            response = await session.get(url, timeout=30)
            response.raise_for_status()

            json_results = await response.json()

            results = json_results['results']

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
    def __init__(self, mart_kind, name, mart_code, api):
        self._mart_kind = mart_kind
        self._name      = name
        self._mart_code = mart_code
        self._entity_id = None

        self._api       = api

        self._state = None
        self.marts  = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._entity_id is None:
            self._entity_id = 'mart_holiday_{}_{}'.format(self._mart_kind, self._mart_code)
            return self._entity_id
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

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api.update()
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
    def extra_state_attributes (self):
        """Attributes."""
        return self.marts[self._mart_code]

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "connections": {(self._mart_kind, self._mart_code)},
            "identifiers": {
                (
                    DOMAIN,
                    self._mart_kind,
                    self._mart_code,
                )
            },
            "manufacturer": MANUFACT,
            "model": "대형마트 휴무일",
            "name": "대형마트 휴무일(GS슈퍼마켓)",
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._mart_code),
            "DeviceEntryType": "service",
        }
