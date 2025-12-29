import click


@click.group()
def cli():
    """Commands for managing a Purse-enabled wallet"""


if __name__ == "__main__":
    cli()
