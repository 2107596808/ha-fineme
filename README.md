# Fineme GPS Tracker for Home Assistant

Home Assistant 自定义集成，适配 Fineme (方案) GPS 定位追踪器，目前仅测试适配 **B6 型号 (Model 513)** 设备。

## 功能

- **GPS 位置追踪** (`device_tracker`) - 实时经纬度、精度、速度、方向
- **电池电量** (`sensor`) - 百分比电量显示
- **信号强度** (`sensor`) - 0-5 格信号
- **速度** (`sensor`) - 实时速度 km/h
- **最新告警** (`sensor`) - 告警文本及时间
- **固件版本 / ICCID / IMEI** (`sensor`) - 设备信息
- **充电状态** (`binary_sensor`) - 是否充电中
- **设备在线** (`binary_sensor`) - 在线/离线状态
- **休眠状态** (`binary_sensor`) - 设备是否休眠
- **SOS 报警** (`binary_sensor`) - SOS 求救检测
- **立即定位** (`button`) - 远程触发设备定位 (S168JUST)
- **强制关机** (`button`) - 远程强制关机 (S168POWERDN)

## 安装

### 手动安装

1. 将 `custom_components/fineme/` 目录复制到你的 Home Assistant `config` 目录下：
   ```
   config/
   └── custom_components/
       └── fineme/
           ├── __init__.py
           ├── api.py
           ├── binary_sensor.py
           ├── button.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── device_tracker.py
           ├── manifest.json
           ├── sensor.py
           ├── strings.json
           └── translations/
               ├── en.json
               └── zh-Hans.json
   ```

2. 重启 Home Assistant
3. 进入 **设置 → 设备与服务 → 添加集成**
4. 搜索 **Fineme** 并添加
5. 输入你的设备账号 (IMEI号) 和密码

### HACS 安装 (暂未支持)

暂不支持 HACS，请手动安装。

## 配置选项

安装后可在集成选项中调整：

| 选项 | 默认值 | 说明 |
|---|---|---|
| 刷新间隔 | 30 秒 | 数据轮询间隔 (建议不低于 15 秒) |

## 技术说明

### API

- **协议**: HTTP POST (明文，非 HTTPS)
- **认证**: 先通过默认 Key 登录获取 session key (key2018)，后续请求使用 session key
- **响应格式**: XML 包裹的 JSON (`<string>` 标签)
- **坐标系统**: API 返回百度坐标系 (BD09)，集成自动转换为 WGS84 用于 HA 地图显示，原始 BD09 坐标保存在 `bd09_latitude` / `bd09_longitude` 属性中
- **轮询间隔**: 默认 30 秒

### 设备型号兼容性

本集成目前仅测试适配 **Model 513 (B6/S168系列)** 设备。

其他型号 (97/98/99 等) 的指令类型不同，可能需要额外适配。详见 `API_REFERENCE.md`。

### 定位精度

| 来源 | 精度 | 说明 |
|---|---|---|
| GPS 卫星 (isGPS=0/1) | ~10m | 室外高精度 |
| LBS 基站 (isGPS=2) | ~500m | 室内/信号差时降级 |

## 文件结构

```
custom_components/fineme/
├── __init__.py          # 集成入口
├── api.py               # 异步 API 客户端 (aiohttp)
├── binary_sensor.py     # 二进制传感器 (充电/在线/休眠/SOS)
├── button.py            # 远程指令按钮 (定位/关机)
├── config_flow.py       # Config Flow 配置界面
├── const.py             # 常量定义
├── coord_convert.py     # BD09↔GCJ02↔WGS84 坐标转换
├── coordinator.py       # DataUpdateCoordinator
├── device_tracker.py    # GPS 位置追踪 (WGS84)
├── manifest.json        # 集成元数据
├── sensor.py            # 传感器 (电量/信号/速度/告警/固件)
├── strings.json         # UI 字符串
└── translations/
    ├── en.json
    └── zh-Hans.json
```

## 注意事项

1. API 使用 **HTTP 明文**通信，存在安全风险
2. key2018 会过期，集成会自动刷新
3. 设备休眠时可能不响应远程指令
4. 坐标已自动从 BD09 转换为 WGS84，可直接在 HA 默认地图上正确显示；原始 BD09 坐标在 entity attributes 中，可用于百度地图显示
5. 刷新间隔建议不低于 15 秒，避免过于频繁请求

## 致谢

- 通过 jadx 反编译 APK (`com.fw.skdz` v6.37) 逆向分析 API
- 参考原始易语言客户端实现

## License

MIT
