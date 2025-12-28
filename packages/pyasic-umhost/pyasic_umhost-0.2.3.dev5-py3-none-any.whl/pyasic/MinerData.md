
# Данные майнеров

## MinerData

Фундаментальный класс информации приходящей от майнеров из метода .get_data(). Далее о составе данных.

### ip и DeviceInfo
Соответствуют атрибутам .ip и .device_info
Класс DeviceInfo хранит в себе статическую или редко меняющуюся информацию.
Библиотека pyasic автоматически определяет тип устройства при создании и сохраняет в экземпляр класса DeviceInfo.
Является свойством класса (property) и создается на уровне бызового MinerProtocol
В качестве атрибутов имеет тип, модель и версию прошивки, а также атрибут algo - отвечающий за алгоритм записи и возврата значений 
exp. device_info=DeviceInfo(make=<MinerMake.ANTMINER: 'AntMiner'>, model=<AntminerModels.T21: 'T21'>, firmware=<MinerFirmware.STOCK: 'Stock'>, algo=<class 'pyasic.device.algorithm.sha256.SHA256Algo'>)

### Серийный номер, мак адрес, версия API, дата релиза, имя хоста
Соответствуют атрибутам .serial_number, .mac, .api_ver, .fw_ver, .hostname


### .sticker_hashrate и .expected_hashrate
Атрибут sticker_hashrate в классе MinerData представляет номинальный/заявленный хешрейт майнера, указанный на стикере/шильдике устройства или в спецификациях производителя.
Это теоретическая максимальная производительность майнера, которую производитель указывает в технических характеристиках в самых благоприятных условиях

Атрибут expected_hashrate. Это ожидаемый/расчетный хешрейт с учетом текущих условий. Используется для определения эффективности работы


### .expected_hashboards, .expected_chips, .expected_fans
.expected_hashboards - представляет собой ожидаемое количество хеш-плат (хешбордов) для конкретной модели майнера. Это теоретическое значение, основанное на спецификациях модели.
.expected_chips - теоретическое количество чипов на всех платах
.expected_fans - содержит информацию об ожидаемом количестве вентиляторов для конкретной модели майнера


### .env_temp, .wattage, .voltage
Атрибут env_temp содержит температуру окружающей среды вокруг майнера, обычно измеряемую в градусах Цельсия.
Атрибут wattage содержит текущую потребляемую мощность майнера в ваттах (Вт).
Атрибут voltage содержит рабочее напряжение майнера, обычно измеряемое в вольтах (В).


### .fans, .fan_psu
Атрибут fans (или fan) содержит информацию о вентиляторах майнера.
Атрибут fan_psu содержит информацию о скорости вращения вентиляторов блоков питания (Power Supply Unit - PSU) майнера. 


### .hashboards
Атрибут содержит подробную информацию о хеш-платах (хешбордах) майнера
exp. hashboards=[HashBoard(slot=0, hashrate=63981900000000.0, inlet_temp=None, outlet_temp=None, temp=45.0, chip_temp=50.0, chips=108, expected_chips=108, serial_number='HQDZYS0BDJEBB02DK', missing=False, tuned=None, active=None, voltage=None), ...]


### .config
Атрибут config представляет собой словарь, который содержит различные конфигурационные параметры майнера

exp. config=MinerConfig(pools=PoolConfig(groups=[PoolGroup(pools=[Pool(url='stratum+tcp://ru.btc.neopool.pro:3333', user='krasnprof190.T21x190x2017863', password='123'), ...], quota=1, name=None)]), fan_mode=FanModeNormal(mode='normal', minimum_fans=1, minimum_speed=0), temperature=TemperatureConfig(target=None, hot=None, danger=None), mining_mode=MiningModeNormal(mode='normal'), freq_level=FreqLevel(level='100')), fault_light=False, errors=[], is_mining=True, is_sleep=False, uptime=332038, pools=[PoolMetrics(url=PoolUrl(scheme=<Scheme.STRATUM_V1: 'stratum+tcp'>, host='ru.btc.neopool.pro', port=3333, pubkey=None), accepted=49746, rejected=14, get_failures=1, remote_failures=0, active=False, alive=False, index=0, user='krasnprof190.T21x190x2017863', pool_rejected_percent=0.028135048231511254, pool_stale_percent=0.0020096463022508037), PoolMetrics(url=PoolUrl(scheme=<Scheme.STRATUM_V1: 'stratum+tcp'>, host='ru.btc.neopool.com', port=3333, pubkey=None), accepted=47268, rejected=26, get_failures=0, remote_failures=0, active=True, alive=True, index=1, user='krasnprof190.T21x190x2017863', pool_rejected_percent=0.054975261132490384, pool_stale_percent=0.0), PoolMetrics(url=PoolUrl(scheme=<Scheme.STRATUM_V1: 'stratum+tcp'>, host='eu.btc.neopool.com', port=3333, pubkey=None), accepted=0, rejected=0, get_failures=0, remote_failures=0, active=False, alive=True, index=2, user='krasnprof190.T21x190x2017863', pool_rejected_percent=0.0, pool_stale_percent=0.0)], hashrate=191407320000000.0, wattage_limit=None, total_chips=324, nominal=True, percent_expected_chips=100, percent_expected_hashrate=106, percent_expected_wattage=None, temperature_avg=46, efficiency=None, efficiency_fract=None, datetime='2025-12-16T16:55:42.163563+03:00', timestamp=1765893342, make='AntMiner', model='T21', firmware='Stock', algo='SHA256')