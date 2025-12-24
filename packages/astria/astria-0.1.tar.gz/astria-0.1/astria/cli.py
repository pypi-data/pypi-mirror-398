import os

import click

from .clean import connect_to_email

from .unsubscribe import search_for_email

ENV_FILE = "setup_op.env"


@click.group()
def astria():
    pass


@astria.command()
@click.option(
    "--provider",
    prompt="Enter your email provider",
    type=click.Choice(["Gmail", "Outlook", "Icloud", "Hotmail"], case_sensitive=False),
)
@click.option("--address", prompt="Enter your email address")
@click.option("--password", prompt="Enter your app password", hide_input=True)
def setup(provider, address, password):
    """Creates local configuration file."""
    try:
        with open(ENV_FILE, "w") as f:
            f.write(f"PROVIDER={provider}\n")
            f.write(f"ADDRESS={address}\n")
            f.write(f"PASSWORD={password}\n")
        click.echo("Configuration saved!")
    except Exception as e:
        click.echo(f"Error saving file: {e}")


@astria.command()
def unsubscribe():
    """Saves all the "unsubscribe" links to "links.txt" """
    creds = {}

    if os.path.exists(ENV_FILE):
        click.echo("Loading credentials from file...")
        with open(ENV_FILE, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    creds[key] = value

        if "ADDRESS" in creds and "PASSWORD" in creds:
            search_for_email(
                creds["PROVIDER"],
                creds["ADDRESS"],
                creds["PASSWORD"],
            )
        else:
            click.echo(
                "Error: Missing ADDRESS or PASSWORD in setup file. Run 'setup' again."
            )

    else:
        click.echo("Error: No credentials found please run 'setup' command first")


@astria.command()
@click.option(
    "--selection",
    prompt="Enter the type of mails you want to delete",
    type=click.Choice(["Newsletters", "Custom", "All"], case_sensitive=False),
)
def clean_email(selection):
    """Connects and cleans
    email using saved credentials."""
    address = ""
    if selection == "Custom":
        address = input("Enter the specific email address you want to delete: ")

    creds = {}

    if os.path.exists(ENV_FILE):
        click.echo("Loading credentials from file...")
        with open(ENV_FILE, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    creds[key] = value

        if "ADDRESS" in creds and "PASSWORD" in creds:
            connect_to_email(
                creds["PROVIDER"],
                creds["ADDRESS"],
                creds["PASSWORD"],
                selection,
                address,
            )
        else:
            click.echo(
                "Error: Missing ADDRESS or PASSWORD in setup file. Run 'setup' again."
            )

    else:
        click.echo("Error: No credentials found please run 'setup' command first")


if __name__ == "__main__":
    astria()
