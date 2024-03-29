# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased 0.2.0-beta]
### Added
- Added support for realtime meter and powerflow data
- Added sample data for smartmeter, powerflow and cummulation inverter data
- Added the serial number of the inverter as an additional tag

### Changed
- Updated the configuration options of the config file
- Moved InfluxDB client configuration to `*.ini` file

## [0.1.0] - 2023-06-01
### Added
- Basic application to upload Fronius inverter data to InfluxDB
- Sample YAML config-file for user specific configuration
- Dockerfile for container-based execution 
- Adapted development/test server and sample data from [fronius-to-influx](https://github.com/szymi-/fronius-to-influx)