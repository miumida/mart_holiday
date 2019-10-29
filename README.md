# 주말에 마트가도 될까요?(대형마트 휴무일) Sensor
주말에 마트가도 될까요?(대형마트 휴무일) Sensor for Home Assistant<br>
E마트/롯데마트/Homeplus의 휴무일을 나타내주는 Home Assistant Sensor 입니다.<br>

<br><br>
## Installation
- HA 설치 경로 아래 custom_components 에 파일을 넣어줍니다.<br>
  `<config directory>/custom_components/martholiday/__init__.py`<br>
  `<config directory>/custom_components/martholiday/manifest.json`<br>
  `<config directory>/custom_components/martholiday/sensor.py`<br>
- configuration.yaml 파일에 설정을 추가합니다.<br>
- Home-Assistant 를 재시작합니다<br>
<br><br>
## Usage
### configuration
- HA 설정에 대형마트 휴무일 sensor를 추가합니다.<br>
```yaml
sensor:
- platform: martholiday
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
```
<br><br>
### 마트 종류 (mart_kind) 옵션

|종류|설명|
|--|--|
|e|E마트|
|l|롯데마트|
|h|Homeplus|
