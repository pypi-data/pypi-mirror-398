import json
import logging
import os
import sys
from email.policy import default
from importlib.metadata import entry_points
from pathlib import Path

import click

from treqs import __package_name__
from treqs.check_elements import check_elements
from treqs.create_elements import create_elements
from treqs.extension_loader import load_resolver_callback
from treqs.list_elements import (
    list_elements,
    list_elements_md_tab_strat,
    list_elements_plantuml_strat,
)
from treqs.process_elements import process_elements


@click.group()
@click.version_option(package_name=__package_name__)
def treqs():
    logger = logging.getLogger("treqs-on-git.treqs-ng")
    # We use level 10 for debug, level 20 for verbose, level 30+ for important
    # This corresponds to
    # DEBUG=10, INFO=20, WARNING=30,
    # but with different semantics
    logger.setLevel(10)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


@click.command(help="List treqs elements in this folder")
@click.option("--type", help="Limit action to specified treqs element type")
@click.option("--uid", help="Limit action to treqs element with specified id")
@click.option(
    "--attribute",
    type=str,
    multiple=True,
    help="Filter elements based on attributes, e.g., --attribute asil=1",
)
@click.option(
    "--outlinks/--no-outlinks",
    default=False,
    help="Print outgoing tracelinks",
    show_default=True,
)
@click.option(
    "--inlinks/--no-inlinks",
    default=False,
    help="Print incoming tracelinks",
    show_default=True,
)
@click.option(
    "--followlinks",
    type=bool,
    default=False,
    help="List treqs elements recursively by following links (plantuml only)",
)
@click.option(
    "--verbose/--no-verbose",
    type=bool,
    default=False,
    help="Print verbose output instead of only important messages.",
    show_default=True,
)
@click.option(
    "--plantuml/--no-plantuml",
    type=bool,
    default=False,
    help="Generate a PlantUML diagram from the treqs elements",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Choose output mode: table or json for API use.",
)
@click.option(
    "--recursive",
    type=bool,
    default=True,
    help="List treqs elements recursively in all subfolders.",
)
@click.argument("filename", nargs=-1)
def list(
    filename,
    type,
    recursive,
    uid,
    outlinks,
    inlinks,
    followlinks,
    verbose,
    plantuml,
    attribute,
    output,
):
    setVerbosity(verbose)
    attributes = parse_attributes(attribute) if attribute else None

    # Load resolver from extensions
    resolver_callback = load_resolver_callback()

    if plantuml:
        listelementsstrategy = list_elements_plantuml_strat()
    else:
        listelementsstrategy = list_elements_md_tab_strat()

    le = list_elements(listelementsstrategy, resolver_callback)
    result = le.list_elements(
        filename=filename,
        treqs_type=type,
        outlinks=outlinks,
        inlinks=inlinks,
        recursive=recursive,
        uid=uid,
        followlinks=followlinks,
        attributes=attributes,
        output=output,
    )

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        # click.echo(result)
        click.echo()
        sys.exit(result)


@click.command(
    help="Creates a treqs element and prints it on the command line.",
)
@click.option(
    "--type",
    type=str,
    default="undefined",
    help="The treqs element type that the new element should have. "
    "If available, treqs will select a template for this type.",
)
@click.option(
    "--label",
    type=str,
    default="",
    help="Short text describing treqs element. Markdown headings ok.",
)
@click.option(
    "--amount",
    type=int,
    default=1,
    help="How many times to create the element using the given template.",
)
@click.option(
    "--templatefolder",
    type=click.Path(exists=True),
    default=Path(__file__).parent / "../templates",
    help="Location where the templates are stored. "
    "Default location is the template folder in the treqs homefolder. "
    "A path to any folder can be given here and it is recommended to "
    "maintain a template folder for each project in which treqs is used. "
    "In that case, consider a template folder in your local repository, "
    "e.g. as sub-folder of requirements.",
)
@click.option(
    "--template",
    is_flag=False,
    default="treqs_element",
    help="A .md file that contains a template for specifying a requirement. "
    "This allows to choose a template independent from type.",
)
@click.option(
    "--verbose",
    type=bool,
    default=False,
    help="Print verbose output instead of only the most important messages.",
)
@click.option(
    "--interactive/--non-interactive",
    default=False,
    help="Choose between an interactive or a non-interactive interface.",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Choose output mode: table or json for API use.",
)
def create(
    type,
    amount,
    verbose,
    templatefolder,
    template,
    label,
    interactive,
    output,
):
    setVerbosity(verbose)

    if interactive:
        if type == "undefined":
            type = click.prompt(
                "Which type should the element have?",
                type=str,
                default="undefined",
            )
        if label == "":
            label = click.prompt(
                "Enter the label for the element",
                type=str,
                default="",
            )

    path = Path(os.path.join(templatefolder, type + ".md")).exists()
    path2 = Path(os.path.join(templatefolder, template + ".md")).exists()

    results = []

    if path is True:
        for _ in range(amount):
            result = create_elements.create_markdown_element(
                type,
                templatefolder,
                label,
            )
            results.append(result)
    elif path is False and path2 is True:
        for _ in range(amount):
            result = create_elements.create_markdown_new_template(
                type,
                templatefolder,
                template,
                label,
            )
            results.append(result)
        if interactive or (not interactive and type != "undefined"):
            results.append(
                "Template not found for this type. "
                "Output generated with default template. "
                "Refer to treqs create --help."
            )
    else:
        results.append("No matching template found")

    if output == "json":
        click.echo(json.dumps({"elements": results}, indent=2))
    else:
        for r in results:
            click.echo(r)


@click.command(help="Creates a link to a treqs element.")
@click.option(
    "--linktype",
    prompt="Which type should the link have?",
    default="relatesto",
    help="The treqs link type, specifying the type of relationship to target.",
)
@click.option(
    "--target",
    prompt="What UID does the target treqs element have?",
    default="UID missing",
    help="Use treqs list to find the right UID.",
)
@click.option(
    "--verbose/--no-verbose",
    type=bool,
    default=False,
    help="Print verbose output instead of only the most important messages.",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Choose output mode: table or json for API use.",
)
def createlink(linktype, target, verbose, output):
    setVerbosity(verbose)
    result = create_elements.create_link(linktype, target)

    if output == "json":
        click.echo(json.dumps({"link": result}, indent=2))
    else:
        click.echo(result)


@click.command(help="Checks for consistency of treqs elements.")
@click.option(
    "--recursive",
    type=bool,
    default=True,
    help="Check treqs elements recursively in all subfolders.",
)
@click.option(
    "--ttim",
    default="./ttim.yaml",
    help="Path to a TTIM (type & traceability info model) in json format.",
)
@click.option(
    "--verbose/--no-verbose",
    type=bool,
    default=False,
    help="Print verbose output instead of only the most important messages.",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Choose output mode: table or json for API use.",
)
# , help='Give a file or directory to list from.')
@click.argument("filename", nargs=-1)
def check(recursive, filename, ttim, verbose, output):
    setVerbosity(verbose)
    ce = check_elements(output=output, verbose=verbose)
    result = ce.check_elements(filename, recursive, ttim)

    if output == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        sys.exit(result)


# TODO GL: Imho too many options here. Confusing. Address in the future
# by having a single strategy
# attribute with different string options?
@click.command(
    help="Process a treqs file by generating content in protected areas.",
)
@click.option(
    "--recursive",
    type=bool,
    default=True,
    help="Process all subfolder recursively.",
    show_default=True,
)
@click.option(
    "--web/--no-web",
    default=False,
    help="Generate PlantUML images via web service (Treqs extensions only).",
    show_default=True,
)
@click.option(
    "--links/--no-links",
    default=False,
    help="Generate diagram URLs from a file (Treqs extensions only).",
    show_default=True,
)
@click.option(
    "--html",
    type=str,
    metavar="",
    default=False,
    is_flag=True,
    help="Generate HTML with traceable diagrams (only with Treqs extensions).",
    show_default=False,
)
@click.option(
    "--svg",
    type=str,
    metavar="",
    default=False,
    is_flag=True,
    help="Generate SVG diagrams instead of PNGs (Treqs extensions only).",
    show_default=False,
)
@click.option(
    "--verbose/--no-verbose",
    type=bool,
    default=False,
    help="Print verbose output instead of only the most important messages.",
    show_default=True,
)
@click.argument("filename")
def process(filename, recursive, web, html, svg, links, verbose):
    setVerbosity(verbose)
    pe = process_elements()
    pe.process_elements(filename, recursive, web, html, svg, links)


@click.command(help="Generate a new id used for treqs element.")
@click.option(
    "--amount",
    help="Specify amount of generated ids",
    type=int,
    default=1,
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Choose output mode: table or json for API use.",
)
def generateid(amount, output):
    result = create_elements.generate_id(amount)

    if output == "json":
        ids = result.splitlines()
        click.echo(json.dumps({"ids": ids}, indent=2))
    else:
        click.echo(result)


treqs.add_command(create)
treqs.add_command(list)
treqs.add_command(check)
treqs.add_command(createlink)
treqs.add_command(generateid)
treqs.add_command(process)

eps = entry_points()

if type(eps) is dict:
    # python 3.9 and earlier, eps would be a dictionary
    discovered_plugins = eps.get("treqs.plugins", [])
else:
    # new python versions will give an EntryPoints object
    discovered_plugins = eps.select(group="treqs.plugins")
for plugin in discovered_plugins:
    cmd = plugin.load()
    treqs.add_command(cmd)


def setVerbosity(verbose):
    if verbose:
        logging.getLogger("treqs-on-git.treqs-ng").setLevel(10)
    else:
        logging.getLogger("treqs-on-git.treqs-ng").setLevel(20)


def parse_attributes(attribute):
    attributes = {}
    for at in attribute:
        m = f"Invalid attribute format: '{at}'. Must be in 'key=value' format."
        if "=" not in at:
            raise click.BadParameter(m)
        key, value = at.split("=")
        attributes[key] = value
    return attributes


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, format="%(message)s")
    treqs()
