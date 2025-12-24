from typing import List, Optional

from anyscale._private.sdk import sdk_command
from anyscale.policy._private.policy_sdk import PrivatePolicySDK
from anyscale.policy.models import Policy, PolicyConfig, ResourcePolicy


_POLICY_SDK_SINGLETON_KEY = "policy_sdk"

_SET_EXAMPLE = """
import anyscale
from anyscale.policy.models import PolicyConfig, PolicyBinding

policy_config = PolicyConfig(
    bindings=[
        PolicyBinding(role_name="collaborator", principals=["ug_abc123"]),
        PolicyBinding(role_name="readonly", principals=["ug_def456", "ug_ghi789"]),
    ]
)
anyscale.policy.set(
    resource_type="cloud",
    resource_id="cld_abc123",
    config=policy_config,
)
"""

_SET_ARG_DOCSTRINGS = {
    "resource_type": "Resource type ('cloud', 'project', or 'organization').",
    "resource_id": "Resource ID (e.g., cld_abc123, prj_xyz789, org_def456).",
    "config": "Policy configuration with role bindings.",
}

_GET_EXAMPLE = """
import anyscale
from anyscale.policy.models import Policy

policy = anyscale.policy.get(resource_type="cloud", resource_id="cld_abc123")
for binding in policy.bindings:
    print(f"{binding.role_name}: {binding.principals}")
"""

_GET_ARG_DOCSTRINGS = {
    "resource_type": "Resource type ('cloud', 'project', or 'organization').",
    "resource_id": "Resource ID (e.g., cld_abc123, prj_xyz789, org_def456).",
}

_LIST_EXAMPLE = """
import anyscale
from anyscale.policy.models import ResourcePolicy

policies = anyscale.policy.list(resource_type="cloud")
for policy in policies:
    print(f"{policy.resource_id}: {policy.bindings}")
"""

_LIST_ARG_DOCSTRINGS = {
    "resource_type": "Resource type to list policies for ('cloud' or 'project').",
}


@sdk_command(
    _POLICY_SDK_SINGLETON_KEY,
    PrivatePolicySDK,
    doc_py_example=_SET_EXAMPLE,
    arg_docstrings=_SET_ARG_DOCSTRINGS,
)
def set(  # noqa: A001
    resource_type: str,
    resource_id: str,
    config: PolicyConfig,
    *,
    _private_sdk: Optional[PrivatePolicySDK] = None
):
    """Set user group permission policy for a resource.

    Valid role_name values by resource type:

    **Cloud**:
    - `collaborator`: Read/write access (create, read, update, delete)
    - `readonly`: Read-only access

    **Project**:
    - `collaborator`: Read/write access (create, read, update)
    - `readonly`: Read-only access

    **Organization**:
    - `owner`: Full control (write + collaborator management)
    - `collaborator`: Read/write access to organization resources
    """
    return _private_sdk.set(  # type: ignore
        resource_type=resource_type, resource_id=resource_id, config=config,
    )


@sdk_command(
    _POLICY_SDK_SINGLETON_KEY,
    PrivatePolicySDK,
    doc_py_example=_GET_EXAMPLE,
    arg_docstrings=_GET_ARG_DOCSTRINGS,
)
def get(
    resource_type: str,
    resource_id: str,
    *,
    _private_sdk: Optional[PrivatePolicySDK] = None
) -> Policy:
    """Get user group permission policy for a resource.

    Returns a Policy object with role bindings.
    """
    return _private_sdk.get(  # type: ignore
        resource_type=resource_type, resource_id=resource_id,
    )


@sdk_command(
    _POLICY_SDK_SINGLETON_KEY,
    PrivatePolicySDK,
    doc_py_example=_LIST_EXAMPLE,
    arg_docstrings=_LIST_ARG_DOCSTRINGS,
)
def list(  # noqa: A001
    resource_type: str, *, _private_sdk: Optional[PrivatePolicySDK] = None
) -> List[ResourcePolicy]:
    """List permission policies for all resources of a specific type.

    Returns a list of ResourcePolicy objects.
    """
    return _private_sdk.list(resource_type=resource_type)  # type: ignore
