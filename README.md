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

### HACS 安装（推荐）

1. 打开 HACS → 集成
2. 点击右上角 **⋮** → **自定义存储库**
3. 添加仓库地址：`https://github.com/2107596808/ha-fineme`，类别选择 **集成**
4. 搜索 **Fineme GPS Tracker** 并下载安装
5. 重启 Home Assistant
6. 进入 **设置 → 设备与服务 → 添加集成**
7. 搜索 **Fineme** 并添加
8. 输入你的设备账号 (IMEI号) 和密码

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

### HACS 更新

HACS 会自动检测更新，也可在集成页面手动点击更新。

## 配置选项

安装后可在集成选项中调整：

| 选项 | 默认值 | 说明 |
|---|---|---|
| 刷新间隔 | 30 秒 | 数据轮询间隔 (建议不低于 15 秒) |

## 高德地图卡片

集成自带高德地图自定义 Lovelace 卡片 (`fineme-amap-card`)，安装集成后会自动注册资源。

### 使用方式

1. 进入 HA 仪表盘 → **编辑仪表盘** → **添加卡片** → **手动卡片**
2. 粘贴以下 YAML 配置：

```yaml
type: custom:fineme-amap-card
entity: device_tracker.fineme_b6_05086  # 替换为你的 entity_id
zoom: 16
height: 400
map_style: 'amap://styles/normal'        # 可选: light/dark/fresh/grey/blue
amap_key: 'YOUR_AMAP_KEY'                # 填写你的高德 JS API Key
```

### 卡片配置参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `entity` | (必填) | device_tracker 实体 ID |
| `zoom` | 16 | 初始缩放级别 (3-18) |
| `height` | 400 | 卡片高度 (像素) |
| `amap_key` | (必填) | 高德地图 JS API Key，可在 [高德开放平台](https://lbs.amap.com/) 免费申请 |
| `map_style` | `amap://styles/normal` | 地图样式 (normal/light/dark/fresh/grey/blue) |
| `use_bd09` | `false` | 是否使用原始百度坐标 (true=BD09, false=WGS84自动转GCJ02) |
| `battery_entity` | (可选) | 电量传感器实体 ID，显示在信息窗口 |

### 地图样式示例

| style 值 | 效果 |
|---|---|
| `amap://styles/normal` | 标准地图 |
| `amap://styles/light` | 月光银 |
| `amap://styles/dark` | 雅士灰 |
| `amap://styles/fresh` | 草色青 |
| `amap://styles/grey` | 远山蓝 |
| `amap://styles/blue` | 远峰蓝 |

> **注意**: 如自动注册资源失败，请手动添加 Lovelace 资源：
> 设置 → 仪表盘 → 资源 → 添加资源 → URL: `/fineme/fineme-amap-card.js`，类型: JavaScript 模块

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
├── www/
│   └── fineme-amap-card.js  # 高德地图 Lovelace 卡片
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
