"""Template update integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_AUTO_UPDATE,
    CONF_AVAILABILITY,
    CONF_DEVICE_CLASS,
    CONF_ENTITY_PICTURE,
    CONF_INSTALL_ACTION,
    CONF_INSTALLED_VERSION,
    CONF_LATEST_VERSION,
    CONF_NAME,
    CONF_RELEASE_NOTES,
    CONF_TITLE,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

# Error messages
_INSTALL_NOT_IMPLEMENTED_MSG = "Installation not implemented"
_NO_ACTION_SPECIFIED_MSG = "No action specified in install_action"
_INVALID_INSTALL_ACTION_MSG = "Invalid install_action configuration"
_ERROR_RENDERING_TEMPLATE_MSG = "Error rendering install action: {}"


class TemplateUpdateEntity(UpdateEntity):
    """Template Update entity."""

    def __init__(self, hass: HomeAssistant, config: ConfigType) -> None:
        """Initialize the template update entity."""
        _LOGGER.debug("Initializing template update entity with config: %s", config)
        self._hass = hass
        self._config = config
        self._attr_name = config.get(CONF_NAME)
        self._attr_unique_id = config.get(CONF_NAME)

        # Set supported features based on configuration
        self._attr_supported_features = UpdateEntityFeature(0)
        if config.get(CONF_INSTALL_ACTION):
            _LOGGER.debug("Entity %s supports installation", self._attr_name)
            self._attr_supported_features |= UpdateEntityFeature.INSTALL
            # If install_action is configured, also enable SPECIFIC_VERSION
            self._attr_supported_features |= UpdateEntityFeature.SPECIFIC_VERSION
        if config.get(CONF_RELEASE_NOTES):
            _LOGGER.debug("Entity %s supports release notes", self._attr_name)
            self._attr_supported_features |= UpdateEntityFeature.RELEASE_NOTES

        # Configure auto-update
        self._attr_auto_update = config.get(CONF_AUTO_UPDATE, False)
        _LOGGER.debug(
            "Entity %s auto_update: %s", self._attr_name, self._attr_auto_update
        )

        # Set up templates
        _LOGGER.debug("Setting up templates for entity %s", self._attr_name)
        self._installed_version_template = Template(
            config[CONF_INSTALLED_VERSION], hass
        )
        self._latest_version_template = Template(config[CONF_LATEST_VERSION], hass)
        self._release_notes_template = Template(
            config.get(CONF_RELEASE_NOTES, ""), hass
        )
        self._title_template = Template(config.get(CONF_TITLE, ""), hass)
        self._entity_picture_template = Template(
            config.get(CONF_ENTITY_PICTURE, ""), hass
        )
        self._availability_template = Template(config.get(CONF_AVAILABILITY, ""), hass)

        # Install action configuration
        self._install_action = config.get(CONF_INSTALL_ACTION, {})
        if self._install_action:
            _LOGGER.debug(
                "Entity %s install action: %s", self._attr_name, self._install_action
            )

        # Set device class if specified
        if device_class := config.get(CONF_DEVICE_CLASS):
            self._attr_device_class = device_class
            _LOGGER.debug("Entity %s device class: %s", self._attr_name, device_class)

    @property
    @override
    def installed_version(self) -> str | None:
        """Return the installed version."""
        try:
            version = str(self._installed_version_template.async_render())
            _LOGGER.debug("Entity %s installed version: %s", self._attr_name, version)
            return version
        except (ValueError, TypeError) as err:
            _LOGGER.error(
                "Error getting installed version for %s: %s", self._attr_name, err
            )
            return None

    @property
    @override
    def latest_version(self) -> str | None:
        """Return the latest version."""
        try:
            version = str(self._latest_version_template.async_render())
            _LOGGER.debug("Entity %s latest version: %s", self._attr_name, version)
            return version
        except (ValueError, TypeError) as err:
            _LOGGER.error(
                "Error getting latest version for %s: %s", self._attr_name, err
            )
            return None

    @override
    def release_notes(self) -> str | None:
        """Return the release notes."""
        try:
            notes = str(self._release_notes_template.async_render())
            _LOGGER.debug("Entity %s release notes: %s", self._attr_name, notes)
            return notes
        except (ValueError, TypeError) as err:
            _LOGGER.error(
                "Error getting release notes for %s: %s", self._attr_name, err
            )
            return None

    @property
    @override
    def title(self) -> str | None:
        """Return the title."""
        try:
            title = str(self._title_template.async_render())
            _LOGGER.debug("Entity %s title: %s", self._attr_name, title)
            return title
        except (ValueError, TypeError) as err:
            _LOGGER.error("Error getting title for %s: %s", self._attr_name, err)
            return None

    @property
    @override
    def entity_picture(self) -> str | None:
        """Return the entity picture."""
        try:
            picture = str(self._entity_picture_template.async_render())
            _LOGGER.debug("Entity %s picture: %s", self._attr_name, picture)
            return picture
        except (ValueError, TypeError) as err:
            _LOGGER.error(
                "Error getting entity picture for %s: %s", self._attr_name, err
            )
            return None

    @property
    @override
    def available(self) -> bool:
        """Return if the entity is available."""
        if not self._availability_template:
            return True
        try:
            available = bool(self._availability_template.async_render())
            _LOGGER.debug("Entity %s availability: %s", self._attr_name, available)
            return available
        except (ValueError, TypeError) as err:
            _LOGGER.error("Error getting availability for %s: %s", self._attr_name, err)
            return False

    def _render_template(self, template_str: str | Template) -> str | None:
        """Render a template string."""
        if not template_str:
            return None

        try:
            if isinstance(template_str, Template):
                result = template_str.async_render()
            else:
                template = Template(template_str)
                template.hass = self._hass
                result = template.async_render()
            _LOGGER.debug(
                "Entity %s template render: %s -> %s",
                self._attr_name,
                template_str,
                result,
            )
            return result
        except TemplateError as err:
            _LOGGER.exception(
                "Entity %s error rendering template %s: %s",
                self._attr_name,
                template_str,
                err,
            )
            return None

    @override
    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install an update."""
        _LOGGER.debug(
            "Entity %s installing update: version=%s, backup=%s, kwargs=%s",
            self._attr_name,
            version,
            backup,
            kwargs,
        )

        # Prepare data for action call
        data = {
            "version": version,
            "backup": backup,
            **kwargs,
        }

        # Get the action call configuration
        install_action = self._config.get(CONF_INSTALL_ACTION)
        if install_action is None:
            _LOGGER.warning(
                "Entity %s has no install action configured", self._attr_name
            )
            return

        action = self._render_template(install_action)
        if not action:
            _LOGGER.error("Entity %s failed to render install action", self._attr_name)
            return

        # Call the action
        domain, action_name = action.split(".", 1)
        _LOGGER.debug(
            "Entity %s calling service %s.%s with data: %s",
            self._attr_name,
            domain,
            action_name,
            data,
        )
        await self.hass.services.async_call(domain, action_name, data)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up template update platform."""
    if discovery_info is None:
        _LOGGER.debug("No discovery info provided")
        return

    if "entities" not in discovery_info:
        _LOGGER.debug("No entities in discovery info")
        return

    _LOGGER.debug(
        "Setting up template update platform with entities: %s",
        discovery_info["entities"],
    )
    async_add_entities(discovery_info["entities"])
