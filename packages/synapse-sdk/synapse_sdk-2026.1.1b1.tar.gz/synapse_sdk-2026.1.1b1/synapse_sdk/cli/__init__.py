"""Synapse SDK CLI.

Usage:
    synapse --help
    synapse run <plugin> <action> [--params JSON]
    synapse config <path> [--format yaml|json]
    synapse version
"""

from synapse_sdk.cli.main import cli

__all__ = ['cli']
