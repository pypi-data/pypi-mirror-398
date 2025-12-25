import abc
import dataclasses
from typing import Any, List, Optional, Sequence, TYPE_CHECKING

from driverlessai import _commons, _core, _experiments, _utils

if TYPE_CHECKING:
    import fsspec  # noqa F401


class Deployment(_commons.ServerObject, abc.ABC):
    """A deployment in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)


class TritonDeployment(Deployment):
    """
    A deployment in an
    [NVIDIA Triton inference server](https://github.com/triton-inference-server/server)
    in the Driverless AI server.
    """

    def __init__(
        self, client: "_core.Client", key: str, is_local: bool, raw_info: Optional[Any]
    ) -> None:
        super().__init__(client=client, key=key)
        self._is_local = is_local
        self._set_raw_info(raw_info)

    @property
    def is_local_deployment(self) -> bool:
        """
        Whether the Triton deployment is in the built-in (local) Triton server
        in the Driverless AI server or in a remote Triton server.
        """
        return self._is_local

    @property
    def state(self) -> str:
        """Current state of the Triton deployment."""
        self._update()  # The state might have changed, so fetch again.
        return self._get_raw_info().state

    @property
    @_utils.beta
    def triton_model(self) -> "TritonModel":
        """Triton model created by the Triton deployment."""
        raw_info = self._get_raw_info()
        return TritonModel(
            raw_info.inputs,
            raw_info.model_desc,
            raw_info.outputs,
            raw_info.platform,
            raw_info.versions,
        )

    @property
    def triton_server_hostname(self) -> str:
        """Hostname of the Triton server in which the Triton deployment occurred."""
        return self._get_raw_info().host

    def _update(self) -> None:
        self._set_raw_info(
            self._client._backend.get_triton_model(
                local=self.is_local_deployment, key=self.key
            )
        )
        self._set_name(self._get_raw_info().model_desc)

    @_utils.beta
    def delete(self) -> None:
        """Permanently deletes the Triton deployment from the Driverless AI server."""
        if not self.is_local_deployment:
            raise Exception("Cannot delete a remote Triton deployment.")
        self.unload()
        self._client._backend.delete_triton_model(
            experiment_key=self.key,
            local=self.is_local_deployment,
        )

    @_utils.beta
    def load(self) -> None:
        """Load the Triton deployment."""
        self._client._backend.load_triton_model(
            experiment_key=self.key,
            local=self.is_local_deployment,
            config_json=None,
            files=None,
        )
        self._update()

    @_utils.beta
    def unload(self) -> None:
        """Unload the Triton deployment."""
        self._client._backend.unload_triton_model(
            experiment_key=self.key,
            local=self.is_local_deployment,
        )
        self._update()


class Deployments:
    """
    Interact with
    [deployments](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/deployment.html)
    in the Driverless AI server.
    """

    def __init__(self, client: "_core.Client") -> None:
        self._client = client

    def _deploy_to_triton(
        self,
        to_local: bool,
        experiment: _experiments.Experiment,
        deploy_predictions: bool = True,
        deploy_shapley: bool = False,
        deploy_original_shapley: bool = False,
        enable_high_concurrency: bool = False,
    ) -> TritonDeployment:
        key = self._client._backend.deploy_model_to_triton(
            experiment_key=experiment.key,
            local=to_local,
            deploy_preds=deploy_predictions,
            deploy_pred_contribs=deploy_shapley,
            deploy_pred_contribs_orig=deploy_original_shapley,
            dest_dir=None,
            high_concurrency=enable_high_concurrency,
        )
        return TritonDeployment(self._client, key, to_local, None)

    def _get_triton_deployment(self, in_local: bool, key: str) -> TritonDeployment:
        all_deployments = self._list_triton_deployments(in_local)
        deployments = [d for d in all_deployments if d.key == key]
        triton_server_type = "local" if in_local else "remote"
        if len(deployments) == 0:
            raise ValueError(
                f"Triton deployment '{key}' cannot be found "
                f"in the {triton_server_type} Triton server."
            )
        if len(deployments) > 1:
            raise Exception(
                f"Found {len(deployments)} Triton deployments "
                f"with the same key '{key}' in the {triton_server_type} Triton server."
            )
        return deployments[0]

    def _list_triton_deployments(
        self, in_local: bool, start_index: int = 0, count: int = None
    ) -> List["TritonDeployment"]:
        if count:
            data = self._client._backend.list_triton_models(
                local=in_local, offset=start_index, limit=count
            ).items
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.list_triton_models(
                    in_local, offset=page_position, limit=page_size
                ).items
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return [TritonDeployment(self._client, d.model_name, in_local, d) for d in data]

    @_utils.beta
    def deploy_to_triton_in_local(
        self,
        experiment: _experiments.Experiment,
        deploy_predictions: bool = True,
        deploy_shapley: bool = False,
        deploy_original_shapley: bool = False,
        enable_high_concurrency: bool = False,
    ) -> TritonDeployment:
        """
        Deploys the model created from an experiment to the local Triton server
        in the Driverless AI server.

        Args:
            experiment: Experiment model.
            deploy_predictions: Whether to deploy model predictions or not.
            deploy_shapley: Whether to deploy model Shapley or not.
            deploy_original_shapley: Whether to deploy model original Shapley or not.
            enable_high_concurrency: Whether to enable handling several requests at once

        Returns:
            Deployed Triton deployment.

        ??? warning "Removed in Driverless AI v1.11.0"
            Local Triton deployments are no longer supported
            from H2O Driverless AI v1.11.0 onwards.
        """

        if self._client.server.version >= "1.11.0":
            raise Exception(
                "Local Triton deployments are no longer "
                "supported from H2O Driverless AI v1.11.0 onwards."
            )

        return self._deploy_to_triton(
            True,
            experiment,
            deploy_predictions,
            deploy_shapley,
            deploy_original_shapley,
            enable_high_concurrency,
        )

    @_utils.beta
    def deploy_to_triton_in_remote(
        self,
        experiment: _experiments.Experiment,
        deploy_predictions: bool = True,
        deploy_shapley: bool = False,
        deploy_original_shapley: bool = False,
        enable_high_concurrency: bool = False,
    ) -> TritonDeployment:
        """
        Deploys the model created from an experiment to a remote Triton server
        configured in the Driverless AI server.

        Args:
            experiment: Experiment model.
            deploy_predictions: Whether to deploy model predictions or not.
            deploy_shapley: Whether to deploy model Shapley or not.
            deploy_original_shapley: Whether to deploy model original Shapley or not.
            enable_high_concurrency: Whether to enable handling several requests at once

        Returns:
            Deployed Triton deployment.
        """
        return self._deploy_to_triton(
            False,
            experiment,
            deploy_predictions,
            deploy_shapley,
            deploy_original_shapley,
            enable_high_concurrency,
        )

    def get_from_triton_in_local(self, key: str) -> TritonDeployment:
        """
        Retrieves a Triton deployment, deployed in the local Triton
        server configured in the Driverless AI server.

        Args:
            key: The unique ID of the Triton deployment.

        Returns:
            The Triton deployment corresponding to the key.

        ??? warning "Removed in Driverless AI v1.11.0"
            Local Triton deployments are no longer
            supported from H2O Driverless AI v1.11.0 onwards.
        """
        if self._client.server.version >= "1.11.0":
            raise Exception(
                "Local Triton deployments are no "
                "longer supported from H2O Driverless AI v1.11.0 onwards."
            )

        return self._get_triton_deployment(True, key)

    def get_from_triton_in_remote(self, key: str) -> TritonDeployment:
        """
        Retrieves a Triton deployment, deployed in a remote Triton
        server configured in the Driverless AI server.

        Args:
            key: The unique ID of the Triton deployment.

        Returns:
            The Triton deployment corresponding to the key.
        """
        return self._get_triton_deployment(False, key)

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the Deployments page in the Driverless AI server.

        Returns:
            The full URL to the Deployments page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}deployments"
        )

    @_utils.beta
    def list_triton_deployments(
        self, start_index: int = 0, count: int = None
    ) -> Sequence["TritonDeployment"]:
        """
        Retrieves Triton deployments in the Driverless AI server.

        Args:
            start_index: The index of the first Triton deployment to retrieve.
            count: The maximum number of Triton deployments to retrieve.
                If `None`, retrieves all available Triton deployments.

        Returns:
            Triton deployments.
        """
        local = []
        if self._client.server.version < "1.11.0":
            local = self._list_triton_deployments(True, start_index, count)
        remote = self._list_triton_deployments(False, start_index, count)
        return local + remote


@dataclasses.dataclass(frozen=True)
class TritonModel:
    """A Triton model created by a Triton deployment."""

    inputs: List[str]
    """Inputs of the Triton model."""
    name: str
    """Name of the Triton model."""
    outputs: List[str]
    """Outputs of the Triton model."""
    platform: str
    """Supported platform of the Triton model."""
    versions: List[str]
    """Versions of the Triton model."""
