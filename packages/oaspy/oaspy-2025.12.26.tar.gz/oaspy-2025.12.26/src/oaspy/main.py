# -*- coding: utf-8 -*-

import importlib.metadata

import click

from .converter import convert
from .insomnia import get_info as i_get_info
from .openapi import validate_export
from .utils import check_file, check_input, open_file
from .yaak import get_info as y_get_info


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    app_version = importlib.metadata.version("oaspy")
    click.echo(f"oaspy {app_version}")

    ctx.exit()


@click.group()
@click.option(
    "-v",
    "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=print_version,
    help="show current version and exit.",
)
# @click.pass_context
def command_line():
    """oaspy is a quick-and-dirty tool to generate
    an OpenApi 3.x specification from an insomnia
    V4/Yaak collections.
    """

    pass


@command_line.command()
@click.option("--file", "-f", required=True, help="file to import.")
@click.option(
    "--schema",
    "-s",
    default="v30",
    required=False,
    help="OpenApi definition to be generated [v30|v31]",
)
@click.option("--output", "-o", help="file name to save.")
@click.option("--order_folder", "-o_f", is_flag=True, default=False, help="order folders.")
@click.option("--order_request", "-o_r", is_flag=True, default=False, help="order request.")
def gen(file, schema, output, order_folder, order_request):
    """Generate an OpenApi 3.x file, from an
    allowed collection.
    """

    if check_file(file):
        json_data = open_file(file)

        if json_data is None:
            print("oaspy info: the contents of the file could not be read")
        else:
            result = check_input(json_data)

            if result is None:
                print("oaspy info: collection could not be read")
                return

            if result in ["inso", "yaak"]:
                convert(file, schema, output, order_folder, order_request, result)
            else:
                print("oaspy info: cannot be determined, the collection type")
    else:
        print(f"oaspy info: No such file '{file}'...")
        print("exiting...")
        click.echo()


@command_line.command()
@click.option("--file", "-f", required=True, help="openApi file to check")
def check(file):
    """Validates the structure of an OpenApi file."""

    if check_file(file):
        json_data = open_file(file)

        if json_data is None:
            print("oaspy check: the contents of the file could not be read")
        else:
            validate_export(json_data)
    else:
        print(f"oaspy check: No such file '{file}'...")

    click.echo()
    print("exiting...")


@command_line.command()
@click.option("--file", "-f", required=True, help="Collection file to check")
def info(file):
    """Shows information from an allowed collection."""

    if check_file(file):
        json_data = open_file(file)

        if json_data is None:
            print("oaspy info: the contents of the file could not be read")
        else:
            result = check_input(json_data)

            if result is None:
                print("oaspy info: collection could not be read")
                return

            if result == "inso":
                i_get_info(json_data)
            elif result == "yaak":
                y_get_info(json_data)
            else:
                print("oaspy info: cannot be determined, the collection type")

    else:
        print(f"oaspy info: No such file '{file}'...")

    click.echo()
    print("exiting...")


if __name__ == "__main__":
    command_line()
