r"""
# Omnata Plugin Runtime

This runtime provides a Python-based plugin system for Omnata.

The runtime is kept separate from the Devkit in order to keep runtime dependencies to a minimum.

It contains several submodules:

## api

Used internally for the interface between the plugin and the Omnata engine. Not intended for use by plugin developers.

## configuration

Data classes used by the configuration process

## forms

Containers for form elements, used by the Omnata UI to render configuration forms during connection and sync setup.

## omnata_plugin

The main plugin engine, contains the OmnataPlugin class which is subclassed when creating a plugin, as well as
related classes for handling requests and responses.

## rate_limiting

Functionality for rate limiting API calls to remote systems.

## record_transformer

Record transformation functionality. Source records are transformed during each sync run in order to check for differences.
This is a lightweight operation achieved via User-Defined-Functions, so record transformers are kept separate from the
plugin code to further minimise dependancies.

"""

__docformat__ = "markdown"  # explicitly disable rST processing in the examples above.

# if we're running inside Snowflake, we want to default the snowflake logging to WARN
# so that we don't get a ton of snowflake queries in the logs
import sys
import logging
if "snowflake_import_directory" in sys._xoptions:
    logger = logging.getLogger("snowflake")
    logger.setLevel(logging.WARN)  # we don't want snowflake queries being logged by default
