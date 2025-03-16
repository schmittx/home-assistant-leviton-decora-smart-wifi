[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
# Leviton Decora Smart Wi-Fi Home Assistant Integration
Custom component to allow control of [Leviton Decora Smart Wi-Fi devices](https://www.leviton.com/en/products/brands/decora-smart) in [Home Assistant](https://home-assistant.io).

## Features
- This is an complete rewrite of the existing Home Assistant core integration with support for additional devices.
- Additional entities have been added to manage configuration for each device as well (ex. auto shutoff, max/min dimming levels, etc.).
- Support for activities (`button`), Home/Away status (`select`), scenes (`scene`), and schedules (`switch`) is also included.
- Support for two-factor authentication.

## Install
1. Ensure Home Assistant is updated to version 2025.3.0 or newer.
2. Use HACS and add as a [custom repo](https://hacs.xyz/docs/faq/custom_repositories); or download and manually move to the `custom_components` folder.
3. Once the integration is installed follow the standard process to setup via UI and search for `Leviton Decora Smart Wi-Fi`.
4. Follow the prompts.

## Options
- Residences and devices can be updated via integration options.
- If `Advanced Mode` is enabled for the current profile, additional options are available (interval, timeout, and response logging).

## Supported Devices
### Controllers
- D2SCS
- DW4BC
### Fans
- D24SF
- DW4SF
### GFCI Outlets
- D2GF1
- D2GF2
### Lights
- D23LP
- D26HD
- D2ELV
- D2MSD
- DW1KD
- DW3HL
- DW6HD
- DWVAA
### Motion Sensors
- D2MSD
### Outlets
- D215P
- D215R
- DW15A
- DW15P
- DW15R
### Switches
- D215O
- D215S
- D2SCS
- DW15S

## Future Plans
- Websocket support to allow for cloud push updates (any help with this would be appreciated as I have no experience with async and websockets).
- Control of night settings start/end time
- Support for D2GF2, DN15S, DN6HD, MLWSB
