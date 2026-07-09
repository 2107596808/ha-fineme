"""Device tracker platform for Fineme GPS Tracker."""

import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, CONF_MODEL, DOMAIN
from .coord_convert import bd09_to_wgs84
from .coordinator import FinemeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fineme tracker platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([FinemeTracker(coordinator, config_entry)])


class FinemeTracker(CoordinatorEntity, TrackerEntity):
    """Representation of a Fineme GPS Tracker device."""

    _attr_has_entity_name = True
    _attr_name = None  # Use device name
    _attr_translation_key = "tracker"

    def __init__(
        self,
        coordinator: FinemeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the tracker."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._device_name = config_entry.data[CONF_DEVICE_NAME]
        self._model = config_entry.data[CONF_MODEL]

        self._attr_unique_id = f"fineme_{self._device_id}_tracker"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self._device_id))},
            name=self._device_name,
            manufacturer="Fineme",
            model=f"B6 (Model {self._model})",
        )

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    def _get_raw_coords(self) -> tuple[float, float] | None:
        """Return raw (BD09) latitude and longitude, or None."""
        if self.coordinator.data and self.coordinator.data.get("tracking"):
            tracking = self.coordinator.data["tracking"]
            try:
                lat = float(tracking.get("lat", 0))
                lng = float(tracking.get("lng", 0))
                if lat != 0 and lng != 0:
                    return lat, lng
            except (ValueError, TypeError):
                pass
        return None

    @property
    def latitude(self) -> float | None:
        """Return latitude (WGS84, converted from BD09)."""
        coords = self._get_raw_coords()
        if coords:
            _, wgs_lat = bd09_to_wgs84(coords[1], coords[0])
            return wgs_lat
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude (WGS84, converted from BD09)."""
        coords = self._get_raw_coords()
        if coords:
            wgs_lng, _ = bd09_to_wgs84(coords[1], coords[0])
            return wgs_lng
        return None

    @property
    def location_accuracy(self) -> int:
        """Return location accuracy in meters.

        GPS satellite (isGPS=0/1) = high accuracy (~10m)
        LBS base station (isGPS=2) = low accuracy (~500m)
        """
        if self.coordinator.data and self.coordinator.data.get("tracking"):
            tracking = self.coordinator.data["tracking"]
            is_gps = tracking.get("isGPS", 2)
            if is_gps in (0, 1):
                return 10  # GPS satellite - high accuracy
            elif is_gps == 2:
                return 500  # LBS base station - low accuracy
        return 1000  # Unknown

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data and self.coordinator.data.get("tracking"):
            tracking = self.coordinator.data["tracking"]

            # Original BD09 coordinates (for Baidu map use)
            try:
                bd_lat = float(tracking.get("lat", 0))
                bd_lng = float(tracking.get("lng", 0))
                if bd_lat != 0 and bd_lng != 0:
                    attrs["bd09_latitude"] = bd_lat
                    attrs["bd09_longitude"] = bd_lng
            except (ValueError, TypeError):
                pass

            # Coordinate system info
            attrs["coordinate_system"] = "WGS84 (BD09 original in attributes)"

            # Speed
            try:
                attrs["speed"] = float(tracking.get("speed", 0))
            except (ValueError, TypeError):
                attrs["speed"] = 0

            # Course/direction
            attrs["course"] = tracking.get("course", "0")

            # Position time
            attrs["position_time"] = tracking.get("positionTime", "")

            # GPS type
            is_gps = tracking.get("isGPS", 2)
            if is_gps in (0, 1):
                attrs["location_source"] = "GPS卫星"
            elif is_gps == 2:
                attrs["location_source"] = "LBS基站"
            else:
                attrs["location_source"] = f"未知({is_gps})"

            # Stop status
            is_stop = tracking.get("isStop", "0")
            attrs["is_stopped"] = str(is_stop) == "1"

            # Sleep status
            is_sleep = tracking.get("isSleep", 0)
            attrs["is_sleeping"] = str(is_sleep) == "1"

        return attrs

    @property
    def force_update(self) -> bool:
        """Force state updates."""
        return True
