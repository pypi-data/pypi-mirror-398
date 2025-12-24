import click
from rich import print as rprint
import tabulate

import anyscale
from anyscale.cli_logger import BlockLogger
from anyscale.commands import command_examples
from anyscale.commands.util import AnyscaleCommand


log = BlockLogger()


@click.group("user-group", help="Manage user groups.")
def user_group_cli() -> None:
    pass


@user_group_cli.command(
    name="list", cls=AnyscaleCommand, example=command_examples.USER_GROUP_LIST_EXAMPLE,
)
@click.option(
    "--max-items",
    default=50,
    type=int,
    help="Maximum number of user groups to return.",
)
def list_user_groups(max_items: int) -> None:
    """
    List user groups in the organization.
    """
    try:
        user_groups = anyscale.user_group.list(max_items=max_items)
    except ValueError as e:
        log.error(str(e))
        return

    if not user_groups:
        log.info("No user groups found.")
        return

    table = tabulate.tabulate(
        [(ug.id, ug.name) for ug in user_groups], headers=["ID", "Name"],
    )
    rprint(table)


@user_group_cli.command(
    name="get", cls=AnyscaleCommand, example=command_examples.USER_GROUP_GET_EXAMPLE,
)
@click.option(
    "--id", required=True, type=str, help="The ID of the user group to retrieve.",
)
def get_user_group(id: str) -> None:  # noqa: A002
    """
    Get a specific user group by ID.
    """
    try:
        user_group = anyscale.user_group.get(id=id)
    except ValueError as e:
        log.error(f"Failed to get user group: {e}")
        return

    details = [
        ("ID", user_group.id),
        ("Name", user_group.name),
        ("Organization ID", user_group.org_id),
        ("Created At", user_group.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Updated At", user_group.updated_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
    ]
    table = tabulate.tabulate(details, tablefmt="plain")
    rprint(table)
