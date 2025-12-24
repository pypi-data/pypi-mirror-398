import click
from rich import print as rprint
import tabulate
import yaml

import anyscale
from anyscale.cli_logger import BlockLogger
from anyscale.commands import command_examples
from anyscale.commands.util import AnyscaleCommand
from anyscale.policy.models import PolicyBinding, PolicyConfig


log = BlockLogger()


@click.group("policy", help="Manage resource permission policies.")
def policy_cli() -> None:
    pass


@policy_cli.command(
    name="set", cls=AnyscaleCommand, example=command_examples.POLICY_SET_EXAMPLE,
)
@click.option(
    "--resource-type",
    required=True,
    type=click.Choice(["cloud", "project", "organization"], case_sensitive=False),
    help="Resource type ('cloud', 'project', or 'organization').",
)
@click.option(
    "--resource-id",
    required=True,
    type=str,
    help="Resource ID (e.g., cld_abc123, prj_xyz789, org_def456).",
)
@click.option(
    "-f",
    "--config-file",
    required=True,
    type=click.Path(exists=True),
    help="Path to a YAML config file with policy bindings.",
)
def set_policy(resource_type: str, resource_id: str, config_file: str,) -> None:
    """
    Set user group permission policy for a resource.

    The config file should be in YAML format with bindings list.

    Example policy.yaml:

    \b
    bindings:
      - role_name: collaborator
        principals:
          - ug_abc123
      - role_name: readonly
        principals:
          - ug_def456
          - ug_ghi789

    Valid role_name values:

    \b
      Cloud:        collaborator, readonly
      Project:      collaborator, readonly
      Organization: owner, collaborator
    """
    log.info(f"Setting policy for {resource_type} {resource_id}...")

    try:
        with open(config_file) as f:
            config_dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise click.ClickException(f"Failed to parse YAML file '{config_file}': {e}")

    if config_dict is None:
        raise click.ClickException(
            f"Invalid config file '{config_file}': file is empty."
        )
    if not isinstance(config_dict, dict):
        raise click.ClickException(
            f"Invalid config file '{config_file}': expected a YAML mapping with top-level 'bindings'."
        )

    try:
        bindings = [
            PolicyBinding(role_name=b["role_name"], principals=b["principals"],)
            for b in config_dict.get("bindings", [])
        ]
        config = PolicyConfig(bindings=bindings)
    except (KeyError, TypeError) as e:
        raise click.ClickException(f"Invalid config file format: {e}")

    try:
        anyscale.policy.set(
            resource_type=resource_type, resource_id=resource_id, config=config,
        )
    except ValueError as e:
        raise click.ClickException(f"Failed to set policy: {e}")

    log.info(f"Policy for {resource_type} {resource_id} has been updated.")


@policy_cli.command(
    name="get", cls=AnyscaleCommand, example=command_examples.POLICY_GET_EXAMPLE,
)
@click.option(
    "--resource-type",
    required=True,
    type=click.Choice(["cloud", "project", "organization"], case_sensitive=False),
    help="Resource type ('cloud', 'project', or 'organization').",
)
@click.option(
    "--resource-id",
    required=True,
    type=str,
    help="Resource ID (e.g., cld_abc123, prj_xyz789, org_def456).",
)
def get_policy(resource_type: str, resource_id: str,) -> None:
    """
    Get user group permission policy for a resource.
    """
    try:
        policy = anyscale.policy.get(
            resource_type=resource_type, resource_id=resource_id,
        )
    except ValueError as e:
        log.error(f"Failed to get policy: {e}")
        return

    if not policy.bindings:
        log.info(f"No policy bindings found for {resource_type} {resource_id}.")
        return

    status_str = policy.sync_status.value

    log.info(f"Policy for {resource_type} {resource_id}:")

    table_data = []
    for binding in policy.bindings:
        for principal in binding.principals:
            table_data.append((binding.role_name, principal, status_str))

    table = tabulate.tabulate(
        table_data, headers=["Role", "Principal (User Group ID)", "Process Status"],
    )
    rprint(table)


@policy_cli.command(
    name="list", cls=AnyscaleCommand, example=command_examples.POLICY_LIST_EXAMPLE,
)
@click.option(
    "--resource-type",
    required=True,
    type=click.Choice(["cloud", "project"], case_sensitive=False),
    help="Resource type to list policies for ('cloud' or 'project').",
)
def list_policies(resource_type: str,) -> None:
    """
    List permission policies for all resources of a specific type.

    Only shows resources that have bindings configured.
    """
    try:
        policies = anyscale.policy.list(resource_type=resource_type)
    except ValueError as e:
        log.error(f"Failed to list policies: {e}")
        return

    if not policies:
        log.info(f"No {resource_type}s found.")
        return

    # Filter to only show policies with bindings
    policies_with_bindings = [p for p in policies if p.bindings]

    if not policies_with_bindings:
        log.info(f"No bindings configured for any {resource_type}s.")
        return

    for policy in policies_with_bindings:
        log.info(f"\n{policy.resource_type}: {policy.resource_id}")

        status_str = policy.sync_status.value
        table_data = []
        for binding in policy.bindings:
            for principal in binding.principals:
                table_data.append((binding.role_name, principal, status_str))
        table = tabulate.tabulate(
            table_data, headers=["Role", "Principal (User Group ID)", "Process Status"],
        )
        rprint(table)
