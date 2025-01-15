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
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import DOMAIN, SW_VERSION, _COSTCO_STORES, CONF_MART_KIND, CONF_MART_CODE, CONF_NAME, CONF_AREA, MODEL, MANUFACT, _MART_KIND, _MART_URL, _MART_NAME, LMART_SEARCH_URL, EMART_IMSI_URL, LMART_BSE_URL, HOMEPLUS_BSE_URL, HOMEPLUS_EXPRESS_BSE_URL,GSSUPER_BSE_URL
from .const import ATTR_NAME, ATTR_ID, ATTR_TEL, ATTR_ADDR, ATTR_HOLIDAY, ATTR_HOLIDAY_1, ATTR_HOLIDAY_2, ATTR_HOLIDAY_3, ATTR_HOLIDAY_4, ATTR_NEXT_HOLIDAY, ATTR_BUSSINESS_HOURS, ATTR_OPERTIME, ATTR_HOLIDATE, ATTR_DAYOFF, DEFAULT_MART_ALPHA_ICON

_LOGGER = logging.getLogger(__name__)

COMM_DATE_FORMAT = '{}-{}-{}'

SCAN_INTERVAL = timedelta(seconds=14400)


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

    try:
        api = martAPI(hass, config_entry)

        await api.update()

        mart = martSensor(api)

        sensors += [mart]
    except Exception as ex:
        _LOGGER.error(f'[{DOMAIN}] Failed to update mart API status Error: %s', ex)

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

        # 0/0 처리
        elif len(tmp) == 2:
            if len(tmp[0]) == 1:
                tmp[0] = '0' + tmp[0]
            if len(tmp[1]) == 1:
                tmp[1] = '0' + tmp[1]

            if ( pMonth == '12' and tmp[0] == '01' ):
                pYear = str(int(pYear) + 1)
            
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
        return datetime(year=int(tmp[0]), month=int(tmp[1]), day=int(tmp[2]), hour=23, minute=59, second=59)
    else:
        return None

class martAPI:
    """mart API."""
    def __init__(self, hass, config_entry):
        self._hass  = hass
        self._entry = config_entry

        self._mart_kind = config_entry.data[CONF_MART_KIND]
        self._mart_code = config_entry.data[CONF_MART_CODE]
        self._mart_name = config_entry.data[CONF_NAME]

        self._session   = async_get_clientsession(self._hass)

        self._entity_id = generate_entity_id('mart_holiday.mart_{}', '{}_{}'.format(self._mart_kind, self._mart_code), hass= hass)

        self.result = {}

    async def _get(self, url, json=False):
        response = await self._session.get(url, timeout=30)
        response.raise_for_status()

        if json:
            html = await response.json()
            return html
        else:
            html = await response.text()
            return html 


    async def _post(self, url):
        response = await self._session.post(url, timeout=30)
        response.raise_for_status()

        html = await response.text()
        return html

    async def update(self):
        param =  parse.quote(self._mart_name) if self._mart_kind == 'g' else self._mart_code
        url = _MART_URL[self._mart_kind].format(param)

        if self._mart_kind == 'e':
            self.parseEmart( await self._get(url) )
        elif self._mart_kind == 'h':
            self.parseHomeplus( await self._get(url) )
        elif self._mart_kind == 'g':
            self.parseGSSuper( await self._get(url, True) )
        elif self._mart_kind == 'c':
            self.calcCostco()
        else:
            self.parseLotte( await self._post(url) )

    def parseEmart(self, html):
        dict = {}

        soup = BeautifulSoup(html, "lxml")

        contents = soup.find("dt", {"class": "icon-closed"}).find_next_siblings("dd")

        holi = contents[0].text.strip()

        r = re.compile(r"\d{1,2}\/\d{1,2}")
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
            
        arr_holi = []
        
        for day in rtn:
            arr_holi.append(self.s2d(ConvertLmartToComm(day)))

        dt = datetime.now()

        nowDt = dt.strftime("%d")

        nextOffday = nowDt

        #param 정보 추출
        dict[self._mart_code] = {
                    ATTR_ID   : self._mart_code,
                    ATTR_NAME : self._mart_name,

                    ATTR_HOLIDATE  : self.get_next_holiday(arr_holi, True),
                    ATTR_HOLIDAY_1 : ConvertLmartToComm(holi1) if len(rtn) > 0 else holi1,
                    ATTR_HOLIDAY_2 : ConvertLmartToComm(holi2) if len(rtn) > 1 else holi2,
                    ATTR_HOLIDAY_3 : ConvertLmartToComm(holi3) if len(rtn) > 2 else holi3,

                    ATTR_NEXT_HOLIDAY : nextOffday
                }

        self.result = dict

    def parseLotte(self, html):
        dict = {}

        soup = BeautifulSoup(html, "lxml")

        day_off = soup.select_one('span.day-off').text
        address = soup.select_one('div.address').text

        time = soup.select_one('span.time').text
        call = soup.select_one('span.call').text

        holidate = day_off

        # 00/00 처리
        r = re.compile(r"\d{1,2}\/\d{1,2}")
        rtn = r.findall(holidate)
        
        arr_holi = []
        
        for day in rtn:
            arr_holi.append(self.s2d(ConvertLmartToComm(day)))
            
        holidate = self.get_next_holiday(arr_holi, True)

        dict[self._mart_code]= {
            ATTR_ID    : self._mart_code,
            ATTR_NAME  : self._mart_code,
            ATTR_TEL   : call,

            ATTR_ADDR  : address,
            ATTR_BUSSINESS_HOURS  : time,
            ATTR_DAYOFF: day_off,
            
            ATTR_HOLIDATE :  holidate,
            ATTR_HOLIDAY_1 : ConvertLmartToComm(rtn[0]),
            ATTR_HOLIDAY_2 : (ConvertLmartToComm(rtn[1]) if len(rtn) > 1 else None)
        }

        self.result = dict


    def parseHomeplus(self, html):
        dict = {}

        soup = BeautifulSoup(html, 'html.parser')
        storeDetail = soup.find(id="store_detail01")

        tds = storeDetail.find_all("td")

        addr     = tds[0].get_text().strip()
        holiday  = tds[1].get_text().strip()
        tel      = tds[2].get_text().strip()
        opertime = tds[3].get_text().strip()

        #휴무일 추출 : 2019-03-24 형태의 값만 추출한다.
        r = re.compile(r"\d{4}-\d{2}-\d{2}")

        rtn = r.findall(holiday)

        if len(rtn) > 0:
            holiday = min(rtn)

        dict[self._mart_code]= {
            ATTR_ID    : self._mart_code,
            ATTR_NAME  : self._mart_name,
            ATTR_TEL   : tel,

            ATTR_ADDR     : addr,
            ATTR_HOLIDAY  : holiday,
            ATTR_OPERTIME : opertime
        }

        # 휴무이을 딕셔너리에 추가
        arr_holi = []
        cnt = 1
        for tmp in rtn:
            dict[self._mart_code].update( {'holiday_{}'.format(str(cnt)):tmp} )
            arr_holi.append(self.s2d(tmp))
            cnt += 1
            
        dict[self._mart_code].update( {ATTR_HOLIDATE:self.get_next_holiday(arr_holi, True)} )

        self.result = dict


    def parseGSSuper(self, html):
        results = html['results']

        arr_holi = []
        dict = {}

        for itm in results:
            if itm['shopCode'] != self._mart_code:
                continue
            
            close1 = ConvertGssuperToComm(itm['closedDate1'])
            close2 = ConvertGssuperToComm(itm['closedDate2'])
            close3 = ConvertGssuperToComm(itm['closedDate3'])
            close4 = ConvertGssuperToComm(itm['closedDate4'])
            
            if close1 is not None:
                arr_holi.append(self.s2d(close1))
            
            if close2 is not None:
                arr_holi.append(self.s2d(close2))
            
            if close3 is not None:
                arr_holi.append(self.s2d(close3))
            
            if close4 is not None:
                arr_holi.append(self.s2d(close4))
            
            holidate = self.get_next_holiday(arr_holi, True)

            dict[itm['shopCode']] = {
                ATTR_ID     : itm['shopCode'],
                ATTR_NAME   : itm['shopName'],
                ATTR_TEL    : itm['phone'],
                ATTR_ADDR   : itm['address'],
                
                ATTR_HOLIDATE  : holidate,

                ATTR_HOLIDAY_1 : close1,
                ATTR_HOLIDAY_2 : close2,
                ATTR_HOLIDAY_3 : close3,
                ATTR_HOLIDAY_4 : close4,
            }

        self.result = dict


    def calcCostco(self, year=None, month=None):
        """Update function for updating api information."""
        try:
            arr_holi = []
            
            dt = datetime.now()

            pYear  = dt.strftime("%Y") if year is None else year
            pMonth = dt.strftime("%m") if month is None else month

            nowDt = dt.strftime("%d")

            mart_dict ={}

            monthInfo = calendar.monthrange(int(pYear), int(pMonth))

            data_1st = datetime(year=int(pYear), month=int(pMonth), day=1)
            
            # 1월은 1/1일을 무조건 휴무일로 처리
            if ( int(pMonth) == 1 ):
                arr_holi.append(data_1st)

            costco_nm = _COSTCO_STORES[self._mart_code][0]
            costco_1st_holiday = _COSTCO_STORES[self._mart_code][1]
            costco_2nd_holiday = _COSTCO_STORES[self._mart_code][2]

            #둘째주
            addCnt_1st = 0
            addCnt_2nd = 0

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
            i = addCnt_1st
            while i < monthInfo[1]:
                if i > monthInfo[1]:
                    break

                tmp = data_1st + timedelta(days=i)

                month_tmp_1.append(tmp)

                i = i + 7

            #넷째주
            month_tmp_2 = []
            i = addCnt_2nd
            while i < monthInfo[1]:
                if i > monthInfo[1]:
                    break

                tmp = data_1st + timedelta(days=i)

                month_tmp_2.append(tmp)

                i = i + 7

            #휴무일
            holiday_1 = month_tmp_1[1]
            holiday_2 = month_tmp_2[3]
            
            arr_holi.append(month_tmp_1[1])
            arr_holi.append(month_tmp_2[3])

            #가까운 휴무일 지정
            holidate = self.get_next_holiday(arr_holi, True)

            mart_dict[self._mart_code]= {
                ATTR_ID       : self._mart_code,
                ATTR_NAME     : self._mart_name,

                ATTR_HOLIDATE   : holidate,
                ATTR_HOLIDAY_1  : self.d2s(arr_holi[0]),
                ATTR_HOLIDAY_2  : self.d2s(arr_holi[1]),
                ATTR_HOLIDAY_3  : (self.d2s(arr_holi[2]) if len(arr_holi) > 2 else '-'),
            }

            self.result = mart_dict

        except Exception as ex:
            _LOGGER.error('Failed to update Costco API status Error: %s', ex)
            raise
        
    def d2s(self, val):
        if val is None:
            return None
        
        if isinstance(val, str):
            val = datetime.strptime(val, "%Y-%m-%d")
        elif isinstance(val, datetime):
            pass
        else:
            return None
        
        return val.strftime("%Y-%m-%d")
    
    def s2d(self, val):
        if val is None:
            return None
        
        if isinstance(val, str):
            return datetime.strptime(val, "%Y-%m-%d")
        else:
            return None
        
    def get_next_holiday(self, arr, text=False):
        #현재 날짜 가져오기
        curr = datetime.today()
        
        next_dates = [date for date in sorted(arr) if date >= curr ]
        
        #결과가 없으면 None을 반환
        if not next_dates:
            return None

        #결과가 있으면 첫 번째 날짜를 반환
        return self.d2s(next_dates[0]) if text else next_dates[0]


class martSensor(Entity):
    def __init__(self, api):
        self._api       = api

        self._mart_kind = api._mart_kind
        self._mart_name = api._mart_name
        self._mart_code = api._mart_code

        self.entity_id  = api._entity_id

        self._holidate  = None

        self._state     = None
        self.marts      = {}

    @property
    def unique_id(self):
        """Return the entity ID."""
        return 'sensor.mart_holiday_{}_{}'.format(self._mart_kind, self._mart_code)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return _MART_NAME[self._mart_kind].format(self._mart_name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return DEFAULT_MART_ALPHA_ICON.format(self._mart_kind)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._holidate

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api.update()
        marts_dict = self._api.result

        self._holidate = marts_dict[self._mart_code].get(ATTR_HOLIDATE, '-')

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
            "model": MODEL,
            "name": "대형마트 휴무일({})".format(_MART_KIND[self._mart_kind]),
            "sw_version": SW_VERSION,
            "via_device": (DOMAIN, self._mart_code),
        }
