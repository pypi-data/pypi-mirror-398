"""Projects module of official Python client for Driverless AI."""

from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence

from driverlessai import _commons
from driverlessai import _core
from driverlessai import _datasets
from driverlessai import _experiments
from driverlessai import _logging
from driverlessai import _utils


class Project(_commons.ServerObject):
    """A project in the Driverless AI server."""

    def __init__(self, client: "_core.Client", key: str) -> None:
        super().__init__(client=client, key=key)
        self._dataset_types = {
            "test_dataset": "Testing",
            "test_datasets": "Testing",
            "train_dataset": "Training",
            "train_datasets": "Training",
            "validation_dataset": "Validation",
            "validation_datasets": "Validation",
        }
        self._datasets: Optional[Dict[str, Sequence[_datasets.Dataset]]] = None
        self._experiments: Optional[_commons.ServerObjectList] = None

    def _update(self) -> None:
        self._set_raw_info(self._client._backend.get_project(key=self.key))
        self._set_name(self._get_raw_info().name)
        self._datasets = {
            "test_datasets": _commons.ServerObjectList(
                data=self._client._backend.get_datasets_for_project(
                    project_key=self.key,
                    dataset_type=self._dataset_types["test_dataset"],
                ),
                get_method=self._client.datasets.get,
                item_class_name=_datasets.Dataset.__name__,
            ),
            "train_datasets": _commons.ServerObjectList(
                data=self._client._backend.get_datasets_for_project(
                    project_key=self.key,
                    dataset_type=self._dataset_types["train_dataset"],
                ),
                get_method=self._client.datasets.get,
                item_class_name=_datasets.Dataset.__name__,
            ),
            "validation_datasets": _commons.ServerObjectList(
                data=self._client._backend.get_datasets_for_project(
                    project_key=self.key,
                    dataset_type=self._dataset_types["validation_dataset"],
                ),
                get_method=self._client.datasets.get,
                item_class_name=_datasets.Dataset.__name__,
            ),
        }
        self._experiments = _commons.ServerObjectList(
            data=[
                x.summary
                for x in self._client._backend.list_project_experiments(
                    project_key=self.key
                ).model_summaries
            ],
            get_method=self._client.experiments.get,
            item_class_name=_experiments.Experiment.__name__,
        )

    @property
    def datasets(self) -> Dict[str, Sequence[_datasets.Dataset]]:
        """Datasets linked to the project."""
        self._update()
        return self._datasets

    @property
    def description(self) -> Optional[str]:
        """Description of the project."""
        return self._get_raw_info().description or None

    @property
    def experiments(self) -> Sequence["_experiments.Experiment"]:
        """Experiments linked to the project."""
        self._update()
        return self._experiments

    @property
    def sharings(self) -> List[Dict[str, Optional[str]]]:
        """
        Users with whom the projects have
        been shared with when the H2O Storage is connected.
        """
        sharings = []
        for sharing in self._client._backend.list_project_sharings(project_id=self.key):
            username = _utils.get_storage_user_name(self._client, sharing.user_id)
            try:
                role = _utils.get_storage_role_name(
                    self._client, sharing.restriction_role_id
                )
            except RuntimeError:
                # Owner role is not listed
                role = None
            sharings.append({"username": username, "role": role})
        return sharings

    def delete(self, include_experiments: bool = False) -> None:
        """
        Permanently deletes the project from the Driverless AI server.

        Args:
            include_experiments: Unlink & delete experiments linked to the project.
        """
        if include_experiments:
            experiments = self.experiments

            for experiment in experiments:
                try:
                    self.unlink_experiment(experiment)
                except self._client._server_module.protocol.RemoteError as e:
                    _logging.logger.warning(
                        self._client._backend._format_server_error(
                            message=f"Cannot unlink experiment {experiment} "
                            f"from project {self.key}, {e.message['message']}"
                        )
                    )
                    continue

                try:
                    experiment.delete()
                except self._client._server_module.protocol.RemoteError as e:
                    _logging.logger.warning(
                        self._client._backend._format_server_error(
                            message=f"Unable to delete the experiment {experiment}. "
                            f"{e.message['message']}"
                        )
                    )
                    continue

        key = self.key
        self._client._backend.delete_project(key=key)
        _logging.logger.info(f"Driverless AI Server reported project {key} deleted.")

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the project details page in the Driverless AI server.

        Returns:
            URL to the project details page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}"
            f"project?projectKey={self.key}"
        )

    @_utils.min_supported_dai_version("1.11.0")
    def get_dataset_tags(self, dataset: "_datasets.Dataset") -> List[str]:
        """
        Returns the tags set for a particular dataset linked to the project.

        Args:
            dataset: A dataset linked to the project.

        Returns:
            Tags of the dataset.
        """
        dataset_summaries = self._client._backend.get_datasets_for_project(
            project_key=self.key, dataset_type="Training"
        )

        for dataset_summary in dataset_summaries:
            if dataset_summary.key == dataset.key:
                return dataset_summary.tags

        raise ValueError(f"Dataset {dataset} is not linked to the project.")

    def link_dataset(
        self,
        dataset: _datasets.Dataset,
        dataset_type: str,
        link_associated_experiments: bool = False,
    ) -> "Project":
        """
        Links a dataset to the project.

        Args:
            dataset: The dataset to be linked.
            dataset_type: Type of the dataset. Possible values are `train_dataset`,
                `validation_dataset`, or `test_dataset`.
            link_associated_experiments: Also link experiments that used the dataset.

        Returns:
            This project.
        """
        if self._client._server.version >= "1.10.6":
            self._client._backend.link_dataset_to_project_sync(
                project_key=self.key,
                dataset_key=dataset.key,
                dataset_type=self._dataset_types[dataset_type],
                link_dataset_experiments=link_associated_experiments,
            )
        else:
            self._client._backend.link_dataset_to_project(
                project_key=self.key,
                dataset_key=dataset.key,
                dataset_type=self._dataset_types[dataset_type],
                link_dataset_experiments=link_associated_experiments,
            )
        self._update()
        return self

    def link_experiment(self, experiment: "_experiments.Experiment") -> "Project":
        """
        Links an experiment to the project.

        Args:
            experiment: The experiment to link.

        Returns:
            This project.
        """
        if self._client._server.version >= "1.10.6.1":
            self._client._backend.link_experiment_to_project_sync(
                project_key=self.key, experiment_key=experiment.key
            )
        else:
            self._client._backend.link_experiment_to_project(
                project_key=self.key, experiment_key=experiment.key
            )
        self._update()
        return self

    def rename(self, name: str) -> "Project":
        """
        Changes the display name of the project.

        Args:
            name: New display name.

        Returns:
            This project.
        """
        self._client._backend.update_project_name(key=self.key, name=name)
        self._update()
        return self

    def redescribe(self, description: str) -> "Project":
        """
        Changes the description of the project.

        Args:
            description: New description.

        Returns:
            This project.
        """
        self._client._backend.update_project_description(
            key=self.key, description=description
        )
        self._update()
        return self

    def share(self, username: str, role: str = "Default") -> None:
        """
        Shares the project with a user when H2O Storage is connected.

        Args:
            username: Driverless AI username of user to share with.
            role: Role for the user. Possible values are `Default` or `Reader`.
        """
        self._client._backend.share_project(
            project_id=self.key,
            user_id=_utils.get_storage_user_id(self._client, username),
            restriction_role_id=_utils.get_storage_role_id(self._client, role),
        )

    def get_experiment_tags(self, experiment: "_experiments.Experiment") -> List[str]:
        """
        Returns the tags set for an experiment linked to the project.

        Args:
            experiment: An experiment linked to the project.

        Returns:
            Tags of the experiment.
        """

        experiment_list = self._client._backend.list_project_experiments(
            project_key=self.key
        ).model_summaries

        for experiment_data in experiment_list:
            if experiment_data.summary.key == experiment.key:
                return experiment_data.tags

        raise ValueError(f"Experiment {experiment} is not linked to the project.")

    def update_experiment_tags(
        self, experiment: "_experiments.Experiment", tags: List[str]
    ) -> None:
        """
        Updates tags from an experiment linked to the project.

        Args:
            experiment: experiment: An experiment linked to the project.
            tags: New tags.

        ??? Example
            Create a project, link an experiment, and remove all existing tags.

            ```py
            project = client.projects.create(
                name="test project",
                description="project description",
            )
            project.link_experiment(experiment)
            project.update_experiment_tags(experiment, [])
            ```
        """

        current_tags = self.get_experiment_tags(experiment)
        # Remove all existing tags
        for tag in current_tags:
            self._client._backend.untag_project_experiment(
                project_id=self.key, experiment_id=experiment.key, experiment_tag=tag
            )
        # Add new tags
        for tag in tags:
            self._client._backend.tag_project_experiment(
                project_id=self.key, experiment_id=experiment.key, experiment_tag=tag
            )

    def unlink_dataset(
        self, dataset: _datasets.Dataset, dataset_type: str
    ) -> "Project":
        """
        Unlinks a dataset from the project.

        Args:
            dataset: The dataset to be unlinked.
            dataset_type: Type of the dataset. Possible values are `train_dataset`,
                `validation_dataset`, or `test_dataset`.

        Returns:
            This project.
        """
        self._client._backend.unlink_dataset_from_project(
            project_key=self.key,
            dataset_key=dataset.key,
            dataset_type=self._dataset_types[dataset_type],
        )
        self._update()
        return self

    def unlink_experiment(self, experiment: "_experiments.Experiment") -> "Project":
        """
        Unlinks an experiment from the project.

        Args:
            experiment: The experiment to be unlinked.

        Returns:
            This project.
        """
        self._client._backend.unlink_experiment_from_project(
            project_key=self.key, experiment_key=experiment.key
        )
        self._update()
        return self

    def unshare(self, username: str) -> None:
        """
        Unshare the project when H2O Storage is connected.

        Args:
            username: Driverless AI username of user to unshare with.
        """
        for sharing in self._client._backend.list_project_sharings(project_id=self.key):
            if (
                username == _utils.get_storage_user_name(self._client, sharing.user_id)
                and sharing.restriction_role_id
            ):
                self._client._backend.unshare_project(
                    project_id=self.key, sharing_id=sharing.id
                )
                return
        raise RuntimeError(f"Project share with '{username}' not found.")

    @_utils.min_supported_dai_version("1.11.0")
    def update_dataset_tags(
        self, dataset: "_datasets.Dataset", tags: List[str]
    ) -> None:
        """
        Updates tags from a dataset linked to the project.

        Args:
            dataset: A dataset linked to the project.
            tags: New tags.

        ??? Example
            Create a project, link a dataset, and remove all existing tags.

            ```py
            project = client.projects.create(
                name="test project",
                description="project description",
            )
            project.link_dataset(dataset)
            project.update_dataset_tags(dataset, [])
            ```
        """

        current_tags = self.get_dataset_tags(dataset)
        # Remove all existing tags
        for tag in current_tags:
            self._client._backend.untag_project_dataset(
                project_id=self.key, dataset_id=dataset.key, dataset_tag=tag
            )
        # Add new tags
        for tag in tags:
            self._client._backend.tag_project_dataset(
                project_id=self.key, dataset_id=dataset.key, dataset_tag=tag
            )


class Projects:
    """
    Interact with
    [projects](https://docs.h2o.ai/driverless-ai/1-10-lts/docs/userguide/projects.html)
    in the Driverless AI server.
    """

    def __init__(self, client: "_core.Client"):
        self._client = client

    def create(
        self, name: str, description: Optional[str] = None, force: bool = False
    ) -> Project:
        """Creates a project in the Driverless AI server.

        Args:
            name: Display name for project.
            description: Description of project.
            force: Whether to create the project even when a project
                already exists with the same name.

        Returns:
            Created project.
        """
        if not force:
            _utils.error_if_project_exists(self._client, name)
        key = self._client._backend.create_project(name=name, description=description)
        return self.get(key)

    def get(self, key: str) -> Project:
        """
        Retrieves a project in the Driverless AI server.

        Args:
            key: The unique ID of the project.

        Returns:
            The project corresponding to the key.
        """
        return Project(self._client, key)

    def gui(self) -> _utils.Hyperlink:
        """
        Returns the full URL to the Projects page in the Driverless AI server.

        Returns:
            The full URL to the Projects page.
        """
        return _utils.Hyperlink(
            f"{self._client.server.address}{self._client._gui_sep}projects"
        )

    def list(self, start_index: int = 0, count: int = None) -> Sequence["Project"]:
        """
        Retrieves projects in the Driverless AI server.

        Args:
            start_index: The index of the first project to retrieve.
            count: The maximum number of projects to retrieve.
                If `None`, retrieves all available projects.

        Returns:
            Projects.
        """
        if count:
            data = self._client._backend.list_projects(
                offset=start_index, limit=count
            ).items
        else:
            page_size = 100
            page_position = start_index
            data = []
            while True:
                page = self._client._backend.list_projects(
                    offset=page_position, limit=page_size
                ).items
                data += page
                if len(page) < page_size:
                    break
                page_position += page_size
        return _commons.ServerObjectList(
            data=data, get_method=self.get, item_class_name=Project.__name__
        )

    @_utils.beta
    def get_by_name(self, name: str) -> Optional["Project"]:
        """
        Retrieves a project by its display name from the Driverless AI server.

        Args:
            name: Name of the project.

        Returns:
            The project with the specified name if it exists, otherwise `None`.
        """
        sort_query = self._client._server_module.messages.EntitySortQuery("", "", "")
        template = f'"name": "{name}"'
        data = self._client._backend.search_and_sort_projects(
            template, sort_query, False, 0, 1
        ).items
        if data:
            return Project(self._client, data[0].key)
        else:
            return None
