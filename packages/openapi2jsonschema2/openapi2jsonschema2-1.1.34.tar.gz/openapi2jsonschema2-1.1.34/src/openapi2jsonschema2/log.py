#!/usr/bin/env python

import click


def info(message: str) -> None:
    """
    Prints an informational message to the console in green color.
    """
    click.echo(click.style(message, fg="green"), color=True)


def debug(message: str) -> None:
    """
    Prints a debug message to the console in yellow color.
    """
    click.echo(click.style(message, fg="yellow"), color=True)


def error(message: str) -> None:
    """
    Prints an error message to the console in red color.
    """
    click.echo(click.style(message, fg="red"), color=True)
