# utils.py

import click


def echo(text: str):
    click.echo(text)


def echoc(text: str, color: str):
    click.echo(click.style(text, fg=color))
