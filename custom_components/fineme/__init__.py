"""The Fineme GPS Tracker integration."""

import logging
import os

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import FinemeAPI
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import FinemeCoordinator

_LOGGER = logging.getLogger(__name__)

JS_URL = f"/fineme/fineme-amap-card.js"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fineme GPS Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api = FinemeAPI()
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = FinemeCoordinator(
        hass=hass,
        api=api,
        config_data=entry.data,
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Register static path for Lovelace card
    www_dir = os.path.join(os.path.dirname(__file__), "www")
    if os.path.isdir(www_dir):
        await hass.http.async_register_static_paths([
            StaticPathConfig("/fineme", www_dir, cache_headers=False)
        ])

    # Auto-register AMap card as Lovelace resource
    await _async_register_lovelace_resource(hass)

    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register the AMap card JS as a Lovelace resource."""
    try:
        from homeassistant.components.lovelace import (
            resources,
            ResourceNotFound,
        )
        from homeassistant.components.lovelace.resources import ResourceCollection

        # Access the resource collection
        ll_conf = hass.data.get("lovelace")
        if ll_conf is None:
            return

        res_collection = getattr(ll_conf, "resources", None)
        if res_collection is None:
            return

        # Check if already registered
        for res in res_collection.async_items():
            if res.get("url") == JS_URL:
                _LOGGER.debug("AMap card resource already registered")
                return

        # Register new resource
        await res_collection.async_create_item({
            "res_type": "module",
            "url": JS_URL,
        })
        _LOGGER.info("Registered AMap card resource: %s", JS_URL)

    except Exception as err:
        _LOGGER.warning(
            "Could not auto-register AMap card. "
            "Please add %s as a Lovelace resource manually: %s",
            JS_URL, err
        )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
