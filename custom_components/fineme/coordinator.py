"""Data update coordinator for Fineme GPS Tracker."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FinemeAPI, FinemeAPIError
from .const import (
    CMD_LOCATE_NOW,
    CONF_DEVICE_ID,
    CONF_KEY2018,
    CONF_TIME_ZONE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class FinemeCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching data from Fineme API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: FinemeAPI,
        config_data: dict,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.device_id = config_data[CONF_DEVICE_ID]
        self.key = config_data[CONF_KEY2018]
        self.time_zone = config_data[CONF_TIME_ZONE]
        self.device_name = config_data.get("device_name", "Fineme Device")
        self.model = config_data.get("model", 513)
        self._detail_data = None
        self._detail_fetched = False

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoints."""
        try:
            # Wake device by sending locate command before fetching data.
            # The device only reports fresh data when it receives a command;
            # otherwise the server returns stale cached data.
            try:
                await self.api.send_command(
                    device_id=self.device_id,
                    command_type=CMD_LOCATE_NOW,
                    model=self.model,
                    key=self.key,
                )
            except FinemeAPIError as err:
                # If wake command fails (e.g. device offline), continue with cached data
                _LOGGER.debug("Wake command failed, using cached data: %s", err)

            # Brief delay for device to process the wake command and report
            await asyncio.sleep(2)

            # Fetch tracking and status in parallel
            tracking_task = self.api.get_tracking(
                self.device_id, self.key, self.time_zone
            )
            status_task = self.api.get_device_status(
                self.device_id, self.key, self.time_zone
            )

            tracking, status = await asyncio.gather(
                tracking_task, status_task
            )

            # Fetch device detail only once
            if not self._detail_fetched:
                try:
                    self._detail_data = await self.api.get_device_detail(
                        self.device_id, self.key, self.time_zone
                    )
                    self._detail_fetched = True
                except FinemeAPIError as err:
                    _LOGGER.warning("Failed to fetch device detail: %s", err)

            return {
                "tracking": tracking,
                "status": status,
                "detail": self._detail_data,
            }

        except FinemeAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_refresh_key(self, username: str, password: str) -> bool:
        """Refresh the API key by re-login."""
        try:
            result = await self.api.login(username, password)
            state = result.get("state")
            if str(state) == "0":
                # Extract new key based on login type
                login_type = result.get("loginType")
                if str(login_type) == "1":
                    info = result.get("deviceInfo", {})
                else:
                    info = result.get("deviceUser", {})
                new_key = info.get("key2018", "")
                if new_key:
                    self.key = new_key
                    _LOGGER.debug("API key refreshed successfully")
                    return True
            return False
        except FinemeAPIError as err:
            _LOGGER.error("Failed to refresh API key: %s", err)
            return False
