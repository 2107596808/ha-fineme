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

JS_URLS = [
    "/fineme/fineme-amap-card.js",
    "/fineme/fineme-bmap-card.js",
    "/fineme/fineme-gmap-card.js",
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Fineme integration (called once per HA start)."""
    # Register static path for map card JS files
    www_dir = os.path.join(os.path.dirname(__file__), "www")
    if os.path.isdir(www_dir):
        try:
            await hass.http.async_register_static_paths([
                StaticPathConfig("/fineme", www_dir, cache_headers=False)
            ])
            _LOGGER.debug("Registered static path /fineme -> %s", www_dir)
        except Exception as err:
            _LOGGER.warning("Failed to register static path: %s", err)

    return True


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

    # Try to auto-register Lovelace resources (best-effort)
    await _async_register_lovelace_resources(hass)

    return True


async def _async_register_lovelace_resources(hass: HomeAssistant) -> None:
    """Register map card JS files as Lovelace resources (best-effort)."""
    try:
        # Try to access Lovelace resource storage
        from homeassistant.components.lovelace.resources import ResourceStorageCollection

        # Find the resource collection from hass.data
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is None:
            _LOGGER.debug("Lovelace data not available yet, skipping auto-registration")
            return

        res_collection = getattr(lovelace_data, "resources", None)
        if res_collection is None:
            _LOGGER.debug("Lovelace resource collection not found")
            return

        # Get existing resource URLs
        existing_urls = set()
        for res in res_collection.async_items():
            url = res.get("url", "")
            existing_urls.add(url)

        # Register each JS URL if not already present
        for url in JS_URLS:
            if url not in existing_urls:
                await res_collection.async_create_item({
                    "res_type": "module",
                    "url": url,
                })
                _LOGGER.info("Registered Lovelace resource: %s", url)
            else:
                _LOGGER.debug("Already registered: %s", url)

    except Exception as err:
        _LOGGER.debug(
            "Auto-registration of map cards failed (this is normal on some HA setups). "
            "Please add the resources manually. Error: %s", err
        )
        _LOGGER.info(
            "To use map cards, manually add these Lovelace resources "
            "(Settings > Dashboards > Resources): %s",
            ", ".join(JS_URLS),
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
