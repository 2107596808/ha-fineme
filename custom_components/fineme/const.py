"""Constants for the Fineme GPS Tracker integration."""

DOMAIN = "fineme"

# API Configuration
API_BASE_URL = "http://www.fangdao8.com:8082/openapiv3.asmx"
API_DEFAULT_KEY = "7DU2DJFDR8321"

# Configuration keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"
CONF_MODEL = "model"
CONF_KEY2018 = "key2018"
CONF_TIME_ZONE = "time_zone"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIME_ZONE = "8:00"

# Command types for Model 513 (S168 series)
CMD_LOCATE_NOW = "S168JUST"
CMD_POWER_OFF = "S168POWERDN"
CMD_FIND_DEVICE = "S168FINDME"
CMD_EMERGENCY = "S168URGENT"

# Supported device models
SUPPORTED_MODELS = [513]

# Platforms
PLATFORMS = ["device_tracker", "sensor", "binary_sensor", "button"]
