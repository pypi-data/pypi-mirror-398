# Contains non-generated classes representing DB entity references.
import abc


class EntityReference(abc.ABC):
    """Common ancestor of different kinds of DB entity references.

    The display_name field filled in when entities are returned by the API.
    It is ignored on any entity mutating API calls. Use explicit API endpoints
    to modify entity names, where supported.
    """

    def __init__(self, key, display_name=""):
        self.key = key
        self.display_name = display_name

    @abc.abstractmethod
    def clone(self):
        pass

    @abc.abstractmethod
    def kind(self):
        pass

    def dump(self):
        d = {k: v for k, v in vars(self).items()}
        return d


class ModelReference(EntityReference):
    """Represents a reference to a model entity."""

    def clone(self):
        return ModelReference(self.key, self.display_name)

    def kind(self):
        return "model"

    @staticmethod
    def load(d: dict):
        return ModelReference(**d)


class DatasetReference(EntityReference):
    """Represents a reference to a dataset entity."""

    def clone(self):
        return DatasetReference(self.key, self.display_name)

    def kind(self):
        return "dataset"

    @staticmethod
    def load(d: dict):
        return DatasetReference(**d)
