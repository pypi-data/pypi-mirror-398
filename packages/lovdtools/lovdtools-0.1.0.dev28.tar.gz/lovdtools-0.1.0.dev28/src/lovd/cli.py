"""
LOVDTools CLI
=============

This module provides a command-line interface for the LOVDTools API client.

"""

from __future__ import annotations

import logging

import click

from .client import LOVDClient
from .config import options
from .constants import ACQUISITION_CONFIG_PATH, LOVDTOOLS_VERSION


# : API client initialization
#
client = LOVDClient()


# : command-line interface
#
@click.group(invoke_without_command=True)
@click.option(
    "--version",
    "-V",
    is_flag=True,
    help="Show `lovdtools`'s version string and exit."
)
@click.pass_context
def cli(ctx, version):
    """LOVDTools – An API client for the global–shared LOVD instance.

    This is a command-line interface for the LOVD API client, which
    provides various utilities for querying the global–shared instance
    of the Leiden Open Variants Database (LOVD).

    """
    logging.basicConfig(level="INFO", format="%(name)s – %(levelname)s: %(message)s")
    ctx.logger = logging.getLogger(__name__)

    ctx.logger.debug("Logger setup complete.")

    if version:
        click.echo(f"lovdtools, v{LOVDTOOLS_VERSION}")

    if not ctx.invoked_subcommand and not version:
        click.echo(ctx.get_help())


@cli.group()
def config():
    pass


@config.command(name="show")
def show_config():
    """List all configuration options, along with their current values."""
    print()
    print("LOVDTools Configuration")
    print("─" * 70)

    for k, v in options.items():
        print(f"o    {k}: {v}")

    print("─" * 70 + "\n")


@config.command(name="get")
@click.argument("key", metavar="KEY", required=True)
def get_config_option(key: str):
    """Get the current value of a specific configuration option."""
    print(f"\n{key.lower()}: {options[key]}\n")


@config.command(name="set")
@click.argument("key", metavar="KEY", required=True)
@click.argument("value", nargs=-1, metavar="VALUE", required=True)
def set_config_option(key: str, value: tuple[str]):
    """Set the current value of a specific configuration option."""
    try:
        # Join the tuple elements into a single string
        value_str = " ".join(value)
        
        # Determine if this key should be a list or string
        # target_gene_symbols and search_terms should be lists
        # email and user_agent should be strings
        if key in ["target_gene_symbols", "search_terms"]:
            # Split by spaces to create a list
            values = value_str.split()
            options[key] = values
        else:
            # Keep as a single string (don't split)
            options[key] = value_str
        
        with open(ACQUISITION_CONFIG_PATH, "w") as f:
            import yaml
            yaml.safe_dump(options, f)
            
        click.echo(f"Set configuration option `{key}` to `{value_str}`.")
    except Exception as e:
        raise e


@cli.command(name="query")
@click.argument("symbols", nargs=-1, metavar="SYMBOLS")
@click.option(
    "--search-terms",
    "-S",
    multiple=True,
    help="A search term or array of search terms by which to filter results."
)
@click.option(
    "--filters",
    "-F",
    multiple=True,
    help="An array of [KEY]:[VALUE] pairs to pass as parameters to the LOVD API call."
)
@click.option(
    "--out",
    "-o",
    help="The directory to which results are output."
)
@click.option(
    "--include-effect",
    "-E",
    is_flag=True,
    help="Includes variants' reported effects in results."
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enables verbose output."
)
@click.option(
    "--progressive",
    "-p",
    is_flag=True,
    help="Enables a progress bar indicator for the query."
)
def query(
    symbols: tuple[str],
    search_terms: tuple[str] | None,
    filters: tuple[str] | None,
    out: str | None,
    include_effect: bool | None,
    verbose: bool | None,
    progressive: bool | None
):
    """Query LOVD for the given gene symbol(s).

    Retrieves records for variants reported on the given gene symbols,
    according to the provided filters.

    """
    if progressive:
        client.with_progress()
    
    symbols = symbols or options["target_gene_symbols"]

    if verbose:
        click.echo("Getting variants reported on the following gene(s):")

    for s in symbols:
        if s in "email target_gene_symbols user_agent":
            raise click.BadArgumentUsage(
                "It looks like you're trying to get the current value of a\n"
                "configuration option, but you used `lovdtools get [KEY]`, which is\n"
                "for querying LOVD for variants on one or more gene symbols.\n"
                "\nInstead, you should use `lovdtools config get [KEY]`."
            )

        else:
            if verbose:
                click.echo(f"    o  {s}")

    try:
        variants = client.get_variants_for_genes(
            symbols,
            out or "./output",
            search_terms,
            include_effect or True,
            list({k:v for k, v in [f.split(sep=":") for f in filters]}),
        )
    except click.BadArgumentUsage as e:
        e("Improper argument usage.")
    except click.BadOptionUsage as e:
        e("Improper option usage.")
    except click.BadParameter as e:
        e("Bad parameter usage.")
    except Exception as e:
        e("LOVDTools encountered an unhandled exception. Double-check your inputs.")

    if verbose:
        click.echo("Requisition complete.")

    return variants

