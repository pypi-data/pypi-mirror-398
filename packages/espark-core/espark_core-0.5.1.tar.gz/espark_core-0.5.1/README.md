# Espark

Espark is a lightweight framework for building scalable and efficient ESP32-based IoT applications. It provides a modular architecture, easy-to-use APIs, and built-in support for common IoT protocols.

## Project Goals

- Simplify the development of ESP32 applications.
- Provide a modular and extensible architecture.
- Support common IoT protocols like MQTT.
- Ensure efficient resource management for low-power devices.
- Provide a clean and easy-to-use API.
- Provide an user-friendly UI for configuration and monitoring.

## Features

- **Device Provisioning**: Easy setup and configuration of ESP32 devices.
- **Telemetry Collection**: Built-in support for collecting and sending telemetry data.
- **Scalable Architecture**: Designed to handle a large number of devices efficiently.
- **Seamless Communication**: Support for MQTT protocol.

## Hardware Requirements

- ESP32 Development Board
- USB Cable for programming and power
- Optional: Sensors and triggers for specific applications

## Project Structure

```
espark/
├── espark-core/
│   ├── esparkcore/      # FastAPI backend framework
│   │   ├── data/              # Models, repositories
│   │   ├── routers/           # API endpoints
│   │   ├── schedules/         # Background tasks
│   │   ├── services/          # Business logic, MQTT handling
│   │   └── utils/             # Utility functions
│   └── Makefile
├── espark-node/
│   ├── esparknode/      # MicroPython application framework
│   │   ├── actions/           # Action handlers
│   │   ├── data/              # Data storage
│   │   ├── libraries/         # External libraries
│   │   ├── networks/          # Network management
│   │   ├── sensors/           # Sensor interfaces
│   │   ├── triggers/          # Trigger interfaces
│   │   ├── utils/             # Utility functions
│   │   └── base_node.py       # Main application file
│   └── Makefile
└── espark-react/        # React frontend application
    ├── src/
    │   ├── data/              # Data models and data providers
    │   ├── i18n/              # Internationalization files
    │   ├── pages/             # Application pages
    │   ├── routes/            # Application routing
    │   ├── utils/             # Utility functions
    │   ├── App.tsx            # Main application component
    │   └── index.tsx          # Application entry point
    └── package.json
```

## Development Workflows

### Setting up the backend

1. Add espark-core as a dependency in your FastAPI project.
2. Configure database connections and MQTT settings as environment variables.
3. Implement additional data models, repositories, routers, and business logic if needed.
4. Add the `DeviceRouter`, `TelemetryRouter`, and other additional routers to your FastAPI app.

### Setting up the ESP32 application

1. Clone the espark-node repository to your local machine.
2. Copy `espark-core/Makefile.template` to `Makefile` and customize it for your device.
3. Run `make upgrade` to copy the espark-core library to your device project.
4. Implement device-specific actions, sensors, and triggers as needed.
5. Run `make flash` to upload the firmware to your ESP32 device.
6. Run `make deploy` to upload the application to the device.

### Setting up the frontend

1. Add espark-react as a dependency in your React project.
2. Render `<EsparkApp />` in your main application file.

### Configurations

- **espark-core**: Use environment variables, or `.env` file, for database and MQTT configurations.
- **espark-node**: Use `esparknode.configs` for device-specific configurations.
- **espark-react**: Customise `EsparkApp` props for application settings.

## Examples and Patterns

- **Router Example**: `device_router.py` in `espark-core/esparkcore/routers/` demonstrates how to create API endpoints for device management.
- **Respository Example**: `device_repository.py` in `espark-core/esparkcore/data/repositories/` shows how to implement data access logic for devices.
- **Action Example**: `esp32_relay.py` in `espark-node/esparknode/actions/` illustrates how to define actions for ESP32 devices.
- **Sensor Example**: `sht20_sensor.py` in `espark-node/esparknode/sensors/` demonstrates how to read data from a SHT20 sensor.
- **Trigger Example**: `gpio_trigger.py` in `espark-node/esparknode/triggers/` shows how to create GPIO-based triggers for device actions.
- **List, Show, Edit Screens Example**: `DeviceList`, `DeviceShow`, and `DeviceEdit` components in `espark-react/src/pages/devices/` demonstrate how to create CRUD screens for device management.

## Example Projects

- **Espartan**: A smart thermostat and open-door alert automation system using ESP32-C3 devices, leveraging espark for device management and telemetry, available at [https://github.com/ayltai/Espartan](https://github.com/ayltai/Espartan).
