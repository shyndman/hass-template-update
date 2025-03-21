"""The Template Update integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_NAME,
    Platform,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_AUTO_UPDATE,
    CONF_AVAILABILITY,
    CONF_ELEMENTS,
    CONF_ENTITY_PICTURE,
    CONF_FOR_EACH,
    CONF_INSTALL_ACTION,
    CONF_INSTALLED_VERSION,
    CONF_LATEST_VERSION,
    CONF_RELEASE_NOTES,
    CONF_TITLE,
    CONF_UPDATE,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

    from .update import TemplateUpdateEntity

_LOGGER = logging.getLogger(__name__)

ACTION_SCHEMA = vol.Schema(
    {
        vol.Required("action"): cv.string,
        vol.Optional("data"): dict,
        vol.Optional("target"): dict,
    }
)

TEMPLATE_UPDATE_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_INSTALLED_VERSION): cv.string,
        vol.Required(CONF_LATEST_VERSION): cv.string,
        vol.Optional(CONF_RELEASE_NOTES): cv.string,
        vol.Optional(CONF_TITLE): cv.string,
        vol.Optional(CONF_ENTITY_PICTURE): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): cv.string,
        vol.Optional(CONF_AVAILABILITY): cv.string,
        vol.Optional(CONF_INSTALL_ACTION): ACTION_SCHEMA,
        vol.Optional(CONF_AUTO_UPDATE, default=False): cv.boolean,
    }
)

TEMPLATE_UPDATE_FOR_EACH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FOR_EACH): vol.Schema(
            {
                vol.Required(CONF_ELEMENTS): vol.All(cv.ensure_list, [dict]),
                vol.Required(CONF_UPDATE): TEMPLATE_UPDATE_ITEM_SCHEMA,
            }
        )
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [vol.Or(TEMPLATE_UPDATE_ITEM_SCHEMA, TEMPLATE_UPDATE_FOR_EACH_SCHEMA)],
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the template update integration."""
    _LOGGER.debug("Setting up template_update integration with config: %s", config)

    if DOMAIN not in config:
        _LOGGER.debug("No configuration found for %s", DOMAIN)
        return True

    entities = []
    domain_config = config[DOMAIN]
    _LOGGER.debug("Processing %d template update configurations", len(domain_config))

    for update_config in domain_config:
        if CONF_FOR_EACH in update_config:
            # Handle for_each configuration
            for_each_node = update_config[CONF_FOR_EACH]
            for_each_entities = _process_for_each_config(
                hass,
                for_each_node[CONF_ELEMENTS],
                for_each_node[CONF_UPDATE],
            )
            entities.extend(for_each_entities)
        else:
            # Handle single entity configuration
            _LOGGER.debug("Processing single entity configuration: %s", update_config)
            entity = _create_entity_from_config(hass, update_config)
            entities.append(entity)
            _LOGGER.debug(
                "Added single template update entity: %s",
                update_config.get(CONF_NAME, "unnamed"),
            )

    await _load_entities(hass, entities, config)
    return True


def _process_for_each_config(
    hass: HomeAssistant, loop_elements: list, update_template: dict
) -> list[TemplateUpdateEntity]:
    """Process a for_each configuration, creating entities for each item."""
    entities = []
    _LOGGER.debug(
        "Processing for_each configuration with %d items and template: %s",
        len(loop_elements),
        update_template,
    )

    for item in loop_elements:
        _LOGGER.debug("Processing for_each item: %s", item)
        template_vars = {"item": item}

        # Create and process the configuration
        entity_config = _process_template_config(hass, update_template, template_vars)

        # Create and add the entity
        entity = _create_entity_from_config(hass, entity_config, item.get("device_id"))
        entities.append(entity)
        _LOGGER.debug("Added entity: %s", entity_config.get(CONF_NAME))

    return entities


def _render_template_value(
    hass: HomeAssistant, value: str, template_vars: dict
) -> str | None:
    """Render a template string with variables."""
    try:
        rendered_value = Template(value, hass).async_render(template_vars)
        _LOGGER.debug("Rendered template: %s -> %s", value, rendered_value)
    except Exception:
        _LOGGER.exception("Error rendering template: %s", value)
        return None
    else:
        return rendered_value


def _process_template_config(
    hass: HomeAssistant, update_template: dict, template_vars: dict
) -> dict:
    """Process a template configuration, rendering all string values."""
    entity_config = {}

    for key, value in update_template.items():
        if isinstance(value, str):
            rendered_value = _render_template_value(hass, value, template_vars)
            if rendered_value is not None:
                entity_config[key] = rendered_value
                _LOGGER.debug("Set %s = %s", key, rendered_value)
        else:
            entity_config[key] = value
            _LOGGER.debug("Copied non-template value for %s: %s", key, value)

    return entity_config


def _create_entity_from_config(
    hass: HomeAssistant, entity_config: dict, item_id: str | None = None
) -> TemplateUpdateEntity:
    """Create a TemplateUpdateEntity from a configuration dictionary."""
    # Import here to avoid circular imports
    from .update import TemplateUpdateEntity

    # Set default name if not provided
    if item_id and CONF_NAME not in entity_config:
        entity_config[CONF_NAME] = f"{DOMAIN}_{item_id}"

    _LOGGER.debug("Creating entity with config: %s", entity_config)
    return TemplateUpdateEntity(hass, entity_config)


async def _load_entities(
    hass: HomeAssistant, entities: list[TemplateUpdateEntity], config: ConfigType
) -> None:
    """Load entities through the discovery service."""
    if not entities:
        _LOGGER.warning("No template update entities were created")
        return

    _LOGGER.debug("Loading %d template update entities via discovery", len(entities))
    try:
        await discovery.async_load_platform(
            hass,
            Platform.UPDATE,
            DOMAIN,
            {"entities": entities},
            config,
        )
        _LOGGER.debug("Successfully loaded template update entities")
    except Exception:
        _LOGGER.exception("Error loading template update entities")
