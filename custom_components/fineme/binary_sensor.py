"""Binary sensor platform for Fineme GPS Tracker."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FinemeAPI
from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, CONF_MODEL, DOMAIN
from .coordinator import FinemeCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FinemeBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Fineme binary sensor entity."""

    is_on_fn: Callable[[dict], bool | None]


def _is_charging(data: dict) -> bool | None:
    """Check if device is charging."""
    if not data:
        return None
    status_data = data.get("status", {})
    tracking_data = data.get("tracking", {})
    status_str = status_data.get("status", "") or tracking_data.get("status", "")
    if status_str:
        return FinemeAPI.parse_charging(status_str)
    return None


def _is_online(data: dict) -> bool | None:
    """Check if device is online."""
    if not data or not data.get("tracking"):
        return None
    tracking = data["tracking"]
    state = tracking.get("state")
    is_sleep = tracking.get("isSleep", 0)
    # Online if state is 0 and not sleeping
    return str(state) == "0" and str(is_sleep) != "1"


def _is_sleeping(data: dict) -> bool | None:
    """Check if device is sleeping."""
    if not data or not data.get("tracking"):
        return None
    tracking = data["tracking"]
    is_sleep = tracking.get("isSleep", 0)
    return str(is_sleep) == "1"


def _is_sos_alarm(data: dict) -> bool | None:
    """Check if SOS alarm is active."""
    if not data or not data.get("status"):
        return None
    warn_txt = data["status"].get("warnTxt", "")
    # SOS alarm contains "求救"
    return "求救" in warn_txt if warn_txt else False


BINARY_SENSOR_DESCRIPTIONS: tuple[FinemeBinarySensorEntityDescription, ...] = (
    FinemeBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        name="充电状态",
        device_class=BinarySensorDeviceClass.PLUG,
        is_on_fn=_is_charging,
    ),
    FinemeBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        name="设备在线",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=_is_online,
    ),
    FinemeBinarySensorEntityDescription(
        key="sleeping",
        translation_key="sleeping",
        name="休眠状态",
        icon="mdi:power-sleep",
        is_on_fn=_is_sleeping,
    ),
    FinemeBinarySensorEntityDescription(
        key="sos_alarm",
        translation_key="sos_alarm",
        name="SOS报警",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=_is_sos_alarm,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fineme binary sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            FinemeBinarySensor(coordinator, config_entry, description)
            for description in BINARY_SENSOR_DESCRIPTIONS
        ]
    )


class FinemeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Fineme binary sensor."""

    _attr_has_entity_name = True
    entity_description: FinemeBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: FinemeCoordinator,
        config_entry: ConfigEntry,
        description: FinemeBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
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
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data)
