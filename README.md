# 주말에 마트 가도 될까요?(대형마트 휴무일) Sensor
주말에 마트 가도 될까요?(대형마트 휴무일) Sensor for Home Assistant<br>
E마트/롯데마트/Homeplus의 휴무일을 나타내주는 Home Assistant Sensor 입니다.<br>
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
| v1.0.6    | 2020.01.16  | 롯데마트 '00월00일' 휴무일 처리 추가 |

<br><br>
## Installation
- HA 설치 경로 아래 custom_components 에 파일을 넣어줍니다.<br>
  `<config directory>/custom_components/mart_holiday/__init__.py`<br>
  `<config directory>/custom_components/mart_holiday/manifest.json`<br>
  `<config directory>/custom_components/mart_holiday/sensor.py`<br>
- configuration.yaml 파일에 설정을 추가합니다.<br>
- Home-Assistant 를 재시작합니다<br>
<br><br>
## Usage
### configuration
- HA 설정에 대형마트 휴무일 sensor를 추가합니다.<br>
```yaml
sensor:
- platform: mart_holiday
  marts:
    - mart_kind: 'e'
      name: '창원점'
      mart_code: '1059'
      area: 'J'
    - mart_kind: 'l'
      name: '창원중앙점'
      mart_code: '0100161'
    - mart_kind: 'h'
      name: '창원점'
      mart_code: '0017'
    - mart_kind: 'c'
      name: '대구점'
      mart_code: '01'
```
### 기본 설정값

|옵션|값|
|--|--|
|platform| (필수) mart_holiday |
|marts| (필수) 센서로 등록할 마트 정보를 추가 |


### 센서별 설정값

|옵션|값|
|--|--|
|mart_kind| (필수) 마트 종류 |
|name| (옵션) 마트 이름(지점). 지정하지 않으면 'mart'로 저장됨 |
|mart_code| (필수) 마트 지점코드 or 마트 지점ID |
|area| (필수) E마트only. mart는 area코드를 가지고  |


### 마트 종류 (mart_kind) 옵션

|종류|설명|
|--|--|
|e|E마트|
|l|롯데마트|
|h|Homeplus|
|c|Costco|


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
  지점찾기 페이지 : http://company.lottemart.com/bc/branch/main.do?menuCd=BM0201&SITELOC=DB001
![lotte_search_1](https://github.com/miumida/martholiday/blob/master/img/lotte_search_1.png)<br>
- 조회된 목록에서 원하는 지점의 '지점사이트' 버튼을 클릭한다.
![lotte_search_2](https://github.com/miumida/martholiday/blob/master/img/lotte_search_2.png)<br>
- 지점사이트가 열리면 주소창에 마지막 부분의 brnchCd=0100161에서 = 뒤에 있는 `0100161`를 마트코드로 사용한다.
![lotte_search_3](https://github.com/miumida/martholiday/blob/master/img/lotte_search_3.png)<br>
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
<br>
