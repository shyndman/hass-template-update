# Template Update for Home Assistant

A Home Assistant integration that provides template-based update entities, allowing you to create update entities whose properties are evaluated using templates.

## Features

- Create update entities with templated properties
- Support for all standard update entity attributes (installed_version, latest_version, release_notes, etc.)
- Bulk creation of update entities using the `for_each` pattern
- YAML-based configuration (no UI flow needed)
- Template support for all properties
- Customizable installation actions through templates

## Installation

1. Copy the `custom_components/template_update` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

Add the following to your `configuration.yaml`:

```yaml
template_update:
  # Single update entity
  - vacuum_firmware:
      name: "Vacuum Firmware"
      installed_version: >-
        {{ states('sensor.vacuum_current_version') }}
      latest_version: >-
        {{ states('sensor.vacuum_latest_version') }}
      release_notes: >-
        {{ states('sensor.vacuum_release_notes') }}
      title: "Vacuum Firmware Update"
      entity_picture: >-
        {{ states('sensor.vacuum_icon') }}
      availability: >-
        {{ states('sensor.vacuum_online') == 'online' }}
      install_action:
        action: vacuum.firmware_update
        target:
          entity_id: vacuum.my_vacuum

  # Multiple updates using for_each
  - device_updates:
      for_each:
        - device_id: vacuum_1
          name: "Vacuum 1"
          model: premium
        - device_id: vacuum_2
          name: "Vacuum 2"
          model: standard
      update:
        name: "{{ item.name }} Firmware"
        installed_version: >-
          {{ states('sensor.vacuum_' + item.device_id + '_version') }}
        latest_version: >-
          {{ states('sensor.vacuum_' + item.device_id + '_latest_version') }}
        release_notes: >-
          {{ states('sensor.vacuum_' + item.device_id + '_release_notes') }}
        title: "{{ item.name }} Update"
        availability: >-
          {{ states('binary_sensor.vacuum_' + item.device_id + '_online') == 'on' }}
        install_action:
          action: mqtt.publish
          data:
            topic: >-
              vacuum/{{ item.device_id }}/cmd/update
            payload: >-
              {
                "model": "{{ item.model }}",
                "device_id": "{{ item.device_id }}",
                "command": "start_update"
              }

  # Using template-based install action
  - system_update:
      name: "System Update"
      installed_version: >-
        {{ states('sensor.current_version') }}
      latest_version: >-
        {{ states('sensor.latest_version') }}
      install_action:
        action: >-
          {% if is_state('switch.maintenance_mode', 'off') %}
            script.start_update_in_maintenance_mode
          {% else %}
            script.start_update
          {% endif %}
        data:
          system: main

  # With auto-update enabled
  - auto_updating_firmware:
      name: "Auto-Updating Firmware"
      installed_version: >-
        {{ states('sensor.firmware_version') }}
      latest_version: >-
        {{ states('sensor.latest_firmware') }}
      auto_update: true
      install_action:
        action: script.update_firmware
```

### Configuration Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| name | string | yes | The name of the update entity |
| installed_version | template | yes | Template for the currently installed version |
| latest_version | template | yes | Template for the latest available version |
| release_notes | template | no | Template for the release notes |
| title | template | no | Template for the update title |
| entity_picture | template | no | Template for the entity picture |
| device_class | string | no | The device class of the update entity |
| availability | template | no | Template for the entity availability |
| install_action | object | no | Action to perform when installing the update |
| auto_update | boolean | no | Whether the entity has auto-update enabled. If true, skipping updates is not allowed. Defaults to false |

### Install Action Format

The `install_action` configuration uses a standard Home Assistant action format:

```yaml
install_action:
  action: domain.action_name
  target:
    entity_id: entity.to_call
  data:
    parameter: value
    another_parameter: >-
      {{ template_value }}
```

## Development

This project uses:
- Python 3.13
- uv for dependency management
- ruff for linting
- hatchling for building

### Setup Development Environment

1. Clone this repository
2. Open in VS Code with Dev Containers
3. Run `scripts/setup` to set up the development environment
4. Run `scripts/develop` to start Home Assistant with this integration

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
