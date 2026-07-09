"""Button platform for Fineme GPS Tracker."""

import logging
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FinemeAPIError
from .const import (
    CMD_LOCATE_NOW,
    CMD_POWER_OFF,
    CMD_FIND_DEVICE,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_MODEL,
    DOMAIN,
)
from .coordinator import FinemeCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FinemeButtonEntityDescription(ButtonEntityDescription):
    """Describes a Fineme button entity."""

    command_type: str
    confirm_required: bool = False


BUTTON_DESCRIPTIONS: tuple[FinemeButtonEntityDescription, ...] = (
    FinemeButtonEntityDescription(
        key="locate_now",
        translation_key="locate_now",
        name="立即定位",
        icon="mdi:crosshairs-gps",
        command_type=CMD_LOCATE_NOW,
        confirm_required=False,
    ),
    FinemeButtonEntityDescription(
        key="find_device",
        translation_key="find_device",
        name="寻找设备",
        icon="mdi:bell-ring",
        command_type=CMD_FIND_DEVICE,
        confirm_required=False,
    ),
    FinemeButtonEntityDescription(
        key="power_off",
        translation_key="power_off",
        name="强制关机",
        icon="mdi:power",
        command_type=CMD_POWER_OFF,
        confirm_required=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fineme button platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            FinemeButton(coordinator, config_entry, description)
            for description in BUTTON_DESCRIPTIONS
        ]
    )


class FinemeButton(CoordinatorEntity, ButtonEntity):
    """Representation of a Fineme command button."""

    _attr_has_entity_name = True
    entity_description: FinemeButtonEntityDescription

    def __init__(
        self,
        coordinator: FinemeCoordinator,
        config_entry: ConfigEntry,
        description: FinemeButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._device_name = config_entry.data[CONF_DEVICE_NAME]
        self._model = config_entry.data[CONF_MODEL]

        self._attr_unique_id = f"fineme_{self._device_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self._device_id))},
            name=self._device_name,
            manufacturer="Fineme",
            model=f"B6 (Model {self._model})",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        command_type = self.entity_description.command_type

        _LOGGER.info(
            "Sending command %s to device %s (model %s)",
            command_type,
            self._device_id,
            self._model,
        )

        try:
            result = await self.coordinator.api.send_command(
                device_id=self._device_id,
                command_type=command_type,
                model=self._model,
                key=self.coordinator.key,
            )

            # Check result
            result_str = str(result) if result else ""
            if result_str.startswith("-"):
                # Error codes
                error_messages = {
                    "-1": "设备不存在",
                    "-2": "设备离线",
                    "-3": "指令发送失败",
                    "-4": "无效指令",
                    "-5": "指令已发送（等待响应）",
                    "-6": "指令响应异常",
                }
                error_msg = error_messages.get(result_str, f"未知错误: {result_str}")
                _LOGGER.warning("Command %s failed: %s", command_type, error_msg)
            else:
                _LOGGER.info("Command %s sent successfully, ID: %s", command_type, result_str)

                # Trigger a refresh to get updated data
                await self.coordinator.async_request_refresh()

        except FinemeAPIError as err:
            _LOGGER.error("Failed to send command %s: %s", command_type, err)
