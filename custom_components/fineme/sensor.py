"""Sensor platform for Fineme GPS Tracker."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FinemeAPI
from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, CONF_MODEL, DOMAIN
from .coordinator import FinemeCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FinemeSensorEntityDescription(SensorEntityDescription):
    """Describes a Fineme sensor entity."""

    value_fn: Callable[[dict], str | int | float | None]
    available_fn: Callable[[dict], bool] = lambda _: True


def _get_battery(data: dict) -> int | None:
    """Get battery percentage."""
    if not data:
        return None
    # Try status first, then tracking
    status_data = data.get("status", {})
    tracking_data = data.get("tracking", {})
    status_str = status_data.get("status", "") or tracking_data.get("status", "")
    if status_str:
        return FinemeAPI.parse_battery(status_str)
    return None


def _get_signal(data: dict) -> int | None:
    """Get signal strength."""
    if not data or not data.get("status"):
        return None
    xinhao = data["status"].get("xinhao", "")
    return FinemeAPI.parse_signal(xinhao) if xinhao else None


def _get_speed(data: dict) -> float | None:
    """Get speed."""
    if not data or not data.get("tracking"):
        return None
    try:
        return float(data["tracking"].get("speed", 0))
    except (ValueError, TypeError):
        return 0


def _get_alarm_text(data: dict) -> str | None:
    """Get latest alarm text."""
    if not data or not data.get("status"):
        return None
    warn_txt = data["status"].get("warnTxt", "")
    warn_time = data["status"].get("warnTime", "")
    if warn_txt:
        return f"{warn_txt} ({warn_time})" if warn_time else warn_txt
    return None


def _get_firmware(data: dict) -> str | None:
    """Get firmware version."""
    if not data or not data.get("detail"):
        return None
    return data["detail"].get("VER", "")


def _get_iccid(data: dict) -> str | None:
    """Get SIM card ICCID."""
    if not data or not data.get("detail"):
        return None
    return data["detail"].get("ICCID", "")


def _get_imei(data: dict) -> str | None:
    """Get device IMEI."""
    if not data or not data.get("detail"):
        return None
    return data["detail"].get("IMEI", "")


def _has_tracking(data: dict) -> bool:
    """Check if tracking data is available."""
    return bool(data and data.get("tracking"))


def _has_detail(data: dict) -> bool:
    """Check if detail data is available."""
    return bool(data and data.get("detail"))


SENSOR_DESCRIPTIONS: tuple[FinemeSensorEntityDescription, ...] = (
    FinemeSensorEntityDescription(
        key="battery",
        translation_key="battery",
        name="电量",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_battery,
        available_fn=_has_tracking,
    ),
    FinemeSensorEntityDescription(
        key="signal",
        translation_key="signal",
        name="信号强度",
        icon="mdi:signal",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_signal,
    ),
    FinemeSensorEntityDescription(
        key="speed",
        translation_key="speed",
        name="速度",
        device_class=SensorDeviceClass.SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_speed,
        available_fn=_has_tracking,
    ),
    FinemeSensorEntityDescription(
        key="alarm",
        translation_key="alarm",
        name="最新告警",
        icon="mdi:alert-circle",
        value_fn=_get_alarm_text,
    ),
    FinemeSensorEntityDescription(
        key="firmware",
        translation_key="firmware",
        name="固件版本",
        icon="mdi:chip",
        entity_registry_enabled_default=False,
        value_fn=_get_firmware,
        available_fn=_has_detail,
    ),
    FinemeSensorEntityDescription(
        key="iccid",
        translation_key="iccid",
        name="ICCID",
        icon="mdi:sim",
        entity_registry_enabled_default=False,
        value_fn=_get_iccid,
        available_fn=_has_detail,
    ),
    FinemeSensorEntityDescription(
        key="imei",
        translation_key="imei",
        name="IMEI",
        icon="mdi:identifier",
        entity_registry_enabled_default=False,
        value_fn=_get_imei,
        available_fn=_has_detail,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fineme sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            FinemeSensor(coordinator, config_entry, description)
            for description in SENSOR_DESCRIPTIONS
        ]
    )


class FinemeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Fineme sensor."""

    _attr_has_entity_name = True
    entity_description: FinemeSensorEntityDescription

    def __init__(
        self,
        coordinator: FinemeCoordinator,
        config_entry: ConfigEntry,
        description: FinemeSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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

    @property
    def native_value(self) -> str | int | float | None:
        """Return the sensor value."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False
        if not self.coordinator.data:
            return False
        return self.entity_description.available_fn(self.coordinator.data)
