# Fineme B6 GPS Tracker - API & Integration Reference

## 1. 设备信息

| 项目 | 值 |
|---|---|
| 设备品牌 | Fineme (方案) |
| 设备型号 | B6 (Model 513) |
| 设备名称 | B6-05086 |
| Device ID | 714574708 |
| IMEI/SN | 865016309205086 |
| 芯片方案 | S281 (汇顶/移远 GPS 定位芯片) |
| 固件版本 | TY281V1.3 / S281_V1.1.0_T6 (2023-06-30) |
| 供应商 ID | 6222 |
| 到期时间 | 2123-08-18 (永久) |
| ICCID | 89860000192037719209 |
| IMSI | 460002581993344 |
| PLMN | 46000 (中国移动 GSM) |
| 测试账号 | 865016309205086 / 123456 |

## 2. API 基础信息

- **API 基地址**: `http://www.fangdao8.com:8082/openapiv3.asmx`
- **请求方式**: HTTP POST
- **Content-Type**: `application/x-www-form-urlencoded; charset=UTF-8`
- **Accept**: `text/html,application/xhtml+xml,application/xml`
- **默认 API Key**: `7DU2DJFDR8321` (用于登录，登录后使用 key2018)
- **Web 平台地址**: `http://www.fangdao8.com:8089/webapp/`
- **Web Key**: `3657DU2DJFDR8321`
- **连接超时**: 5 秒
- **请求超时**: 15 秒

### 2.1 认证流程

1. 用默认 Key `7DU2DJFDR8321` 调用 `LoginByIphone3` 获取 `key2018`
2. 后续所有请求使用 `key2018` 作为 Key 参数
3. key2018 需 URL encode 后传递 (含 +、=、/ 等特殊字符)
4. key2018 会过期，需定期重新登录刷新

### 2.2 响应格式

所有 API 返回 XML 包装的 JSON:
```xml
<?xml version="1.0" encoding="utf-8"?>
<string xmlns="http://tempuri.org/">JSON内容</string>
```
解析方法: 用正则 `<string[^>]*>(.+?)</string>` 提取 JSON，再 `json.loads`。

## 3. API 接口详细说明

### 3.1 LoginByIphone3 - 用户登录

**Endpoint**: `POST /LoginByIphone3`

**请求参数**:
| 参数 | 类型 | 说明 | 示例 |
|---|---|---|---|
| Name | string | 账号 (IMEI号或用户名) | 865016309205086 |
| Pass | string | 密码 | 123456 |
| AppID | string | 应用ID (留空) | "" |
| GMT | string | 时区偏移 | 8:00 |
| Key | string | 默认API Key | 7DU2DJFDR8321 |

**响应 JSON**:
```json
{
  "state": "0",           // "0"=成功, 其他=失败
  "loginType": "1",       // "0"=用户登录, "1"=设备直登
  "deviceInfo": {         // loginType=1 时存在
    "deviceID": "714574708",
    "deviceName": "B6-05086",
    "model": "513",
    "sendCommand": "0-0-0-0-0-0-0-0-0-0",
    "timeZone": "8:00",
    "warnStr": "1-1-1-1-1-1-1-1-1-1-1-1-1",
    "key2018": "rHpQtP785KFfHGVB+euoETS/...",
    "supplierID": "6222"
  }
  // loginType=0 时使用 "deviceUser" 字段
}
```

**warnStr 格式**: `A-B-C-D-E-F-G-H-I-J-K-L-M` (13位，每位0或1)
- 位0: AlarmAlert (告警开关)
- 位1: AlertSound (告警声音)
- 位2: AlertVibration (告警震动)
- 位10: alarmset 位0 取反
- 位4: alarmset 位1 取反
- 位11: alarmset 位2 取反
- 位12: alarmset 位3 取反

### 3.2 GetTracking - 获取实时定位

**Endpoint**: `POST /GetTracking`

**请求参数**:
| 参数 | 类型 | 说明 | 示例 |
|---|---|---|---|
| DeviceID | int | 设备ID | 714574708 |
| Model | int | 设备型号 (0=自动) | 0 |
| TimeZones | string | 时区 | 8:00 |
| MapType | string | 地图类型 | BaiDu |
| Language | string | 语言 | zh_CN |
| Key | string | key2018 | (URL encoded) |

**响应 JSON**:
```json
{
  "state": "0",
  "positionTime": "2026-07-09 22:18:21",  // 定位时间
  "lat": "21.53791",      // 纬度
  "lng": "111.03396",     // 经度
  "speed": "0.00",        // 速度 (km/h)
  "course": "0",          // 方向 (度)
  "isStop": "1",          // "1"=静止, "0"=移动
  "isGPS": "2",           // 0/1=GPS卫星, 2=LBS基站
  "stm": "26",            // 停留时间(分钟)
  "isSleep": "0",         // "0"=正常, "1"=休眠
  "status": "2-电量:6%,充电中"  // 状态字符串
}
```

**status 解析规则**:
- 格式: `{status_code}-电量:{battery}%,{extra}`
- 电量: 正则 `电量:(\d+)%` 提取
- 充电: 包含 `充电中` 字符串即为充电
- status_code: `0`=正常, `2`=LBS, 其他待确认

### 3.3 GetDeviceStatus - 获取设备状态

**Endpoint**: `POST /GetDeviceStatus`

**请求参数**:
| 参数 | 类型 | 说明 | 示例 |
|---|---|---|---|
| DeviceID | int | 设备ID | 714574708 |
| TimeZones | string | 时区 | 8:00 |
| FilterWarn | string | 告警过滤 | 1000 |
| Language | string | 语言 | zh |
| Key | string | key2018 | (URL encoded) |

**响应 JSON**:
```json
{
  "state": "0",
  "id": "714574708",
  "xinhao": ".....",              // 信号强度 (点数=格数, 0-5)
  "status": "2-电量:6%,充电中",    // 同 tracking 的 status
  "sendCommand": "0-0-0-0-0-0-0-0-0-0",
  "warnTxt": "求救报警",           // 最新告警文本
  "warnTime": "2026/07/09 22:18"  // 最新告警时间
}
```

### 3.4 GetDeviceDetail - 获取设备详情

**Endpoint**: `POST /GetDeviceDetail`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| TimeZones | string | 时区 |
| Key | string | key2018 |

**响应 JSON**:
```json
{
  "state": "0",
  "id": "714574708",
  "name": "B6-05086",
  "sn": "865016309205086",
  "type": "B6",
  "model": "513",
  "speedLimit": "0.00",
  "phone": "",
  "carNum": "",
  "userName": "",
  "cellPhone": "",
  "isLBS": "0",
  "isWIFI": "0",
  "ITEM": "S281_W+G+L_XMG",
  "VER": "S281_W+G+L_XMG&2023-06-30|14-34-30&TY281V1.3&S281_V1.1.0_T6",
  "PLMN": "46000",
  "IMEI": "865016309205086",
  "IMSI": "460002581993344",
  "ICCID": "89860000192037719209",
  "OWNER": "",
  "hireExpireTime": "2123-08-18",
  "createTime": "2023-09-01"
}
```

### 3.5 SendCommandByAPP - 发送设备指令

**Endpoint**: `POST /SendCommandByAPP`

**请求参数**:
| 参数 | 类型 | 说明 | 示例 |
|---|---|---|---|
| DeviceID | int | 设备ID | 714574708 |
| CommandType | string | 指令类型 | S168JUST |
| Model | int | 设备型号 | 513 |
| Paramter | string | 参数 (注意拼写!) | "" |
| SN | string | 序列号 (留空) | "" |
| Key | string | key2018 | (URL encoded) |

**响应**: 直接返回 CommandID 字符串 (成功) 或错误码字符串
- 成功: `"12345"` (数字字符串，即 CommandID)
- `-1`: 设备不存在
- `-2`: 设备离线
- `-3`: 指令发送失败
- `-4`: 无效指令
- `-5`: 指令已发送 (部分型号等待响应)
- `-6`: 指令响应异常

### 3.5.1 指令类型 (CommandType) 完整列表

**S168 系列指令** (适用于 Model 501-513):
| 指令 | 功能 | 参数 | 适用型号 | 来源 |
|---|---|---|---|---|
| `S168JUST` | 立即定位 | "" | 501-513 | DeviceTracking |
| `S168POWERDN` | 强制关机 | "" | 505/506/507/508/513/98 | Home |
| `S168FINDME` | 寻找设备 (发声) | "" | S168系列 | Setting |
| `S168URGENT` | 紧急模式 (高频定位) | "" | 508/513 | Setting |
| `S168LISTEN` | 语音监听 | "" | 503/505/506/507/508/509/510/512/513 | VoiceComm |
| `S168BCALL` | 语音回拨 | "" | S168系列 | Setting |
| `S168REBOOT` | 在线重启 | "" | S168系列 | Setting |
| `S168PROFILE` | 场景模式切换 | 模式值 | S168系列 | Setting |

**BSJ 系列指令** (适用于 Model 23 和部分 S168 型号):
| 指令 | 功能 | 参数 | 适用型号 | 来源 |
|---|---|---|---|---|
| `BSJSF` | 设置电子围栏 | "灵敏度-通知方式" (如 "0080-0") | 23 | Setting2 |
| `BSJCF` | 清除电子围栏 | "" | 23 | Setting2 |
| `BSJDXH` | 设置短信报警号码 | 手机号 | 23 | Setting2 |
| `BSJSPEED` | 设置超速报警值 | 速度(km/h) | 23 | Setting2 |
| `BSJSPEEDOFF` | 关闭超速报警 | "" | 23 | Setting2 |
| `BSJWORKMODEL` | 设置工作模式 | "0"/"1"/"2" | 23 | Setting2 |
| `BSJSLEEP` | 超级省电模式 | "60"/"120"/"240"/"480"/"720" (分钟) | 23 | Setting2 |
| `BSJSLEEPOFF` | 关闭省电模式 | "" | 23 | Setting2 |
| `BSJSOUND` | 录音时长设置 | "15"/"30" (秒) | 23 | VoiceComm |

**WTWD 系列指令** (适用于 Model 97/98):
| 指令 | 功能 | 参数 | 适用型号 | 来源 |
|---|---|---|---|---|
| `WTWDSHUTDOWN` | 远程关机 | "" | 98/97 | Home |
| `WTWDCQ` | 远程重启 | "" | 98 | Home |
| `WTWDLY` | 温度延迟设置 | "30"/"60"/"180"/"300" (秒) | 98/97 | VoiceComm |
| `WTWDXCLY` | 温度持续录音开关 | "0"/"1" | 98/97 | VoiceComm |
| `WTWDSKLY` | 温度声控录音开关 | "0"/"1" | 98/97 | VoiceComm |

**808 系列指令** (适用于 Model 90):
| 指令 | 功能 | 参数 | 适用型号 | 来源 |
|---|---|---|---|---|
| `808DYD` | 断油电 | "" | 90 | Setting2 |
| `808HFYD` | 恢复油电 | "" | 90 | Setting2 |
| `808SF` | 设置围栏 | "灵敏度-通知方式" | 90 | Setting2 |
| `808CF` | 清除围栏 | "" | 90 | Setting2 |
| `808DXH` | 设置短信报警号码 | 手机号 | 90 | Setting2 |
| `808SPEED` | 设置超速报警 | 速度值 | 90 | Setting2 |

**其他指令**:
| 指令 | 功能 | 参数 | 适用型号 | 来源 |
|---|---|---|---|---|
| `CR` | 通用位置请求 | "" | 150/152/155/156/157/160-163 | Web |
| `TIMER` | 上报间隔设置 | 秒数 | 23 | Setting2 |
| `MC` | 设置监听号码 | 手机号 | 23 | Setting2 |
| `FLOWER` | 爱心等级 | "1"-"5" | 通用 | Love |
| `SAVE` | 智能录音模式 | "0"/"1"/"2" | 505/508/510/512/513 | VoiceComm |
| `NBLJDW` | 内部定位 | "" | 99 | (已知) |
| `WTWDLJDW` | 外部定位 | "" | 97/98 | (已知) |

**Model 513 (B6) 可用指令汇总**:
- `S168JUST` — 立即定位
- `S168POWERDN` — 强制关机
- `S168FINDME` — 寻找设备
- `S168URGENT` — 紧急模式
- `S168LISTEN` — 语音监听
- `SAVE` — 智能录音模式

**Model 513 特殊处理**:
- 追踪页隐藏"刷新"按钮，显示"立即定位"按钮
- 发送 S168JUST 后需轮询 GetResponse 获取结果
- 支持强制关机 S168POWERDN

### 3.6 GetResponse - 获取指令响应

**Endpoint**: `POST /GetResponse`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| CommandID | int | 指令ID (来自 SendCommandByAPP) |
| TimeZones | string | 时区 |
| Key | string | key2018 |

**响应 JSON**:
```json
{
  "state": "0",
  "isResponse": 1   // 1=已有响应, 0=等待中
}
```
- 如果 isResponse=0 且重试次数<3，5秒后重试
- 最多重试3次

### 3.7 GetNewWarn - 获取新告警

**Endpoint**: `POST /GetNewWarn`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| ID | int | 设备ID (用户登录=userID, 设备登录=deviceID) |
| TypeID | int | 类型 (0=用户, 1=设备) |
| LastID | int | 上次告警ID (首次传0) |
| TimeZones | string | 时区 |
| Language | string | 语言 |
| Key | string | key2018 |

**响应 JSON**:
```json
{
  "state": "0",           // "0"=有新告警, "2002"=无新数据
  "id": 12345,            // 告警ID
  "warnTxt": "求救报警",   // 告警内容
  "warnTime": "2026/07/09 22:18",
  "deviceID": 714574708
}
```

### 3.8 GetAddressByLatlng - 逆地理编码

**Endpoint**: `POST /GetAddressByLatlng`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| Lat | string | 纬度 |
| Lng | string | 经度 |
| MapType | string | 地图类型 (BaiDu/Google) |
| Language | string | 语言 (zh_CN) |

**响应**: 地址文本字符串

### 3.9 GetDeviceSetInfo - 获取设备设置

**Endpoint**: `POST /GetDeviceSetInfo`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| Key | string | key2018 |

**响应 JSON** (Model 23):
```json
{
  "state": "0",
  "BSJWORKMODEL": "0",
  "timer": "60",
  "BSJSLEEP": "",
  "BSJSF": "",
  "BSJSPEED": "0",
  "BSJDXH": "",
  "ywsleep": ""
}
```

**响应 JSON** (Model 90):
```json
{
  "state": "0",
  "center": "",
  "808SF": "",
  "BSJSPEED": "0"
}
```

### 3.10 GetVoiceList - 获取语音列表

**Endpoint**: `POST /GetVoiceList`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| PageNo | int | 页码 |
| PageCount | int | 每页数量 (30) |
| Key | string | key2018 |

**响应 JSON**:
```json
{
  "state": "0",
  "arr": [
    {
      "VoiceId": "123",
      "Path": "/voice/path",
      "CreateTime": "2026-07-09 22:00",
      "Length": "15",
      "Source": "1"
    }
  ]
}
```

### 3.11 GetVoiceNew - 获取新语音

**Endpoint**: `POST /GetVoiceNew`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| VoiceId | int | 语音ID |
| Key | string | key2018 |

### 3.12 SendVoice - 发送语音到设备

**Endpoint**: `POST /SendVoice`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| Type | string | 类型 ("0") |
| Voice | string | 语音数据 (hex编码的AMR) |
| Length | int | 时长(秒) |
| Key | string | key2018 |

### 3.13 DeletedVoiceByDeviceID - 删除设备语音

**Endpoint**: `POST /DeletedVoiceByDeviceID`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| Key | string | key2018 |

### 3.14 UpdateDevice - 更新设备信息

**Endpoint**: `POST /UpdateDevice`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| DeviceName | string | 设备名称 |
| CarNum | string | 车牌号 |
| PhoneNumbe | string | 设备电话号码 |
| CarUserName | string | 联系人姓名 |
| CellPhone | string | 联系人手机 |
| Key | string | key2018 |

**响应**: state `"2005"` = 成功, `"2003"` = 昵称已存在

### 3.15 SetWarn - 设置告警偏好

**Endpoint**: `POST /SetWarn`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| ID | int | 用户ID或设备ID |
| TypeID | int | 类型 (0=用户, 1=设备) |
| WarnStr | string | "1-1-1-1-1-1-1-1-1-1-1-1-1" (13位) |
| Key | string | key2018 |

### 3.16 GetGeofence - 获取电子围栏列表

**Endpoint**: `POST /GetGeofence`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| TimeZones | string | 时区 |
| MapType | string | 地图类型 |
| Key | string | key2018 |

**响应 JSON**:
```json
{
  "state": "0",
  "geofences": [
    {
      "geofenceID": 123,
      "fenceName": "家",
      "lng": "111.033",
      "lat": "21.537",
      "radius": "500",
      "createTime": "2026-01-01"
    }
  ]
}
```

### 3.17 DelGeofence - 删除电子围栏

**Endpoint**: `POST /DelGeofence`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| GeofenceID | int | 围栏ID |
| DeviceID | int | 设备ID |
| Key | string | key2018 |

### 3.18 GetDevicesHistory - 获取历史轨迹

**Endpoint**: `POST /GetDevicesHistory`

**请求参数**:
| 参数 | 类型 | 说明 |
|---|---|---|
| DeviceID | int | 设备ID |
| StartTime | string | "yyyy/MM/dd HH:mm:ss" |
| EndTime | string | "yyyy/MM/dd HH:mm:ss" |
| TimeZones | string | 时区 |
| ShowLBS | string | "0"或"1" (是否显示LBS点) |
| MapType | string | 地图类型 |
| SelectCount | int | 最大点数 (1000) |
| Key | string | key2018 |

**响应 JSON**:
```json
{
  "state": "0",
  "devices": [ ... ]  // 历史点位数组
}
```

## 4. 地图引擎支持

| 类型编号 | 地图 | SDK | 说明 |
|---|---|---|---|
| 1 | Google Maps | Google Maps SDK | 海外优先 |
| 2 | 百度地图 | Baidu Map SDK | 中文区默认 |
| 3 | 高德地图 | AMap SDK | 备选 |
| 12 | 天地图 | WebView | URL: webapp/track-tdt.html |

**地图类型判断逻辑** (`m.e.J()` 方法):
- type=3 → "Google"
- type=1 → "BaiDu"
- type=2/4/5 → "Google"
- 其他 → ""

**百度地图 API Key**: `IyYOGRTOvkIit2osh1UA5vByXPY4N5wu`
**Google Maps API Key**: `AIzaSyCwb9IqNEHfaLqh_ex5QY4HQ_IYxrQFF4w`
**高德地图 API Key**: `9582d1736f0764d428e71660183c7031`

## 5. 数据存储 (SharedPreferences "config")

| Key | 类型 | 说明 |
|---|---|---|
| loginRemember | bool | 记住密码 |
| userName | string | 用户名 |
| userPass | string | 密码 (明文!) |
| loginType | int | 0=用户, 1=设备 |
| mapType | int | 1=Google, 2=百度, 3=高德, 12=天图 |
| selectedDevice | int | 当前设备ID |
| selectedDeviceName | string | 当前设备名 |
| SelectedDeviceModel | int | 当前设备型号 |
| timeZone | string | 时区 |
| userId | int | 用户ID |
| key2018 | string | 认证密钥 |
| deviceListArray | string | 设备列表 JSON |
| AlarmAlert | bool | 告警开关 |
| AlertSound | bool | 告警声音 |
| AlertVibration | bool | 告警震动 |
| alarmset | string | 告警设置 (4位二进制字符串) |
| Privacy | bool | 隐私协议同意 |
| FMapView.MapType | int | 地图显示类型 |
| FMapView.TileType | int | 地图瓦片类型 |

## 6. HA 集成文件结构

```
custom_components/fineme/
├── __init__.py          # 集成入口，创建 coordinator，转发平台
├── manifest.json        # 域: fineme, iot_class: cloud_polling
├── config_flow.py       # 输入账号密码 → login → 保存配置
├── const.py             # 域名、API URL、指令常量
├── coord_convert.py     # BD09↔GCJ02↔WGS84 坐标转换
├── coordinator.py       # DataUpdateCoordinator，30秒轮询
│                        # 并行调 GetTracking + GetDeviceStatus
│                        # 首次额外调 GetDeviceDetail
├── api.py               # 异步 HTTP 客户端 (aiohttp)
│                        # XML→JSON 解析
│                        # parse_battery/parse_charging/parse_signal 静态方法
├── device_tracker.py    # device_tracker: lat/lng/accuracy/speed/course
├── sensor.py            # battery/signal/speed/alarm/firmware/iccid/imei
├── binary_sensor.py     # charging/online/sleeping/sos_alarm
├── button.py            # locate_now(S168JUST) / find_device(S168FINDME) / emergency(S168URGENT)
│                        # voice_listen(S168LISTEN) / voice_call(S168BCALL) / reboot(S168REBOOT)
│                        # power_off(S168POWERDN)
├── strings.json         # UI 字符串 (默认)
└── translations/
    ├── zh-Hans.json     # 中文
    └── en.json          # 英文
```

## 7. 已知问题/注意事项

1. **HTTP 明文通信** - API 使用 http:// 而非 https://
2. **密码明文存储** - SharedPreferences 中密码无加密
3. **API Key 过期** - key2018 有有效期，需定期重新登录刷新
4. **Paramter 拼写** - SendCommandByAPP 的参数名拼写为 `Paramter`（非 Parameter）
5. **XML 响应中 HTML 实体** - 如 `&amp;` 需要解码 (json.loads 前 XML 解析器会处理)
6. **isGPS 含义**: 0=GPS有效, 1=GPS有效(带差分), 2=LBS基站(精度低约500m)
7. **坐标系统**: API 返回百度坐标系 (BD09)，集成已自动转换为 WGS84 用于 HA 地图显示，原始 BD09 坐标保存在 entity attributes 中
8. **告警类型**: 常见有 "求救报警"、"越界报警"、"低电量报警" 等
9. **设备休眠**: isSleep=1 时设备不响应指令，返回 -2 (离线)
10. **S168JUST 指令**: Model 513 发送后，需通过 GetResponse 轮询等待设备上报新位置
