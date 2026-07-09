"""API client for Fineme GPS Tracker."""

import asyncio
import json
import logging
import re
from datetime import datetime
from urllib.parse import quote

import aiohttp

from .const import API_BASE_URL, API_DEFAULT_KEY

_LOGGER = logging.getLogger(__name__)


class FinemeAPIError(Exception):
    """Base exception for Fineme API errors."""


class FinemeAPI:
    """Async API client for Fineme GPS Tracker service."""

    def __init__(self, session: aiohttp.ClientSession | None = None):
        """Initialize the API client."""
        self._session = session
        self._own_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    async def close(self):
        """Close the session if we own it."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, endpoint: str, data: dict) -> dict:
        """Make a POST request to the API and return parsed JSON."""
        session = await self._get_session()
        url = f"{API_BASE_URL}/{endpoint}"

        # Build form-encoded body
        body = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in data.items())

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "text/html,application/xhtml+xml,application/xml",
        }

        try:
            async with session.post(url, data=body, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    raise FinemeAPIError(f"HTTP {resp.status}")
                text = await resp.text()
        except asyncio.TimeoutError as err:
            raise FinemeAPIError("Request timeout") from err
        except aiohttp.ClientError as err:
            raise FinemeAPIError(f"Request failed: {err}") from err

        return self._parse_xml_response(text)

    def _parse_xml_response(self, text: str) -> dict:
        """Parse XML response and extract JSON content."""
        # Response format: <?xml ...><string xmlns="http://tempuri.org/">JSON</string>
        match = re.search(r"<string[^>]*>(.+?)</string>", text, re.DOTALL)
        if not match:
            _LOGGER.error("Failed to parse XML response: %s", text[:200])
            raise FinemeAPIError("Invalid XML response format")

        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to parse JSON: %s", json_str[:200])
            raise FinemeAPIError(f"Invalid JSON: {err}") from err

    async def login(self, username: str, password: str) -> dict:
        """Login and get device info + key2018.

        Returns:
            dict with keys: state, loginType, deviceInfo/deviceUser
            deviceInfo contains: deviceID, deviceName, model, key2018, timeZone, warnStr, sendCommand
        """
        # Calculate GMT offset
        now = datetime.now()
        utc_offset = now.astimezone().utcoffset()
        if utc_offset:
            total_minutes = int(utc_offset.total_seconds() / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            gmt = f"{hours}:{minutes:02d}"
        else:
            gmt = "0:00"

        data = {
            "Name": username,
            "Pass": password,
            "AppID": "",
            "GMT": gmt,
            "Key": API_DEFAULT_KEY,
        }

        result = await self._request("LoginByIphone3", data)

        state = result.get("state")
        if state != "0" and state != 0:
            error_msg = f"Login failed with state={state}"
            _LOGGER.error(error_msg)
            raise FinemeAPIError(error_msg)

        return result

    async def get_tracking(self, device_id: int, key: str, time_zone: str = "8:00") -> dict:
        """Get real-time tracking data.

        Returns:
            dict with keys: state, positionTime, lat, lng, speed, course, isStop, isGPS, stm, isSleep, status
            status format: "2-电量:6%,充电中"
        """
        data = {
            "DeviceID": device_id,
            "Model": 0,
            "TimeZones": time_zone,
            "MapType": "BaiDu",
            "Language": "zh_CN",
            "Key": key,
        }

        return await self._request("GetTracking", data)

    async def get_device_status(self, device_id: int, key: str, time_zone: str = "8:00") -> dict:
        """Get device status.

        Returns:
            dict with keys: state, id, xinhao, status, sendCommand, warnTxt, warnTime
        """
        data = {
            "DeviceID": device_id,
            "TimeZones": time_zone,
            "FilterWarn": "1000",
            "Language": "zh",
            "Key": key,
        }

        return await self._request("GetDeviceStatus", data)

    async def get_device_detail(self, device_id: int, key: str, time_zone: str = "8:00") -> dict:
        """Get device detail info.

        Returns:
            dict with keys: state, id, name, sn, type, model, VER, IMEI, ICCID, IMSI, PLMN, hireExpireTime, etc.
        """
        data = {
            "DeviceID": device_id,
            "TimeZones": time_zone,
            "Key": key,
        }

        return await self._request("GetDeviceDetail", data)

    async def send_command(
        self, device_id: int, command_type: str, model: int, key: str, parameter: str = ""
    ) -> str:
        """Send a command to the device.

        Returns:
            Command ID string on success, or error code string (-1 to -6)
            -1: device not exist
            -2: device offline
            -3: command send failed
            -4: command invalid
            -5: command sent (for some models)
            -6: command response 6
        """
        data = {
            "DeviceID": device_id,
            "CommandType": command_type,
            "Model": model,
            "Paramter": parameter,
            "SN": "",
            "Key": key,
        }

        result = await self._request("SendCommandByAPP", data)
        # The result is the command ID or error code directly as the JSON content
        # But wrapped in state check
        return result

    async def get_response(self, command_id: int, key: str, time_zone: str = "8:00") -> dict:
        """Get response for a previously sent command.

        Returns:
            dict with keys: state, isResponse, etc.
        """
        data = {
            "CommandID": command_id,
            "TimeZones": time_zone,
            "Key": key,
        }

        return await self._request("GetResponse", data)

    async def get_new_warn(self, device_id: int, last_id: int, key: str, time_zone: str = "8:00") -> dict:
        """Get new warnings/alerts.

        Returns:
            dict with keys: state, id, warnTxt, warnTime, deviceID
        """
        data = {
            "ID": device_id,
            "TypeID": 1,
            "LastID": last_id,
            "TimeZones": time_zone,
            "Language": "zh",
            "Key": key,
        }

        return await self._request("GetNewWarn", data)

    @staticmethod
    def parse_battery(status: str) -> int | None:
        """Parse battery percentage from status string.

        Example: "2-电量:6%,充电中" -> 6
        """
        match = re.search(r"电量:(\d+)%", status)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def parse_charging(status: str) -> bool:
        """Parse charging state from status string.

        Example: "2-电量:6%,充电中" -> True
        """
        return "充电中" in status

    @staticmethod
    def parse_signal(xinhao: str) -> int:
        """Parse signal strength from xinhao string.

        Example: "....." -> 5, "..." -> 3
        """
        return xinhao.count(".") if xinhao else 0
