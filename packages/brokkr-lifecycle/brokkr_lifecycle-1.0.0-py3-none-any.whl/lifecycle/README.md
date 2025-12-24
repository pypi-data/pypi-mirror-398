# Brokkr Lifecycle Management Package

This package provides lifecycle management functionality for Brokkr Bridge infrastructure, including device discovery, decommissioning, and status management.

## Installation

```bash
pip install brokkr-lifecycle
```

## Components

- **discovery.py** - Device discovery and inventory management
- **decommission.py** - Device decommissioning workflows
- **lockscreen.py** - Device status and lock screen management
- **ipmi_reset.py** - IPMI reset functionality
- **common/** - Shared utilities and configuration

## Usage

```bash
# Device discovery
brokkr-collector

# Device decommissioning
brokkr-decommission

# Lock screen management
brokkr-lockscreen

# IPMI reset
brokkr-ipmi-reset
```