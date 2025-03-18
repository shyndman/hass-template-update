"""Platform for template update integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template

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
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


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
        self._installed_version_template = Template(config[CONF_INSTALLED_VERSION])
        self._installed_version_template.hass = hass

        self._latest_version_template = Template(config[CONF_LATEST_VERSION])
        self._latest_version_template.hass = hass

        if CONF_RELEASE_NOTES in config:
            self._release_notes_template = Template(config[CONF_RELEASE_NOTES])
            self._release_notes_template.hass = hass
        else:
            self._release_notes_template = None

        if CONF_TITLE in config:
            self._title_template = Template(config[CONF_TITLE])
            self._title_template.hass = hass
        else:
            self._title_template = None

        if CONF_ENTITY_PICTURE in config:
            self._entity_picture_template = Template(config[CONF_ENTITY_PICTURE])
            self._entity_picture_template.hass = hass
        else:
            self._entity_picture_template = None

        if CONF_AVAILABILITY in config:
            self._availability_template = Template(config[CONF_AVAILABILITY])
            self._availability_template.hass = hass
        else:
            self._availability_template = None

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
        except (ValueError, TypeError):
            _LOGGER.exception(
                "Error getting installed version for %s",
                self._attr_name,
            )
            return None
        else:
            return version

    @property
    @override
    def latest_version(self) -> str | None:
        """Return the latest version."""
        try:
            version = str(self._latest_version_template.async_render())
            _LOGGER.debug("Entity %s latest version: %s", self._attr_name, version)
        except (ValueError, TypeError):
            _LOGGER.exception(
                "Error getting latest version for %s",
                self._attr_name,
            )
            return None
        else:
            return version

    @property
    @override
    def release_notes(self) -> str | None:
        """Return the release notes."""
        if not self._release_notes_template:
            return None
        try:
            notes = str(self._release_notes_template.async_render())
            _LOGGER.debug("Entity %s release notes: %s", self._attr_name, notes)
        except (ValueError, TypeError):
            _LOGGER.exception(
                "Error getting release notes for %s",
                self._attr_name,
            )
            return None
        else:
            return notes

    @property
    @override
    def title(self) -> str | None:
        """Return the title."""
        if not self._title_template:
            return None
        try:
            title = str(self._title_template.async_render())
            _LOGGER.debug("Entity %s title: %s", self._attr_name, title)
        except (ValueError, TypeError):
            _LOGGER.exception("Error getting title for %s", self._attr_name)
            return None
        else:
            return title

    @property
    @override
    def entity_picture(self) -> str | None:
        """Return the entity picture."""
        if not self._entity_picture_template:
            return None
        try:
            picture = str(self._entity_picture_template.async_render())
            _LOGGER.debug("Entity %s picture: %s", self._attr_name, picture)
        except (ValueError, TypeError):
            _LOGGER.exception(
                "Error getting entity picture for %s",
                self._attr_name,
            )
            return None
        else:
            return picture

    @property
    @override
    def available(self) -> bool:
        """Return if the entity is available."""
        if not self._availability_template:
            return True
        try:
            available = bool(self._availability_template.async_render())
            _LOGGER.debug("Entity %s availability: %s", self._attr_name, available)
        except (ValueError, TypeError):
            _LOGGER.exception(
                "Error getting availability for %s",
                self._attr_name,
            )
            return False
        else:
            return available

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
        except TemplateError:
            _LOGGER.exception(
                "Entity %s error rendering template %s",
                self._attr_name,
                template_str,
            )
            return None
        else:
            return result

    @override
    async def async_install(
        self, version: str | None, *, should_backup: bool = True, **kwargs: Any
    ) -> None:
        """Install an update."""
        _LOGGER.debug(
            "Entity %s installing update: version=%s, should_backup=%s, kwargs=%s",
            self._attr_name,
            version,
            should_backup,
            kwargs,
        )

        # Prepare data for action call
        data = {
            "version": version,
            "backup": should_backup,
            **kwargs,
        }

        # Get the action call configuration
        install_action = self._config.get(CONF_INSTALL_ACTION)
        if install_action is None:
            _LOGGER.warning(
                "Entity %s has no install action configured", self._attr_name
            )
            return

        action = self._render_template(install_action["action"])
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
    _hass: HomeAssistant,
    _config: ConfigType,
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
