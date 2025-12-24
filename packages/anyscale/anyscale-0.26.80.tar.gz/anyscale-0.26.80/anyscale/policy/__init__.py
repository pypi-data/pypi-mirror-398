from typing import List, Optional

from anyscale._private.anyscale_client import AnyscaleClientInterface
from anyscale._private.sdk import sdk_docs
from anyscale._private.sdk.base_sdk import Timer
from anyscale.cli_logger import BlockLogger
from anyscale.policy._private.policy_sdk import PrivatePolicySDK
from anyscale.policy.commands import (
    _GET_ARG_DOCSTRINGS,
    _GET_EXAMPLE,
    _LIST_ARG_DOCSTRINGS,
    _LIST_EXAMPLE,
    _SET_ARG_DOCSTRINGS,
    _SET_EXAMPLE,
    get,
    list,
    set,
)
from anyscale.policy.models import Policy, PolicyConfig, ResourcePolicy


class PolicySDK:
    def __init__(
        self,
        *,
        client: Optional[AnyscaleClientInterface] = None,
        logger: Optional[BlockLogger] = None,
        timer: Optional[Timer] = None,
    ):
        self._private_sdk = PrivatePolicySDK(client=client, logger=logger, timer=timer)

    @sdk_docs(
        doc_py_example=_SET_EXAMPLE, arg_docstrings=_SET_ARG_DOCSTRINGS,
    )
    def set(  # noqa: F811
        self, resource_type: str, resource_id: str, config: PolicyConfig,
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
        return self._private_sdk.set(
            resource_type=resource_type, resource_id=resource_id, config=config,
        )

    @sdk_docs(
        doc_py_example=_GET_EXAMPLE, arg_docstrings=_GET_ARG_DOCSTRINGS,
    )
    def get(self, resource_type: str, resource_id: str,) -> Policy:  # noqa: F811
        """Get user group permission policy for a resource.

        Returns a Policy object with role bindings.
        """
        return self._private_sdk.get(
            resource_type=resource_type, resource_id=resource_id,
        )

    @sdk_docs(
        doc_py_example=_LIST_EXAMPLE, arg_docstrings=_LIST_ARG_DOCSTRINGS,
    )
    def list(self, resource_type: str,) -> List[ResourcePolicy]:  # noqa: F811
        """List permission policies for all resources of a specific type.

        Returns a list of ResourcePolicy objects.
        """
        return self._private_sdk.list(resource_type=resource_type)
