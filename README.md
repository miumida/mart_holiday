# 주말에 마트 가도 될까요?(대형마트 휴무일) Sensor

![HAKC)][hakc-shield]
![Version v1.1.4][version-shield]

주말에 마트 가도 될까요?(대형마트 휴무일) Sensor for Home Assistant<br>
E마트/롯데마트/Homeplus/Costco/GS슈퍼마켓의 휴무일을 나타내주는 Home Assistant Sensor 입니다.<br>
롯데마트의 경우, 지점 담당자가 휴무일을 제대로 입력하지 않거나 갱신하지 않아 제대로 조회되지 않는 경우도 있습니다.<br>
![mart_holiday_sensor](https://github.com/miumida/mart_holiday/blob/master/mart_holiday_sensor.png?raw=true)<br>

![screenshot_e](https://github.com/miumida/martholiday/blob/master/Screenshot_e.png)<br>
![screenshot_l](https://github.com/miumida/martholiday/blob/master/Screenshot_l.png)<br>
![screenshot_h](https://github.com/miumida/martholiday/blob/master/Screenshot_h.png)<br>
![screenshot_c](https://github.com/miumida/martholiday/blob/master/Screenshot_c.png)<br>
<br><br>
## Version history
| Version | Date        |               |
| :-----: | :---------: | ------------- |
| v1.0.0    | 2019.11.29  | First version  |
| v1.0.1    | 2019.12.03  | 롯데마트 00월 00일로 등록된 휴무일 처리추가 |
| v1.0.2    | 2019.12.09  | 코스트코 휴무일 센서 추가. 롯데마트 휴무일 센서 수정. |
| v1.0.3    | 2019.12.11  | 이마트/롯데마트/코스트코 휴무일 센서 오류 수정. |
| v1.0.4    | 2019.12.27  | 롯데마트/이마트 가까운 휴무일 체크로직 수정. |
| v1.0.5    | 2020.01.05  | 코스트코 휴무일 센서 오류 수정. |
| v1.0.6    | 2020.01.16  | 롯데마트 '00월00일' 휴무일 처리 추가. |
| v1.0.7    | 2020.03.09  | GS슈퍼마켓 휴무일 센서 추가(source by 별명짓기귀찮음[kws9271]).<br> 롯데마트 휴무일 오류 수정. |
| v1.0.8    | 2021.03.09  | manifest.json 파일 version 속성 추가. |
| v1.0.9    | 2021.05.21  | 롯데마트 00/00 일자 처리 수정. |
| v1.1.0    | 2021.05.25  | 통합구성요소 적용. |
| v1.1.1    | 2021.08.14  | 이마트 휴무일로직 임시수정 |
| v1.1.2    | 2021.08.25  | 이마트 휴무일로직 오류 수정. |
| v1.1.3    | 2021.08.25  | 이마트 휴무일 가져오기 로직 개선(휴무일 아이콘기준으로 찾기). |
| v1.1.4    | 2021.12.15  | Fix bug |
| v1.1.5    | 2022.06.27  | Fix bug |
| v1.1.6    | 2022.07.08  | bs4 requirement version 변경 |
| v1.1.10    | 2022.07.12  | 롯데마트 홈페이지 개편에 따른 휴무일로직 변경 |


<br><br>
## Installation
### Manual
- HA 설치 경로 아래 custom_components 에 파일을 넣어줍니다.<br>
  `<config directory>/custom_components/mart_holiday/__init__.py`<br>
  `<config directory>/custom_components/mart_holiday/manifest.json`<br>
  `<config directory>/custom_components/mart_holiday/sensor.py`<br>
- configuration.yaml 파일에 설정을 추가합니다.<br>
- Home-Assistant 를 재시작합니다<br>
### HACS
- HACS > SETTINGS 메뉴 선택
- ADD CUSTOM REPOSITORY에 'https://github.com/miumida/mart_holiday' 입력하고 Category에 'integration' 선택 후, 저장
- HACS > INTEGRATIONS 메뉴 선택 후, 검색하여 설치
<br><br>
## Usage
### Custom Integration
- 구성 > 통합구성요소 > 통합구성요소 추가하기 > 대형마트휴무일 선택 > 설정값 입력 후, 확인.

### Configuration(yaml) : Custom Integration으로 등록해주세요!
- HA설정에 대형마트 휴무일 센서를 추가합니다<br>
- v1.1.7 이상부터는 통합구성요소만 지원합니다.<br>

### 센서별 설정값

|옵션|값|
|--|--|
|mart_kind| (필수) 마트 종류 |
|name| (옵션) 마트 이름(지점). 지정하지 않으면 'mart'로 저장됨<br>(필수) GS슈퍼마켓은 마트이름으로 검색하여 정확한 이름 입력필요 |
|mart_code| (필수) 마트 지점코드 or 마트 지점ID |


### 마트 종류 (mart_kind) 옵션

|종류|설명|
|--|--|
|e|E마트|
|l|롯데마트|
|h|Homeplus|
|c|Costco|
|g|GS슈퍼마켓|


### 마트별 코드 확인(mart_code)
마트에 따라 마트코드를 확인하는 방법은 아래와 같다.
#### E마트
|지역|코드|지역|코드|
|--|--|--|--|
|서울|A|경상|J|
|인천|C|울산|G|
|경기|I|부산|B|
|대전|F|전라|L|
|세종|Q|광주|E|
|충청|N|강원|H|
|대구|D|제주|P|
- 지역코드는 표를 참고하고, 마트코드는 '20191031_이마트_지점코드.txt'에서 코드를 찾으면 된다.<br>
<br><br>
#### 롯데마트
- 롯데마트 지점찾기 페이지로 접속하여 원하는 롯데마트 지점을 검색한다.<br>
  지점찾기 페이지 : http://company.lottemart.com/shop/shop_search_type.asp?#schWord
![lotte_search_1](https://github.com/miumida/mart_holiday/blob/master/img/lotte_search_n_1.png?raw=true)<br>
- 조회된 목록에서 원하는 지점의 지점명과 동일하게 마트코드로 사용한다.
![lotte_search_2](https://github.com/miumida/mart_holiday/blob/master/img/lotte_search_n_2.png?raw=true)<<br>
<br><br>
#### Homeplus
- 홈플러스 매장명 찾기를 통해 원하는 홈플러스 매장을 검색한다<br>
  매장명 검색 페이지 :  http://corporate.homeplus.co.kr/STORE/HyperMarket.aspx
  ![homeplus_search_1](https://github.com/miumida/martholiday/blob/master/img/homeplus_search_1.png)<br>
- 조회된 목록에서 하는 매장의 '입점 정보'를 클릭한다.
- 매장정보가 나타나면 주소창에 있는 sn=0017 부분에서 = 뒤에 있는 `0017`을 마트코드로 사용한다.
![homeplus_search_2](https://github.com/miumida/martholiday/blob/master/img/homeplus_search_2.png)<br>
<br><br>
#### Costco
|코드|마트명|코드|마트명|
|--|-------------|--|-------------|
|01|대전점|09|양재점|
|02|대구점|10|광명점|
|03|세종점|11|하남점|
|04|대구 혁신도시점|12|송도점|
|05|천안점|13|양평점|
|06|부산점|14|상봉점|
|07|울산점|15|일산점|
|08|공세점|16|의정부점|
- 코스트코는 매장이 현재 16개로 홈페이지에서 정보를 가져와서 휴무일을 표시하지 않는다.
- 코스트코 홈페이지에 나와있는 16개의 매장을 기준으로 2자리 숫자로 단순히 코드로 사용한다.
  해당 지점에 대해서는 코드표를 확인하여, mart_code에 사용한다.
<br><br>
#### GS슈퍼마켓
- GS슈퍼마켓 매장명 찾기를 통해 원하는 GS슈퍼마켓 매장을 검색한다
  매장명 검색 페이지: http://gsthefresh.gsretail.com/thefresh/ko/market-info/find
![gssuper_search_1](https://github.com/miumida/martholiday/blob/master/img/gssupermarket_search_1.png)<br>
- 조회된 목록에서 원하는 매장의 이름을 아래 주소에서 넣어 마트코드(shopCode)를 확인한다.
  http://gsthefresh.gsretail.com/thefresh/ko/market-info/find-storelist?searchShopName=[마트이름]
![gssuper_search_2](https://github.com/miumida/martholiday/blob/master/img/gssupermarket_search_2.png)<br>
<br><br>
### Thx.
- 별명짓기귀찮음님 GS슈퍼마켓 소스제공 감사합니다:D
- 저장장치님 이마트 휴무일 찾는 부분 아이디어 제공해주셔서 감사합니다:D

[version-shield]: https://img.shields.io/badge/version-v1.1.10-orange.svg
[hakc-shield]: https://img.shields.io/badge/HAKC-Enjoy-blue.svg
