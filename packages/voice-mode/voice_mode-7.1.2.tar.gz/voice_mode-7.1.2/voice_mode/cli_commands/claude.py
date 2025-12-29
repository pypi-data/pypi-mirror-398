"""CLI commands for Claude-related functionality."""

import click


@click.group(name='claude')
def claude_group():
    """Claude-related commands."""
    pass


@click.group(name='hooks')
def hooks_group():
    """Manage Voice Mode hooks and event handlers for Claude Code."""
    pass