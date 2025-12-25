# -----------------------------------------------------------------------
#             *** WARNING: DO NOT MODIFY THIS FILE ***
#
#         Instead, modify h2oai/service.proto and run "make proto".
# -----------------------------------------------------------------------

from typing import List, Any

from . import validation
from .references import *

class Meta:
    """
    This entity is used for creating Meta information table in ORM mode
    Fields like ID, Key and Creation time are added automatically

    """
    def __init__(self, value, *, validate_toml=False) -> None:
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Meta':
        return Meta(self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Meta':
        return Meta(**d, validate_toml=validate_toml)


class User:
    """
    This entity is used for creating Users table in ORM mode

    """
    def __init__(self, directory, config, *, validate_toml=False) -> None:
        self.directory = directory
        self.config = config
        if validate_toml:
            validation.validate_toml(config, 'config')

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'User':
        return User(self.directory, self.config)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'User':
        return User(**d, validate_toml=validate_toml)


class EchoStatus:
    """

    """
    def __init__(self, progress, message, *, validate_toml=False) -> None:
        self.progress = progress
        self.message = message

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'EchoStatus':
        return EchoStatus(self.progress, self.message)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'EchoStatus':
        return EchoStatus(**d, validate_toml=validate_toml)


class License:
    """
    Represents a license key.

    :param is_valid: Is this license valid?
    :param message: License message.
    :param days_left: Days left before license expires.
    :param plaintext_key: License key.
    :param save_succeeded: Whether the license was applied successfully.
    :param organization: Organization that obtained the license
    :param serial_number: Serial number of the license
    :param license_type: License type ("developer", "trial", "academic", "pilot", "production", "cloud").
    """
    def __init__(self, is_valid, message, days_left, plaintext_key, save_succeeded, organization, serial_number, license_type, *, validate_toml=False) -> None:
        self.is_valid = is_valid
        self.message = message
        self.days_left = days_left
        self.plaintext_key = plaintext_key
        self.save_succeeded = save_succeeded
        self.organization = organization
        self.serial_number = serial_number
        self.license_type = license_type

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'License':
        return License(self.is_valid, self.message, self.days_left, self.plaintext_key, self.save_succeeded, self.organization, self.serial_number, self.license_type)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'License':
        return License(**d, validate_toml=validate_toml)


class AppVersion:
    """
    The application version

    :param arch: Machine's architecture type.
    :param base_version: The application base version.
    :param version: The application version (semver).
    :param build: The application build number.
    :param license: The license associated with this instance.
    :param config: List of expert configurable options for experiments
    :param mliConfig: List of configurable options for MLI
    :param enable_storage: Whether GUI should have H2O remote storage capabilities (https://github.com/h2oai/h2oai-storage) for dataset import/export
    :param enable_storage_projects: Whether GUI uses remote projects loaded from H2O Storage
    """
    def __init__(self, arch, base_version, version, build, license, config, mliConfig, enable_storage, enable_storage_projects, *, validate_toml=False) -> None:
        self.arch = arch
        self.base_version = base_version
        self.version = version
        self.build = build
        self.license = license
        self.config = config
        self.mliConfig = mliConfig
        self.enable_storage = enable_storage
        self.enable_storage_projects = enable_storage_projects

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['license'] = self.license.dump()
        d['config'] = [a.dump() for a in self.config]
        d['mliConfig'] = [a.dump() for a in self.mliConfig]
        return d

    def clone(self) -> 'AppVersion':
        return AppVersion(self.arch, self.base_version, self.version, self.build, self.license, self.config, self.mliConfig, self.enable_storage, self.enable_storage_projects)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AppVersion':
        d['license'] = License.load(d['license'])
        d['config'] = [ConfigItem.load(a) for a in d['config']]
        d['mliConfig'] = [ConfigItem.load(a) for a in d['mliConfig']]
        return AppVersion(**d, validate_toml=validate_toml)


class ExportExperimentJob:
    """

    """
    def __init__(self, progress, status, error, message, experiment_zip_path, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.experiment_zip_path = experiment_zip_path
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExportExperimentJob':
        return ExportExperimentJob(self.progress, self.status, self.error, self.message, self.experiment_zip_path, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExportExperimentJob':
        return ExportExperimentJob(**d, validate_toml=validate_toml)


class ConfigMigrationDefinition:
    """

    """
    def __init__(self, config_name, original_value, new_value, *, validate_toml=False) -> None:
        self.config_name = config_name
        self.original_value = original_value
        self.new_value = new_value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ConfigMigrationDefinition':
        return ConfigMigrationDefinition(self.config_name, self.original_value, self.new_value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ConfigMigrationDefinition':
        return ConfigMigrationDefinition(**d, validate_toml=validate_toml)


class ListInterpretationQueryResponse:
    """

    """
    def __init__(self, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['items'] = [a.dump() for a in self.items]
        return d

    def clone(self) -> 'ListInterpretationQueryResponse':
        return ListInterpretationQueryResponse(self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListInterpretationQueryResponse':
        d['items'] = [InterpretSummary.load(a) for a in d['items']]
        return ListInterpretationQueryResponse(**d, validate_toml=validate_toml)


class ListVisualizationQueryResponse:
    """

    """
    def __init__(self, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['items'] = [a.dump() for a in self.items]
        return d

    def clone(self) -> 'ListVisualizationQueryResponse':
        return ListVisualizationQueryResponse(self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListVisualizationQueryResponse':
        d['items'] = [AutoVizSummary.load(a) for a in d['items']]
        return ListVisualizationQueryResponse(**d, validate_toml=validate_toml)


class JobStatus:
    """
    Generic job status object. It is meant to represent status of an async job, either directly for async jobs with
    no response payload or to be embedded in other jobs along with their normal response payload.

    """
    def __init__(self, progress, status, error, message, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'JobStatus':
        return JobStatus(self.progress, self.status, self.error, self.message, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'JobStatus':
        return JobStatus(**d, validate_toml=validate_toml)


class OAuth2ClientTokens:
    """

    """
    def __init__(self, status, access_token, refresh_token, client_id, error, token_endpoint_url, token_introspection_url, *, validate_toml=False) -> None:
        self.status = status
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.error = error
        self.token_endpoint_url = token_endpoint_url
        self.token_introspection_url = token_introspection_url

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'OAuth2ClientTokens':
        return OAuth2ClientTokens(self.status, self.access_token, self.refresh_token, self.client_id, self.error, self.token_endpoint_url, self.token_introspection_url)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'OAuth2ClientTokens':
        return OAuth2ClientTokens(**d, validate_toml=validate_toml)


class ArtifactDetails:
    """

    """
    def __init__(self, entity_id, artifact_type, path, mime_type, check_missing, remove_path, *, validate_toml=False) -> None:
        self.entity_id = entity_id
        self.artifact_type = artifact_type
        self.path = path
        self.mime_type = mime_type
        self.check_missing = check_missing
        self.remove_path = remove_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ArtifactDetails':
        return ArtifactDetails(self.entity_id, self.artifact_type, self.path, self.mime_type, self.check_missing, self.remove_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ArtifactDetails':
        return ArtifactDetails(**d, validate_toml=validate_toml)


class ExportEntityJob:
    """

    :param id: On success, holds the new ID of the exported entity in h2ai-storage.
    """
    def __init__(self, status, id, error, *, validate_toml=False) -> None:
        self.status = status
        self.id = id
        self.error = error

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['status'] = self.status.dump()
        return d

    def clone(self) -> 'ExportEntityJob':
        return ExportEntityJob(self.status, self.id, self.error)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExportEntityJob':
        d['status'] = JobStatus.load(d['status'])
        return ExportEntityJob(**d, validate_toml=validate_toml)


class ImportEntityJob:
    """

    :param key: On success, holds the key of the new local entity representing the imported one.
    """
    def __init__(self, status, key, error, progress, *, validate_toml=False) -> None:
        self.status = status
        self.key = key
        self.error = error
        self.progress = progress

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['status'] = self.status.dump()
        return d

    def clone(self) -> 'ImportEntityJob':
        return ImportEntityJob(self.status, self.key, self.error, self.progress)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ImportEntityJob':
        d['status'] = JobStatus.load(d['status'])
        return ImportEntityJob(**d, validate_toml=validate_toml)


class Sharing:
    """

    """
    def __init__(self, id, entity_id, user_id, group_id, restriction_role_id, type, *, validate_toml=False) -> None:
        self.id = id
        self.entity_id = entity_id
        self.user_id = user_id
        self.group_id = group_id
        self.restriction_role_id = restriction_role_id
        self.type = type

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Sharing':
        return Sharing(self.id, self.entity_id, self.user_id, self.group_id, self.restriction_role_id, self.type)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Sharing':
        return Sharing(**d, validate_toml=validate_toml)


class Role:
    """

    """
    def __init__(self, id, display_name, *, validate_toml=False) -> None:
        self.id = id
        self.display_name = display_name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Role':
        return Role(self.id, self.display_name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Role':
        return Role(**d, validate_toml=validate_toml)


class StorageUser:
    """

    """
    def __init__(self, id, username, *, validate_toml=False) -> None:
        self.id = id
        self.username = username

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'StorageUser':
        return StorageUser(self.id, self.username)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'StorageUser':
        return StorageUser(**d, validate_toml=validate_toml)


class ExperimentScore:
    """

    """
    def __init__(self, score, score_sd, roc, gains, act_vs_pred, residual_plot, *, validate_toml=False) -> None:
        self.score = score
        self.score_sd = score_sd
        self.roc = roc
        self.gains = gains
        self.act_vs_pred = act_vs_pred
        self.residual_plot = residual_plot

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['roc'] = self.roc.dump()
        d['gains'] = self.gains.dump()
        d['act_vs_pred'] = self.act_vs_pred.dump()
        d['residual_plot'] = self.residual_plot.dump()
        return d

    def clone(self) -> 'ExperimentScore':
        return ExperimentScore(self.score, self.score_sd, self.roc, self.gains, self.act_vs_pred, self.residual_plot)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExperimentScore':
        d['roc'] = ROC.load(d['roc'])
        d['gains'] = GainLift.load(d['gains'])
        d['act_vs_pred'] = H2OPlot.load(d['act_vs_pred'])
        d['residual_plot'] = H2OPlot.load(d['residual_plot'])
        return ExperimentScore(**d, validate_toml=validate_toml)


class KdbCreateDatasetArgs:
    """

    """
    def __init__(self, dst, query, *, validate_toml=False) -> None:
        self.dst = dst
        self.query = query

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'KdbCreateDatasetArgs':
        return KdbCreateDatasetArgs(self.dst, self.query)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'KdbCreateDatasetArgs':
        return KdbCreateDatasetArgs(**d, validate_toml=validate_toml)


class SparkJDBCConfig:
    """

    """
    def __init__(self, options, url, classpath, jarpath, database, *, validate_toml=False) -> None:
        self.options = options
        self.url = url
        self.classpath = classpath
        self.jarpath = jarpath
        self.database = database

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SparkJDBCConfig':
        return SparkJDBCConfig(self.options, self.url, self.classpath, self.jarpath, self.database)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SparkJDBCConfig':
        return SparkJDBCConfig(**d, validate_toml=validate_toml)


class JdbcCreateDatasetArgs:
    """

    """
    def __init__(self, dst, query, id_column, jdbc_user, password, url, classpath, jarpath, database, *, validate_toml=False) -> None:
        self.dst = dst
        self.query = query
        self.id_column = id_column
        self.jdbc_user = jdbc_user
        self.password = password
        self.url = url
        self.classpath = classpath
        self.jarpath = jarpath
        self.database = database

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'JdbcCreateDatasetArgs':
        return JdbcCreateDatasetArgs(self.dst, self.query, self.id_column, self.jdbc_user, self.password, self.url, self.classpath, self.jarpath, self.database)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'JdbcCreateDatasetArgs':
        return JdbcCreateDatasetArgs(**d, validate_toml=validate_toml)


class HiveCreateDatasetArgs:
    """

    """
    def __init__(self, dst, query, hive_conf_path, keytab_path, auth_type, principal_user, database, *, validate_toml=False) -> None:
        self.dst = dst
        self.query = query
        self.hive_conf_path = hive_conf_path
        self.keytab_path = keytab_path
        self.auth_type = auth_type
        self.principal_user = principal_user
        self.database = database

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'HiveCreateDatasetArgs':
        return HiveCreateDatasetArgs(self.dst, self.query, self.hive_conf_path, self.keytab_path, self.auth_type, self.principal_user, self.database)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HiveCreateDatasetArgs':
        return HiveCreateDatasetArgs(**d, validate_toml=validate_toml)


class HiveConfig:
    """

    """
    def __init__(self, options, hive_conf_path, keytab_path, auth_type, principal_user, database, *, validate_toml=False) -> None:
        self.options = options
        self.hive_conf_path = hive_conf_path
        self.keytab_path = keytab_path
        self.auth_type = auth_type
        self.principal_user = principal_user
        self.database = database

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'HiveConfig':
        return HiveConfig(self.options, self.hive_conf_path, self.keytab_path, self.auth_type, self.principal_user, self.database)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HiveConfig':
        return HiveConfig(**d, validate_toml=validate_toml)


class GPTSummaryJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'GPTSummaryJob':
        return GPTSummaryJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'GPTSummaryJob':
        d['entity'] = GPTSummary.load(d['entity'])
        return GPTSummaryJob(**d, validate_toml=validate_toml)


class GPTSummary:
    """

    """
    def __init__(self, provider, summary, *, validate_toml=False) -> None:
        self.provider = provider
        self.summary = summary

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'GPTSummary':
        return GPTSummary(self.provider, self.summary)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'GPTSummary':
        return GPTSummary(**d, validate_toml=validate_toml)


class FeatureStoreProject:
    """

    """
    def __init__(self, name, description, *, validate_toml=False) -> None:
        self.name = name
        self.description = description

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'FeatureStoreProject':
        return FeatureStoreProject(self.name, self.description)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FeatureStoreProject':
        return FeatureStoreProject(**d, validate_toml=validate_toml)


class FeatureStoreFeatureSet:
    """

    """
    def __init__(self, name, description, *, validate_toml=False) -> None:
        self.name = name
        self.description = description

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'FeatureStoreFeatureSet':
        return FeatureStoreFeatureSet(self.name, self.description)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FeatureStoreFeatureSet':
        return FeatureStoreFeatureSet(**d, validate_toml=validate_toml)


class FeatureStoreCreateDatasetArgs:
    """

    """
    def __init__(self, project, feature_set, *, validate_toml=False) -> None:
        self.project = project
        self.feature_set = feature_set

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'FeatureStoreCreateDatasetArgs':
        return FeatureStoreCreateDatasetArgs(self.project, self.feature_set)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FeatureStoreCreateDatasetArgs':
        return FeatureStoreCreateDatasetArgs(**d, validate_toml=validate_toml)


class GbqCreateDatasetArgs:
    """

    """
    def __init__(self, dataset_id, bucket_name, dst, query, project, location, *, validate_toml=False) -> None:
        self.dataset_id = dataset_id
        self.bucket_name = bucket_name
        self.dst = dst
        self.query = query
        self.project = project
        self.location = location

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'GbqCreateDatasetArgs':
        return GbqCreateDatasetArgs(self.dataset_id, self.bucket_name, self.dst, self.query, self.project, self.location)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'GbqCreateDatasetArgs':
        return GbqCreateDatasetArgs(**d, validate_toml=validate_toml)


class SnowCreateDatasetArgs:
    """

    """
    def __init__(self, region, database, warehouse, schema, role, dst, query, optional_formatting, sf_user, password, account, *, validate_toml=False) -> None:
        self.region = region
        self.database = database
        self.warehouse = warehouse
        self.schema = schema
        self.role = role
        self.dst = dst
        self.query = query
        self.optional_formatting = optional_formatting
        self.sf_user = sf_user
        self.password = password
        self.account = account

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SnowCreateDatasetArgs':
        return SnowCreateDatasetArgs(self.region, self.database, self.warehouse, self.schema, self.role, self.dst, self.query, self.optional_formatting, self.sf_user, self.password, self.account)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SnowCreateDatasetArgs':
        return SnowCreateDatasetArgs(**d, validate_toml=validate_toml)


class ConnectorProperties:
    """

    """
    def __init__(self, type, title_text, input_boxes, *, validate_toml=False) -> None:
        self.type = type
        self.title_text = title_text
        self.input_boxes = input_boxes

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['input_boxes'] = [a.dump() for a in self.input_boxes]
        return d

    def clone(self) -> 'ConnectorProperties':
        return ConnectorProperties(self.type, self.title_text, self.input_boxes)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ConnectorProperties':
        d['input_boxes'] = [InputBoxProperties.load(a) for a in d['input_boxes']]
        return ConnectorProperties(**d, validate_toml=validate_toml)


class InputBoxProperties:
    """

    """
    def __init__(self, type, required, is_password, label_title, placeholder_text, name, *, validate_toml=False) -> None:
        self.type = type
        self.required = required
        self.is_password = is_password
        self.label_title = label_title
        self.placeholder_text = placeholder_text
        self.name = name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'InputBoxProperties':
        return InputBoxProperties(self.type, self.required, self.is_password, self.label_title, self.placeholder_text, self.name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'InputBoxProperties':
        return InputBoxProperties(**d, validate_toml=validate_toml)


class HelpVideo:
    """

    """
    def __init__(self, name, path, *, validate_toml=False) -> None:
        self.name = name
        self.path = path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'HelpVideo':
        return HelpVideo(self.name, self.path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HelpVideo':
        return HelpVideo(**d, validate_toml=validate_toml)


class H2OVisAggregation:
    """

    """
    def __init__(self, aggregated_frame, mapping_frame, *, validate_toml=False) -> None:
        self.aggregated_frame = aggregated_frame
        self.mapping_frame = mapping_frame

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OVisAggregation':
        return H2OVisAggregation(self.aggregated_frame, self.mapping_frame)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OVisAggregation':
        return H2OVisAggregation(**d, validate_toml=validate_toml)


class H2OVisStats:
    """

    """
    def __init__(self, number_of_columns, number_of_rows, column_names, column_is_categorical, *, validate_toml=False) -> None:
        self.number_of_columns = number_of_columns
        self.number_of_rows = number_of_rows
        self.column_names = column_names
        self.column_is_categorical = column_is_categorical

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OVisStats':
        return H2OVisStats(self.number_of_columns, self.number_of_rows, self.column_names, self.column_is_categorical)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OVisStats':
        return H2OVisStats(**d, validate_toml=validate_toml)


class H2OParallelCoordinatesPlot:
    """

    """
    def __init__(self, variable_names, profiles, counts, is_categorical, cluster_indices, data_min_max, *, validate_toml=False) -> None:
        self.variable_names = variable_names
        self.profiles = profiles
        self.counts = counts
        self.is_categorical = is_categorical
        self.cluster_indices = cluster_indices
        self.data_min_max = data_min_max

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OParallelCoordinatesPlot':
        return H2OParallelCoordinatesPlot(self.variable_names, self.profiles, self.counts, self.is_categorical, self.cluster_indices, self.data_min_max)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OParallelCoordinatesPlot':
        return H2OParallelCoordinatesPlot(**d, validate_toml=validate_toml)


class H2OHeatMap:
    """

    """
    def __init__(self, column_names, columns, number_of_columns, number_of_rows, counts, *, validate_toml=False) -> None:
        self.column_names = column_names
        self.columns = columns
        self.number_of_columns = number_of_columns
        self.number_of_rows = number_of_rows
        self.counts = counts

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OHeatMap':
        return H2OHeatMap(self.column_names, self.columns, self.number_of_columns, self.number_of_rows, self.counts)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OHeatMap':
        return H2OHeatMap(**d, validate_toml=validate_toml)


class NoGroupVariable:
    """

    """
    def __init__(self, upper_hinge, median, lower_hinge, extreme_outliers, outliers, lower_adjacent_value, upper_adjacent_value, *, validate_toml=False) -> None:
        self.upper_hinge = upper_hinge
        self.median = median
        self.lower_hinge = lower_hinge
        self.extreme_outliers = extreme_outliers
        self.outliers = outliers
        self.lower_adjacent_value = lower_adjacent_value
        self.upper_adjacent_value = upper_adjacent_value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'NoGroupVariable':
        return NoGroupVariable(self.upper_hinge, self.median, self.lower_hinge, self.extreme_outliers, self.outliers, self.lower_adjacent_value, self.upper_adjacent_value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'NoGroupVariable':
        return NoGroupVariable(**d, validate_toml=validate_toml)


class H2OBoxplotEnvelope:
    """

    """
    def __init__(self, no_group_variable, *, validate_toml=False) -> None:
        self.no_group_variable = no_group_variable

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['no_group_variable'] = self.no_group_variable.dump()
        return d

    def clone(self) -> 'H2OBoxplotEnvelope':
        return H2OBoxplotEnvelope(self.no_group_variable)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OBoxplotEnvelope':
        d['no_group_variable'] = NoGroupVariable.load(d['no_group_variable'])
        return H2OBoxplotEnvelope(**d, validate_toml=validate_toml)


class H2OBoxplot:
    """

    """
    def __init__(self, boxplots, variable_name, *, validate_toml=False) -> None:
        self.boxplots = boxplots
        self.variable_name = variable_name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OBoxplot':
        return H2OBoxplot(self.boxplots, self.variable_name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OBoxplot':
        return H2OBoxplot(**d, validate_toml=validate_toml)


class Histogram:
    """

    """
    def __init__(self, counts, variable_name, number_of_bars, number_of_ticks, scale_max, scale_min, *, validate_toml=False) -> None:
        self.counts = counts
        self.variable_name = variable_name
        self.number_of_bars = number_of_bars
        self.number_of_ticks = number_of_ticks
        self.scale_max = scale_max
        self.scale_min = scale_min

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Histogram':
        return Histogram(self.counts, self.variable_name, self.number_of_bars, self.number_of_ticks, self.scale_max, self.scale_min)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Histogram':
        return Histogram(**d, validate_toml=validate_toml)


class H2OHistobar:
    """

    """
    def __init__(self, variable_name, bins, counts, *, validate_toml=False) -> None:
        self.variable_name = variable_name
        self.bins = bins
        self.counts = counts

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OHistobar':
        return H2OHistobar(self.variable_name, self.bins, self.counts)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OHistobar':
        return H2OHistobar(**d, validate_toml=validate_toml)


class H2OScale:
    """

    """
    def __init__(self, scale_min, scale_max, number_of_ticks, *, validate_toml=False) -> None:
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.number_of_ticks = number_of_ticks

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OScale':
        return H2OScale(self.scale_min, self.scale_max, self.number_of_ticks)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OScale':
        return H2OScale(**d, validate_toml=validate_toml)


class H2OOutliers:
    """

    """
    def __init__(self, row_indices, *, validate_toml=False) -> None:
        self.row_indices = row_indices

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OOutliers':
        return H2OOutliers(self.row_indices)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OOutliers':
        return H2OOutliers(**d, validate_toml=validate_toml)


class H2OPlot:
    """

    """
    def __init__(self, x_variable_name, x_values, y_variable_name, y_values, counts, *, validate_toml=False) -> None:
        self.x_variable_name = x_variable_name
        self.x_values = x_values
        self.y_variable_name = y_variable_name
        self.y_values = y_values
        self.counts = counts

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OPlot':
        return H2OPlot(self.x_variable_name, self.x_values, self.y_variable_name, self.y_values, self.counts)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OPlot':
        return H2OPlot(**d, validate_toml=validate_toml)


class H2ODotplot:
    """

    """
    def __init__(self, stacks, variable_name, x_values, scale_min, scale_max, histogram, outliers, *, validate_toml=False) -> None:
        self.stacks = stacks
        self.variable_name = variable_name
        self.x_values = x_values
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.histogram = histogram
        self.outliers = outliers

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['histogram'] = self.histogram.dump()
        d['outliers'] = self.outliers.dump()
        return d

    def clone(self) -> 'H2ODotplot':
        return H2ODotplot(self.stacks, self.variable_name, self.x_values, self.scale_min, self.scale_max, self.histogram, self.outliers)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2ODotplot':
        d['histogram'] = Histogram.load(d['histogram'])
        d['outliers'] = H2OOutliers.load(d['outliers'])
        return H2ODotplot(**d, validate_toml=validate_toml)


class H2ONetwork:
    """

    """
    def __init__(self, edges, edge_weights, nodes, *, validate_toml=False) -> None:
        self.edges = edges
        self.edge_weights = edge_weights
        self.nodes = nodes

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2ONetwork':
        return H2ONetwork(self.edges, self.edge_weights, self.nodes)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2ONetwork':
        return H2ONetwork(**d, validate_toml=validate_toml)


class H2OBarchart:
    """

    """
    def __init__(self, x_values, y_values, x_variable_name, y_variable_name, group_variable_name, *, validate_toml=False) -> None:
        self.x_values = x_values
        self.y_values = y_values
        self.x_variable_name = x_variable_name
        self.y_variable_name = y_variable_name
        self.group_variable_name = group_variable_name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OBarchart':
        return H2OBarchart(self.x_values, self.y_values, self.x_variable_name, self.y_variable_name, self.group_variable_name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OBarchart':
        return H2OBarchart(**d, validate_toml=validate_toml)


class H2ORegression:
    """

    """
    def __init__(self, x_variable_name, x_values, y_variable_name, y_values, predicted_values, *, validate_toml=False) -> None:
        self.x_variable_name = x_variable_name
        self.x_values = x_values
        self.y_variable_name = y_variable_name
        self.y_values = y_values
        self.predicted_values = predicted_values

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2ORegression':
        return H2ORegression(self.x_variable_name, self.x_values, self.y_variable_name, self.y_values, self.predicted_values)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2ORegression':
        return H2ORegression(**d, validate_toml=validate_toml)


class H2OTimeSeriesPlot:
    """

    """
    def __init__(self, subtype, x_variable_name, y_variable_name, x_values, y_values, *, validate_toml=False) -> None:
        self.subtype = subtype
        self.x_variable_name = x_variable_name
        self.y_variable_name = y_variable_name
        self.x_values = x_values
        self.y_values = y_values

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OTimeSeriesPlot':
        return H2OTimeSeriesPlot(self.subtype, self.x_variable_name, self.y_variable_name, self.x_values, self.y_values)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OTimeSeriesPlot':
        return H2OTimeSeriesPlot(**d, validate_toml=validate_toml)


class AutoVizScatterplot:
    """

    """
    def __init__(self, clumpy, correlated, unusual, *, validate_toml=False) -> None:
        self.clumpy = clumpy
        self.correlated = correlated
        self.unusual = unusual

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoVizScatterplot':
        return AutoVizScatterplot(self.clumpy, self.correlated, self.unusual)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoVizScatterplot':
        return AutoVizScatterplot(**d, validate_toml=validate_toml)


class AutoVizHistogram:
    """

    """
    def __init__(self, spikes, skewed, unusual, gaps, *, validate_toml=False) -> None:
        self.spikes = spikes
        self.skewed = skewed
        self.unusual = unusual
        self.gaps = gaps

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoVizHistogram':
        return AutoVizHistogram(self.spikes, self.skewed, self.unusual, self.gaps)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoVizHistogram':
        return AutoVizHistogram(**d, validate_toml=validate_toml)


class AutoVizBoxplot:
    """

    """
    def __init__(self, disparate, heteroscedastic, *, validate_toml=False) -> None:
        self.disparate = disparate
        self.heteroscedastic = heteroscedastic

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoVizBoxplot':
        return AutoVizBoxplot(self.disparate, self.heteroscedastic)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoVizBoxplot':
        return AutoVizBoxplot(**d, validate_toml=validate_toml)


class AutoVizBiplot:
    """

    """
    def __init__(self, components, loadings, number_of_rows, number_of_columns, component_names, counts, variable_names, *, validate_toml=False) -> None:
        self.components = components
        self.loadings = loadings
        self.number_of_rows = number_of_rows
        self.number_of_columns = number_of_columns
        self.component_names = component_names
        self.counts = counts
        self.variable_names = variable_names

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoVizBiplot':
        return AutoVizBiplot(self.components, self.loadings, self.number_of_rows, self.number_of_columns, self.component_names, self.counts, self.variable_names)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoVizBiplot':
        return AutoVizBiplot(**d, validate_toml=validate_toml)


class AutoVizBarcharts:
    """

    """
    def __init__(self, unbalanced, *, validate_toml=False) -> None:
        self.unbalanced = unbalanced

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoVizBarcharts':
        return AutoVizBarcharts(self.unbalanced)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoVizBarcharts':
        return AutoVizBarcharts(**d, validate_toml=validate_toml)


class AutoVizTransformations:
    """

    """
    def __init__(self, transforms, deletions, *, validate_toml=False) -> None:
        self.transforms = transforms
        self.deletions = deletions

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoVizTransformations':
        return AutoVizTransformations(self.transforms, self.deletions)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoVizTransformations':
        return AutoVizTransformations(**d, validate_toml=validate_toml)


class H2OAutoViz:
    """

    """
    def __init__(self, scatterplots, barcharts, histograms, boxplots, outliers, biplot, transformations, custom_plots, *, validate_toml=False) -> None:
        self.scatterplots = scatterplots
        self.barcharts = barcharts
        self.histograms = histograms
        self.boxplots = boxplots
        self.outliers = outliers
        self.biplot = biplot
        self.transformations = transformations
        self.custom_plots = custom_plots

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['scatterplots'] = self.scatterplots.dump()
        d['barcharts'] = self.barcharts.dump()
        d['histograms'] = self.histograms.dump()
        d['boxplots'] = self.boxplots.dump()
        d['biplot'] = self.biplot.dump()
        d['transformations'] = self.transformations.dump()
        d['custom_plots'] = [a.dump() for a in self.custom_plots]
        return d

    def clone(self) -> 'H2OAutoViz':
        return H2OAutoViz(self.scatterplots, self.barcharts, self.histograms, self.boxplots, self.outliers, self.biplot, self.transformations, self.custom_plots)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OAutoViz':
        d['scatterplots'] = AutoVizScatterplot.load(d['scatterplots'])
        d['barcharts'] = AutoVizBarcharts.load(d['barcharts'])
        d['histograms'] = AutoVizHistogram.load(d['histograms'])
        d['boxplots'] = AutoVizBoxplot.load(d['boxplots'])
        d['biplot'] = AutoVizBiplot.load(d['biplot'])
        d['transformations'] = AutoVizTransformations.load(d['transformations'])
        d['custom_plots'] = [VegaPlotJob.load(a) for a in d['custom_plots']]
        return H2OAutoViz(**d, validate_toml=validate_toml)


class ScorerWrapper:
    """

    """
    def __init__(self, name, unhashed_name, maximize, for_regression, for_binomial, for_multiclass, limit_type, description, is_custom, mapping_keys, *, validate_toml=False) -> None:
        self.name = name
        self.unhashed_name = unhashed_name
        self.maximize = maximize
        self.for_regression = for_regression
        self.for_binomial = for_binomial
        self.for_multiclass = for_multiclass
        self.limit_type = limit_type
        self.description = description
        self.is_custom = is_custom
        self.mapping_keys = mapping_keys

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ScorerWrapper':
        return ScorerWrapper(self.name, self.unhashed_name, self.maximize, self.for_regression, self.for_binomial, self.for_multiclass, self.limit_type, self.description, self.is_custom, self.mapping_keys)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ScorerWrapper':
        return ScorerWrapper(**d, validate_toml=validate_toml)


class RecipeActivationItem:
    """

    """
    def __init__(self, unhashed_name, name, *, validate_toml=False) -> None:
        self.unhashed_name = unhashed_name
        self.name = name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'RecipeActivationItem':
        return RecipeActivationItem(self.unhashed_name, self.name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'RecipeActivationItem':
        return RecipeActivationItem(**d, validate_toml=validate_toml)


class RecipeActivation:
    """

    """
    def __init__(self, transformers, models, scorers, data, individuals, *, validate_toml=False) -> None:
        self.transformers = transformers
        self.models = models
        self.scorers = scorers
        self.data = data
        self.individuals = individuals

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['transformers'] = [a.dump() for a in self.transformers]
        d['models'] = [a.dump() for a in self.models]
        d['scorers'] = [a.dump() for a in self.scorers]
        d['data'] = [a.dump() for a in self.data]
        d['individuals'] = [a.dump() for a in self.individuals]
        return d

    def clone(self) -> 'RecipeActivation':
        return RecipeActivation(self.transformers, self.models, self.scorers, self.data, self.individuals)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'RecipeActivation':
        d['transformers'] = [RecipeActivationItem.load(a) for a in d['transformers']]
        d['models'] = [RecipeActivationItem.load(a) for a in d['models']]
        d['scorers'] = [RecipeActivationItem.load(a) for a in d['scorers']]
        d['data'] = [RecipeActivationItem.load(a) for a in d['data']]
        d['individuals'] = [RecipeActivationItem.load(a) for a in d['individuals']]
        return RecipeActivation(**d, validate_toml=validate_toml)


class TransformerWrapper:
    """

    """
    def __init__(self, name, unhashed_name, is_custom, description, mapping_keys, *, validate_toml=False) -> None:
        self.name = name
        self.unhashed_name = unhashed_name
        self.is_custom = is_custom
        self.description = description
        self.mapping_keys = mapping_keys

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TransformerWrapper':
        return TransformerWrapper(self.name, self.unhashed_name, self.is_custom, self.description, self.mapping_keys)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TransformerWrapper':
        return TransformerWrapper(**d, validate_toml=validate_toml)


class PreTransformerWrapper:
    """

    """
    def __init__(self, name, unhashed_name, is_custom, description, mapping_keys, *, validate_toml=False) -> None:
        self.name = name
        self.unhashed_name = unhashed_name
        self.is_custom = is_custom
        self.description = description
        self.mapping_keys = mapping_keys

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'PreTransformerWrapper':
        return PreTransformerWrapper(self.name, self.unhashed_name, self.is_custom, self.description, self.mapping_keys)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'PreTransformerWrapper':
        return PreTransformerWrapper(**d, validate_toml=validate_toml)


class ModelEstimatorWrapper:
    """

    """
    def __init__(self, name, unhashed_name, is_custom, is_unsupervised, description, mapping_keys, *, validate_toml=False) -> None:
        self.name = name
        self.unhashed_name = unhashed_name
        self.is_custom = is_custom
        self.is_unsupervised = is_unsupervised
        self.description = description
        self.mapping_keys = mapping_keys

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ModelEstimatorWrapper':
        return ModelEstimatorWrapper(self.name, self.unhashed_name, self.is_custom, self.is_unsupervised, self.description, self.mapping_keys)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelEstimatorWrapper':
        return ModelEstimatorWrapper(**d, validate_toml=validate_toml)


class DataWrapper:
    """

    """
    def __init__(self, name, unhashed_name, is_custom, description, mapping_keys, *, validate_toml=False) -> None:
        self.name = name
        self.unhashed_name = unhashed_name
        self.is_custom = is_custom
        self.description = description
        self.mapping_keys = mapping_keys

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DataWrapper':
        return DataWrapper(self.name, self.unhashed_name, self.is_custom, self.description, self.mapping_keys)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DataWrapper':
        return DataWrapper(**d, validate_toml=validate_toml)


class IndividualWrapper:
    """

    """
    def __init__(self, name, unhashed_name, is_custom, description, experiment_id, experiment_description, for_regression, for_binary, for_multiclass, mapping_keys, *, validate_toml=False) -> None:
        self.name = name
        self.unhashed_name = unhashed_name
        self.is_custom = is_custom
        self.description = description
        self.experiment_id = experiment_id
        self.experiment_description = experiment_description
        self.for_regression = for_regression
        self.for_binary = for_binary
        self.for_multiclass = for_multiclass
        self.mapping_keys = mapping_keys

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'IndividualWrapper':
        return IndividualWrapper(self.name, self.unhashed_name, self.is_custom, self.description, self.experiment_id, self.experiment_description, self.for_regression, self.for_binary, self.for_multiclass, self.mapping_keys)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'IndividualWrapper':
        return IndividualWrapper(**d, validate_toml=validate_toml)


class DatasetNumericColumnStats:
    """

    :param mean: Needs to be str due to inf/nan/null
    :param std: Needs to be str due to inf/nan/null
    :param min: Can be either number or a date
    :param max: Can be either number or a date
    """
    def __init__(self, count, mean, std, min, max, unique, freq, hist_ticks, hist_counts, *, validate_toml=False) -> None:
        self.count = count
        self.mean = mean
        self.std = std
        self.min = min
        self.max = max
        self.unique = unique
        self.freq = freq
        self.hist_ticks = hist_ticks
        self.hist_counts = hist_counts

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DatasetNumericColumnStats':
        return DatasetNumericColumnStats(self.count, self.mean, self.std, self.min, self.max, self.unique, self.freq, self.hist_ticks, self.hist_counts)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetNumericColumnStats':
        return DatasetNumericColumnStats(**d, validate_toml=validate_toml)


class DatasetNonNumericColumnStats:
    """

    """
    def __init__(self, count, unique, top, freq, hist_ticks, hist_counts, *, validate_toml=False) -> None:
        self.count = count
        self.unique = unique
        self.top = top
        self.freq = freq
        self.hist_ticks = hist_ticks
        self.hist_counts = hist_counts

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DatasetNonNumericColumnStats':
        return DatasetNonNumericColumnStats(self.count, self.unique, self.top, self.freq, self.hist_ticks, self.hist_counts)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetNonNumericColumnStats':
        return DatasetNonNumericColumnStats(**d, validate_toml=validate_toml)


class DatasetColumnStats:
    """

    """
    def __init__(self, is_numeric, num_classes, numeric, non_numeric, *, validate_toml=False) -> None:
        self.is_numeric = is_numeric
        self.num_classes = num_classes
        self.numeric = numeric
        self.non_numeric = non_numeric

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['numeric'] = self.numeric.dump()
        d['non_numeric'] = self.non_numeric.dump()
        return d

    def clone(self) -> 'DatasetColumnStats':
        return DatasetColumnStats(self.is_numeric, self.num_classes, self.numeric, self.non_numeric)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetColumnStats':
        d['numeric'] = DatasetNumericColumnStats.load(d['numeric'])
        d['non_numeric'] = DatasetNonNumericColumnStats.load(d['non_numeric'])
        return DatasetColumnStats(**d, validate_toml=validate_toml)


class DatasetColumn:
    """

    :param data_type: Internal column representation type
    :param logical_types: List of DS types, which this column can be treated as ['num', 'cat', 'date', 'datetime', 'text', 'id', 'image']
    """
    def __init__(self, name, data_type, logical_types, datetime_format, stats, data, training_params, *, validate_toml=False) -> None:
        self.name = name
        self.data_type = data_type
        self.logical_types = logical_types
        self.datetime_format = datetime_format
        self.stats = stats
        self.data = data
        self.training_params = training_params

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['stats'] = self.stats.dump()
        d['training_params'] = self.training_params.dump()
        return d

    def clone(self) -> 'DatasetColumn':
        return DatasetColumn(self.name, self.data_type, self.logical_types, self.datetime_format, self.stats, self.data, self.training_params)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetColumn':
        d['stats'] = DatasetColumnStats.load(d['stats'])
        d['training_params'] = TrainingFeature.load(d['training_params'])
        return DatasetColumn(**d, validate_toml=validate_toml)


class Dataset:
    """

    :param remote: True if the model is only available remotely in Storage.
    :param missing_values: list of missing values used during original import of the data, so can avoid re-doing work in DAI
    """
    def __init__(self, key, name, file_path, file_size, bin_file_path, data_source, row_count, column_count, columns, original_frame, aggregated_frame, mapping_frame, uploaded, remote, missing_values, notes, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.file_path = file_path
        self.file_size = file_size
        self.bin_file_path = bin_file_path
        self.data_source = data_source
        self.row_count = row_count
        self.column_count = column_count
        self.columns = columns
        self.original_frame = original_frame
        self.aggregated_frame = aggregated_frame
        self.mapping_frame = mapping_frame
        self.uploaded = uploaded
        self.remote = remote
        self.missing_values = missing_values
        self.notes = notes

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['columns'] = [a.dump() for a in self.columns]
        return d

    def clone(self) -> 'Dataset':
        return Dataset(self.key, self.name, self.file_path, self.file_size, self.bin_file_path, self.data_source, self.row_count, self.column_count, self.columns, self.original_frame, self.aggregated_frame, self.mapping_frame, self.uploaded, self.remote, self.missing_values, self.notes)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Dataset':
        d['columns'] = [DatasetColumn.load(a) for a in d['columns']]
        return Dataset(**d, validate_toml=validate_toml)


class DatasetSummary:
    """

    :param remote: True if the model is only available remotely in Storage.
    """
    def __init__(self, key, name, file_path, file_size, data_source, row_count, column_count, import_status, import_error, aggregation_status, aggregation_error, aggregated_frame, mapping_frame, uploaded, remote, created, logfile_path, file_path_at_runtime, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.file_path = file_path
        self.file_size = file_size
        self.data_source = data_source
        self.row_count = row_count
        self.column_count = column_count
        self.import_status = import_status
        self.import_error = import_error
        self.aggregation_status = aggregation_status
        self.aggregation_error = aggregation_error
        self.aggregated_frame = aggregated_frame
        self.mapping_frame = mapping_frame
        self.uploaded = uploaded
        self.remote = remote
        self.created = created
        self.logfile_path = logfile_path
        self.file_path_at_runtime = file_path_at_runtime

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DatasetSummary':
        return DatasetSummary(self.key, self.name, self.file_path, self.file_size, self.data_source, self.row_count, self.column_count, self.import_status, self.import_error, self.aggregation_status, self.aggregation_error, self.aggregated_frame, self.mapping_frame, self.uploaded, self.remote, self.created, self.logfile_path, self.file_path_at_runtime)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetSummary':
        return DatasetSummary(**d, validate_toml=validate_toml)


class DatasetSummaryForProject:
    """

    :param remote: True if the dataset is available remotely in Storage.
    :param local: True if the dataset is available locally.
    """
    def __init__(self, key, name, file_path, file_size, data_source, row_count, column_count, import_status, import_error, aggregation_status, aggregation_error, aggregated_frame, mapping_frame, uploaded, remote, local, created, logfile_path, file_path_at_runtime, tags, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.file_path = file_path
        self.file_size = file_size
        self.data_source = data_source
        self.row_count = row_count
        self.column_count = column_count
        self.import_status = import_status
        self.import_error = import_error
        self.aggregation_status = aggregation_status
        self.aggregation_error = aggregation_error
        self.aggregated_frame = aggregated_frame
        self.mapping_frame = mapping_frame
        self.uploaded = uploaded
        self.remote = remote
        self.local = local
        self.created = created
        self.logfile_path = logfile_path
        self.file_path_at_runtime = file_path_at_runtime
        self.tags = tags

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DatasetSummaryForProject':
        return DatasetSummaryForProject(self.key, self.name, self.file_path, self.file_size, self.data_source, self.row_count, self.column_count, self.import_status, self.import_error, self.aggregation_status, self.aggregation_error, self.aggregated_frame, self.mapping_frame, self.uploaded, self.remote, self.local, self.created, self.logfile_path, self.file_path_at_runtime, self.tags)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetSummaryForProject':
        return DatasetSummaryForProject(**d, validate_toml=validate_toml)


class ListDatasetQueryResponse:
    """

    """
    def __init__(self, datasets, offset, limit, total_count, *, validate_toml=False) -> None:
        self.datasets = datasets
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['datasets'] = [a.dump() for a in self.datasets]
        return d

    def clone(self) -> 'ListDatasetQueryResponse':
        return ListDatasetQueryResponse(self.datasets, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListDatasetQueryResponse':
        d['datasets'] = [DatasetSummary.load(a) for a in d['datasets']]
        return ListDatasetQueryResponse(**d, validate_toml=validate_toml)


class DatasetJob:
    """

    """
    def __init__(self, progress, status, error, message, aggregation_status, aggregation_error, entity, created, uploaded, logfile_path, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.aggregation_status = aggregation_status
        self.aggregation_error = aggregation_error
        self.entity = entity
        self.created = created
        self.uploaded = uploaded
        self.logfile_path = logfile_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'DatasetJob':
        return DatasetJob(self.progress, self.status, self.error, self.message, self.aggregation_status, self.aggregation_error, self.entity, self.created, self.uploaded, self.logfile_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetJob':
        d['entity'] = Dataset.load(d['entity'])
        return DatasetJob(**d, validate_toml=validate_toml)


class AutoVizSummary:
    """

    """
    def __init__(self, key, name, dataset, progress, status, message, training_duration, created, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.dataset = dataset
        self.progress = progress
        self.status = status
        self.message = message
        self.training_duration = training_duration
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['dataset'] = self.dataset.dump()
        return d

    def clone(self) -> 'AutoVizSummary':
        return AutoVizSummary(self.key, self.name, self.dataset, self.progress, self.status, self.message, self.training_duration, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoVizSummary':
        d['dataset'] = DatasetReference.load(d['dataset'])
        return AutoVizSummary(**d, validate_toml=validate_toml)


class AutoVizJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, finished, key, name, dataset, deprecated, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.finished = finished
        self.key = key
        self.name = name
        self.dataset = dataset
        self.deprecated = deprecated

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        d['dataset'] = self.dataset.dump()
        return d

    def clone(self) -> 'AutoVizJob':
        return AutoVizJob(self.progress, self.status, self.error, self.message, self.entity, self.created, self.finished, self.key, self.name, self.dataset, self.deprecated)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoVizJob':
        d['entity'] = H2OAutoViz.load(d['entity'])
        d['dataset'] = DatasetReference.load(d['dataset'])
        return AutoVizJob(**d, validate_toml=validate_toml)


class CustomRecipeDbSyncJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'CustomRecipeDbSyncJob':
        return CustomRecipeDbSyncJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CustomRecipeDbSyncJob':
        d['entity'] = CustomRecipeDbSync.load(d['entity'])
        return CustomRecipeDbSyncJob(**d, validate_toml=validate_toml)


class CustomRecipeDbSync:
    """

    """
    def __init__(self, key, name, models, scorers, transformers, datas, explainers, individuals, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.models = models
        self.scorers = scorers
        self.transformers = transformers
        self.datas = datas
        self.explainers = explainers
        self.individuals = individuals

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['models'] = self.models.dump()
        d['scorers'] = self.scorers.dump()
        d['transformers'] = self.transformers.dump()
        d['datas'] = self.datas.dump()
        d['explainers'] = self.explainers.dump()
        d['individuals'] = self.individuals.dump()
        return d

    def clone(self) -> 'CustomRecipeDbSync':
        return CustomRecipeDbSync(self.key, self.name, self.models, self.scorers, self.transformers, self.datas, self.explainers, self.individuals)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CustomRecipeDbSync':
        d['models'] = CustomRecipeDbSyncRecipeType.load(d['models'])
        d['scorers'] = CustomRecipeDbSyncRecipeType.load(d['scorers'])
        d['transformers'] = CustomRecipeDbSyncRecipeType.load(d['transformers'])
        d['datas'] = CustomRecipeDbSyncRecipeType.load(d['datas'])
        d['explainers'] = CustomRecipeDbSyncRecipeType.load(d['explainers'])
        d['individuals'] = CustomRecipeDbSyncRecipeType.load(d['individuals'])
        return CustomRecipeDbSync(**d, validate_toml=validate_toml)


class CustomRecipeDbSyncRecipeType:
    """

    """
    def __init__(self, directory_md5_hash, is_directory_unchanged, custom_recipes, invalid_recipe_files, *, validate_toml=False) -> None:
        self.directory_md5_hash = directory_md5_hash
        self.is_directory_unchanged = is_directory_unchanged
        self.custom_recipes = custom_recipes
        self.invalid_recipe_files = invalid_recipe_files

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['custom_recipes'] = [a.dump() for a in self.custom_recipes]
        return d

    def clone(self) -> 'CustomRecipeDbSyncRecipeType':
        return CustomRecipeDbSyncRecipeType(self.directory_md5_hash, self.is_directory_unchanged, self.custom_recipes, self.invalid_recipe_files)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CustomRecipeDbSyncRecipeType':
        d['custom_recipes'] = [PersistentCustomRecipe.load(a) for a in d['custom_recipes']]
        return CustomRecipeDbSyncRecipeType(**d, validate_toml=validate_toml)


class PersistentCustomRecipe:
    """

    :param display_name: is same as blueprint.display_name
    :param display_name_unhashed: is unhashed version of the display_name
    :param new_name: is same as blueprint.new_name before versioning logic
    :param new_name_unhashed: is the unhashed version of new_name
    :param note: not named description since blueprints can have description metadata
    :param type: transformers | models | scorers | data | explainer | individuals
    :param mtime: identical as target file mtime
    """
    def __init__(self, key, display_name, display_name_unhashed, new_name, new_name_unhashed, input_name, note, original_url, type, target_file, is_active, created, ancestor_key, mtime, md5_hash, *, validate_toml=False) -> None:
        self.key = key
        self.display_name = display_name
        self.display_name_unhashed = display_name_unhashed
        self.new_name = new_name
        self.new_name_unhashed = new_name_unhashed
        self.input_name = input_name
        self.note = note
        self.original_url = original_url
        self.type = type
        self.target_file = target_file
        self.is_active = is_active
        self.created = created
        self.ancestor_key = ancestor_key
        self.mtime = mtime
        self.md5_hash = md5_hash

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'PersistentCustomRecipe':
        return PersistentCustomRecipe(self.key, self.display_name, self.display_name_unhashed, self.new_name, self.new_name_unhashed, self.input_name, self.note, self.original_url, self.type, self.target_file, self.is_active, self.created, self.ancestor_key, self.mtime, self.md5_hash)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'PersistentCustomRecipe':
        return PersistentCustomRecipe(**d, validate_toml=validate_toml)


class UpdateCustomRecipeResponse:
    """

    """
    def __init__(self, job_key, errors, *, validate_toml=False) -> None:
        self.job_key = job_key
        self.errors = errors

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'UpdateCustomRecipeResponse':
        return UpdateCustomRecipeResponse(self.job_key, self.errors)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'UpdateCustomRecipeResponse':
        return UpdateCustomRecipeResponse(**d, validate_toml=validate_toml)


class ListCustomRecipeResponse:
    """

    """
    def __init__(self, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['items'] = [a.dump() for a in self.items]
        return d

    def clone(self) -> 'ListCustomRecipeResponse':
        return ListCustomRecipeResponse(self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListCustomRecipeResponse':
        d['items'] = [PersistentCustomRecipe.load(a) for a in d['items']]
        return ListCustomRecipeResponse(**d, validate_toml=validate_toml)


class GetPersistentCustomRecipeResponse:
    """

    """
    def __init__(self, custom_recipe, code, *, validate_toml=False) -> None:
        self.custom_recipe = custom_recipe
        self.code = code

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['custom_recipe'] = self.custom_recipe.dump()
        return d

    def clone(self) -> 'GetPersistentCustomRecipeResponse':
        return GetPersistentCustomRecipeResponse(self.custom_recipe, self.code)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'GetPersistentCustomRecipeResponse':
        d['custom_recipe'] = PersistentCustomRecipe.load(d['custom_recipe'])
        return GetPersistentCustomRecipeResponse(**d, validate_toml=validate_toml)


class VegaPlotJob:
    """

    :param entity: Vega dictionary
    """
    def __init__(self, progress, status, error, message, entity, created, key, description, dataset, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.key = key
        self.description = description
        self.dataset = dataset

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['dataset'] = self.dataset.dump()
        return d

    def clone(self) -> 'VegaPlotJob':
        return VegaPlotJob(self.progress, self.status, self.error, self.message, self.entity, self.created, self.key, self.description, self.dataset)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'VegaPlotJob':
        d['dataset'] = DatasetReference.load(d['dataset'])
        return VegaPlotJob(**d, validate_toml=validate_toml)


class ScatterPlotJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'ScatterPlotJob':
        return ScatterPlotJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ScatterPlotJob':
        d['entity'] = H2OPlot.load(d['entity'])
        return ScatterPlotJob(**d, validate_toml=validate_toml)


class HistogramJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'HistogramJob':
        return HistogramJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HistogramJob':
        d['entity'] = Histogram.load(d['entity'])
        return HistogramJob(**d, validate_toml=validate_toml)


class VisStatsJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'VisStatsJob':
        return VisStatsJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'VisStatsJob':
        d['entity'] = H2OVisStats.load(d['entity'])
        return VisStatsJob(**d, validate_toml=validate_toml)


class BoxplotJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'BoxplotJob':
        return BoxplotJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'BoxplotJob':
        d['entity'] = H2OBoxplot.load(d['entity'])
        return BoxplotJob(**d, validate_toml=validate_toml)


class DotplotJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'DotplotJob':
        return DotplotJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DotplotJob':
        d['entity'] = H2ODotplot.load(d['entity'])
        return DotplotJob(**d, validate_toml=validate_toml)


class HeatMapJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'HeatMapJob':
        return HeatMapJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HeatMapJob':
        d['entity'] = H2OHeatMap.load(d['entity'])
        return HeatMapJob(**d, validate_toml=validate_toml)


class NetworkJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'NetworkJob':
        return NetworkJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'NetworkJob':
        d['entity'] = H2ONetwork.load(d['entity'])
        return NetworkJob(**d, validate_toml=validate_toml)


class ParallelCoordinatesPlotJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'ParallelCoordinatesPlotJob':
        return ParallelCoordinatesPlotJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ParallelCoordinatesPlotJob':
        d['entity'] = H2OParallelCoordinatesPlot.load(d['entity'])
        return ParallelCoordinatesPlotJob(**d, validate_toml=validate_toml)


class BarchartJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'BarchartJob':
        return BarchartJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'BarchartJob':
        d['entity'] = H2OBarchart.load(d['entity'])
        return BarchartJob(**d, validate_toml=validate_toml)


class OutliersJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'OutliersJob':
        return OutliersJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'OutliersJob':
        d['entity'] = H2OOutliers.load(d['entity'])
        return OutliersJob(**d, validate_toml=validate_toml)


class FileSearchResult:
    """

    """
    def __init__(self, type, name, extra, path, *, validate_toml=False) -> None:
        self.type = type
        self.name = name
        self.extra = extra
        self.path = path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'FileSearchResult':
        return FileSearchResult(self.type, self.name, self.extra, self.path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FileSearchResult':
        return FileSearchResult(**d, validate_toml=validate_toml)


class FileSearchResults:
    """

    """
    def __init__(self, dir, entries, *, validate_toml=False) -> None:
        self.dir = dir
        self.entries = entries

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entries'] = [a.dump() for a in self.entries]
        return d

    def clone(self) -> 'FileSearchResults':
        return FileSearchResults(self.dir, self.entries)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FileSearchResults':
        d['entries'] = [FileSearchResult.load(a) for a in d['entries']]
        return FileSearchResults(**d, validate_toml=validate_toml)


class ModelParameters:
    """

    """
    def __init__(self, dataset, resumed_model, target_col, weight_col, fold_col, orig_time_col, time_col, is_classification, cols_to_drop, validset, testset, enable_gpus, seed, accuracy, time, interpretability, score_f_name, time_groups_columns, unavailable_columns_at_prediction_time, time_period_in_seconds, num_prediction_periods, num_gap_periods, is_timeseries, cols_imputation, config_overrides, custom_features, is_image, *, validate_toml=False) -> None:
        self.dataset = dataset
        self.resumed_model = resumed_model
        self.target_col = target_col
        self.weight_col = weight_col
        self.fold_col = fold_col
        self.orig_time_col = orig_time_col
        self.time_col = time_col
        self.is_classification = is_classification
        self.cols_to_drop = cols_to_drop
        self.validset = validset
        self.testset = testset
        self.enable_gpus = enable_gpus
        self.seed = seed
        self.accuracy = accuracy
        self.time = time
        self.interpretability = interpretability
        self.score_f_name = score_f_name
        self.time_groups_columns = time_groups_columns
        self.unavailable_columns_at_prediction_time = unavailable_columns_at_prediction_time
        self.time_period_in_seconds = time_period_in_seconds
        self.num_prediction_periods = num_prediction_periods
        self.num_gap_periods = num_gap_periods
        self.is_timeseries = is_timeseries
        self.cols_imputation = cols_imputation
        self.config_overrides = config_overrides
        self.custom_features = custom_features
        self.is_image = is_image
        if validate_toml:
            validation.validate_toml(config_overrides, 'config_overrides')

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['dataset'] = self.dataset.dump()
        d['resumed_model'] = self.resumed_model.dump()
        d['validset'] = self.validset.dump()
        d['testset'] = self.testset.dump()
        d['cols_imputation'] = [a.dump() for a in self.cols_imputation]
        d['custom_features'] = [a.dump() for a in self.custom_features]
        return d

    def clone(self) -> 'ModelParameters':
        return ModelParameters(self.dataset, self.resumed_model, self.target_col, self.weight_col, self.fold_col, self.orig_time_col, self.time_col, self.is_classification, self.cols_to_drop, self.validset, self.testset, self.enable_gpus, self.seed, self.accuracy, self.time, self.interpretability, self.score_f_name, self.time_groups_columns, self.unavailable_columns_at_prediction_time, self.time_period_in_seconds, self.num_prediction_periods, self.num_gap_periods, self.is_timeseries, self.cols_imputation, self.config_overrides, self.custom_features, self.is_image)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelParameters':
        d['dataset'] = DatasetReference.load(d['dataset'])
        d['resumed_model'] = ModelReference.load(d['resumed_model'])
        d['validset'] = DatasetReference.load(d['validset'])
        d['testset'] = DatasetReference.load(d['testset'])
        d['cols_imputation'] = [ColumnImputation.load(a) for a in d['cols_imputation']]
        d['custom_features'] = [TrainingFeature.load(a) for a in d['custom_features']]
        return ModelParameters(**d, validate_toml=validate_toml)


class ColumnImputation:
    """

    :param meta: e.g. percentile rank
    :param precomputed: Whether value provided, or computed at validation
    """
    def __init__(self, col_name, type, value, meta, precomputed, *, validate_toml=False) -> None:
        self.col_name = col_name
        self.type = type
        self.value = value
        self.meta = meta
        self.precomputed = precomputed

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ColumnImputation':
        return ColumnImputation(self.col_name, self.type, self.value, self.meta, self.precomputed)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ColumnImputation':
        return ColumnImputation(**d, validate_toml=validate_toml)


class ListDatasetsRequest:
    """

    """
    def __init__(self, offset, limit, *, validate_toml=False) -> None:
        self.offset = offset
        self.limit = limit

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ListDatasetsRequest':
        return ListDatasetsRequest(self.offset, self.limit)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListDatasetsRequest':
        return ListDatasetsRequest(**d, validate_toml=validate_toml)


class ListDatasetsResponse:
    """

    """
    def __init__(self, datasets, *, validate_toml=False) -> None:
        self.datasets = datasets

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['datasets'] = [a.dump() for a in self.datasets]
        return d

    def clone(self) -> 'ListDatasetsResponse':
        return ListDatasetsResponse(self.datasets)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListDatasetsResponse':
        d['datasets'] = [Dataset.load(a) for a in d['datasets']]
        return ListDatasetsResponse(**d, validate_toml=validate_toml)


class VarImpTable:
    """

    """
    def __init__(self, gain, interaction, description, *, validate_toml=False) -> None:
        self.gain = gain
        self.interaction = interaction
        self.description = description

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'VarImpTable':
        return VarImpTable(self.gain, self.interaction, self.description)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'VarImpTable':
        return VarImpTable(**d, validate_toml=validate_toml)


class ScoresTable:
    """

    """
    def __init__(self, best, iteration, score, model_types, *, validate_toml=False) -> None:
        self.best = best
        self.iteration = iteration
        self.score = score
        self.model_types = model_types

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ScoresTable':
        return ScoresTable(self.best, self.iteration, self.score, self.model_types)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ScoresTable':
        return ScoresTable(**d, validate_toml=validate_toml)


class TraceEvent:
    """

    """
    def __init__(self, name, ph, ts, ppid, pid, tid, args, *, validate_toml=False) -> None:
        self.name = name
        self.ph = ph
        self.ts = ts
        self.ppid = ppid
        self.pid = pid
        self.tid = tid
        self.args = args

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TraceEvent':
        return TraceEvent(self.name, self.ph, self.ts, self.ppid, self.pid, self.tid, self.args)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TraceEvent':
        return TraceEvent(**d, validate_toml=validate_toml)


class TraceProgress:
    """

    """
    def __init__(self, trace_events, *, validate_toml=False) -> None:
        self.trace_events = trace_events

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['trace_events'] = [a.dump() for a in self.trace_events]
        return d

    def clone(self) -> 'TraceProgress':
        return TraceProgress(self.trace_events)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TraceProgress':
        d['trace_events'] = [TraceEvent.load(a) for a in d['trace_events']]
        return TraceProgress(**d, validate_toml=validate_toml)


class ModelTraceEvents:
    """

    """
    def __init__(self, events, done, status, *, validate_toml=False) -> None:
        self.events = events
        self.done = done
        self.status = status

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['events'] = [a.dump() for a in self.events]
        return d

    def clone(self) -> 'ModelTraceEvents':
        return ModelTraceEvents(self.events, self.done, self.status)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelTraceEvents':
        d['events'] = [TraceEvent.load(a) for a in d['events']]
        return ModelTraceEvents(**d, validate_toml=validate_toml)


class AutoDLInit:
    """

    """
    def __init__(self, score_f_name, *, validate_toml=False) -> None:
        self.score_f_name = score_f_name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoDLInit':
        return AutoDLInit(self.score_f_name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoDLInit':
        return AutoDLInit(**d, validate_toml=validate_toml)


class AutoDLVisualization:
    """

    :param path: Path to file containing Vega definition, **relative to the data_directory**
    :param checksum: MD5 of file storing visualization, used to detect any changes
    """
    def __init__(self, path, title, description, checksum, *, validate_toml=False) -> None:
        self.path = path
        self.title = title
        self.description = description
        self.checksum = checksum

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoDLVisualization':
        return AutoDLVisualization(self.path, self.title, self.description, self.checksum)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoDLVisualization':
        return AutoDLVisualization(**d, validate_toml=validate_toml)


class AutoDLProgress:
    """

    :param custom_visualizations: List of custom visualizations
    """
    def __init__(self, key, message, iteration, max_iterations, progress, importances, scores, score, score_mean, score_sd, total_features, roc, gains, act_vs_pred, residual_plot, custom_visualizations, *, validate_toml=False) -> None:
        self.key = key
        self.message = message
        self.iteration = iteration
        self.max_iterations = max_iterations
        self.progress = progress
        self.importances = importances
        self.scores = scores
        self.score = score
        self.score_mean = score_mean
        self.score_sd = score_sd
        self.total_features = total_features
        self.roc = roc
        self.gains = gains
        self.act_vs_pred = act_vs_pred
        self.residual_plot = residual_plot
        self.custom_visualizations = custom_visualizations

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['importances'] = [a.dump() for a in self.importances]
        d['scores'] = self.scores.dump()
        d['roc'] = self.roc.dump()
        d['gains'] = self.gains.dump()
        d['act_vs_pred'] = self.act_vs_pred.dump()
        d['residual_plot'] = self.residual_plot.dump()
        d['custom_visualizations'] = [a.dump() for a in self.custom_visualizations]
        return d

    def clone(self) -> 'AutoDLProgress':
        return AutoDLProgress(self.key, self.message, self.iteration, self.max_iterations, self.progress, self.importances, self.scores, self.score, self.score_mean, self.score_sd, self.total_features, self.roc, self.gains, self.act_vs_pred, self.residual_plot, self.custom_visualizations)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoDLProgress':
        d['importances'] = [VarImpTable.load(a) for a in d['importances']]
        d['scores'] = ScoresTable.load(d['scores'])
        d['roc'] = ROC.load(d['roc'])
        d['gains'] = GainLift.load(d['gains'])
        d['act_vs_pred'] = H2OPlot.load(d['act_vs_pred'])
        d['residual_plot'] = H2OPlot.load(d['residual_plot'])
        d['custom_visualizations'] = [AutoDLVisualization.load(a) for a in d['custom_visualizations']]
        return AutoDLProgress(**d, validate_toml=validate_toml)


class GainLift:
    """

    """
    def __init__(self, quantiles, gains, lifts, cum_right, cum_wrong, *, validate_toml=False) -> None:
        self.quantiles = quantiles
        self.gains = gains
        self.lifts = lifts
        self.cum_right = cum_right
        self.cum_wrong = cum_wrong

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'GainLift':
        return GainLift(self.quantiles, self.gains, self.lifts, self.cum_right, self.cum_wrong)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'GainLift':
        return GainLift(**d, validate_toml=validate_toml)


class ROC:
    """

    """
    def __init__(self, labels, auc, aucpr, thresholds, threshold_cms, argmax_cm, default_threshold, *, validate_toml=False) -> None:
        self.labels = labels
        self.auc = auc
        self.aucpr = aucpr
        self.thresholds = thresholds
        self.threshold_cms = threshold_cms
        self.argmax_cm = argmax_cm
        self.default_threshold = default_threshold

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['threshold_cms'] = [a.dump() for a in self.threshold_cms]
        d['argmax_cm'] = self.argmax_cm.dump()
        return d

    def clone(self) -> 'ROC':
        return ROC(self.labels, self.auc, self.aucpr, self.thresholds, self.threshold_cms, self.argmax_cm, self.default_threshold)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ROC':
        d['threshold_cms'] = [ConfusionMatrix.load(a) for a in d['threshold_cms']]
        d['argmax_cm'] = ConfusionMatrix.load(d['argmax_cm'])
        return ROC(**d, validate_toml=validate_toml)


class ConfusionMatrix:
    """

    """
    def __init__(self, labels, matrix, row_counts, col_counts, miss_counts, *, validate_toml=False) -> None:
        self.labels = labels
        self.matrix = matrix
        self.row_counts = row_counts
        self.col_counts = col_counts
        self.miss_counts = miss_counts

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ConfusionMatrix':
        return ConfusionMatrix(self.labels, self.matrix, self.row_counts, self.col_counts, self.miss_counts)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ConfusionMatrix':
        return ConfusionMatrix(**d, validate_toml=validate_toml)


class TrainingColumn:
    """

    """
    def __init__(self, name, dtype, typecode, possible_types, is_numeric, is_integer, is_bool, is_real, is_str, min, max, num_uniques, has_na, sample_levels, datetime_format, raw_name, *, validate_toml=False) -> None:
        self.name = name
        self.dtype = dtype
        self.typecode = typecode
        self.possible_types = possible_types
        self.is_numeric = is_numeric
        self.is_integer = is_integer
        self.is_bool = is_bool
        self.is_real = is_real
        self.is_str = is_str
        self.min = min
        self.max = max
        self.num_uniques = num_uniques
        self.has_na = has_na
        self.sample_levels = sample_levels
        self.datetime_format = datetime_format
        self.raw_name = raw_name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TrainingColumn':
        return TrainingColumn(self.name, self.dtype, self.typecode, self.possible_types, self.is_numeric, self.is_integer, self.is_bool, self.is_real, self.is_str, self.min, self.max, self.num_uniques, self.has_na, self.sample_levels, self.datetime_format, self.raw_name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TrainingColumn':
        return TrainingColumn(**d, validate_toml=validate_toml)


class ModelTrainingSchema:
    """

    """
    def __init__(self, pre_columns, columns, transformed_columns, target, is_classification, labels, missing_values, *, validate_toml=False) -> None:
        self.pre_columns = pre_columns
        self.columns = columns
        self.transformed_columns = transformed_columns
        self.target = target
        self.is_classification = is_classification
        self.labels = labels
        self.missing_values = missing_values

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['pre_columns'] = [a.dump() for a in self.pre_columns]
        d['columns'] = [a.dump() for a in self.columns]
        return d

    def clone(self) -> 'ModelTrainingSchema':
        return ModelTrainingSchema(self.pre_columns, self.columns, self.transformed_columns, self.target, self.is_classification, self.labels, self.missing_values)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelTrainingSchema':
        d['pre_columns'] = [TrainingColumn.load(a) for a in d['pre_columns']]
        d['columns'] = [TrainingColumn.load(a) for a in d['columns']]
        return ModelTrainingSchema(**d, validate_toml=validate_toml)


class TrainingFeature:
    """
    Used to pre-populate experiment with force-in features

    :param transformer_name: Name of transformer, which will be applied
    :param column_names: Ordered list! E.g. for SUM Interaction transformer could be ['x1', 'x2']
    :param monotonicity: Monotonic constraint for model (auto, -1, 0, 1) - as in https://xgboost.readthedocs.io/en/latest/tutorials/monotonic.html
    :param forced_on_off: Whether this feature must be in experiment (on), or must not (off). ['on', 'off', 'auto']
    :param sign: per-feature sign
    :param exclusive: If this feature with this column is used, whether any other transformer can use it
    :param allowed_transformations: List of transformers which can be later applied to this feature
    :param allowed_models: List of models, which can use this feature
    :param interaction_depth: Max depth of nested transformation, in which this feature can occur, -1 for infinite
    :param apply_to_all: Apply the selected transformer to all vs any selected columns
    """
    def __init__(self, transformer_name, column_names, monotonicity, forced_on_off, sign, exclusive, allowed_transformations, allowed_models, interaction_depth, apply_to_all, *, validate_toml=False) -> None:
        self.transformer_name = transformer_name
        self.column_names = column_names
        self.monotonicity = monotonicity
        self.forced_on_off = forced_on_off
        self.sign = sign
        self.exclusive = exclusive
        self.allowed_transformations = allowed_transformations
        self.allowed_models = allowed_models
        self.interaction_depth = interaction_depth
        self.apply_to_all = apply_to_all

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TrainingFeature':
        return TrainingFeature(self.transformer_name, self.column_names, self.monotonicity, self.forced_on_off, self.sign, self.exclusive, self.allowed_transformations, self.allowed_models, self.interaction_depth, self.apply_to_all)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TrainingFeature':
        return TrainingFeature(**d, validate_toml=validate_toml)


class AutoDLResult:
    """

    """
    def __init__(self, log_file_path, pickle_path, summary_path, train_predictions_path, valid_predictions_path, test_predictions_path, unfitted_pipeline_path, fitted_model_path, scoring_pipeline_path, mojo_pipeline_path, test_score, test_score_sd, test_roc, test_gains, test_act_vs_pred, test_residual_plot, labels, ids_col, *, validate_toml=False) -> None:
        self.log_file_path = log_file_path
        self.pickle_path = pickle_path
        self.summary_path = summary_path
        self.train_predictions_path = train_predictions_path
        self.valid_predictions_path = valid_predictions_path
        self.test_predictions_path = test_predictions_path
        self.unfitted_pipeline_path = unfitted_pipeline_path
        self.fitted_model_path = fitted_model_path
        self.scoring_pipeline_path = scoring_pipeline_path
        self.mojo_pipeline_path = mojo_pipeline_path
        self.test_score = test_score
        self.test_score_sd = test_score_sd
        self.test_roc = test_roc
        self.test_gains = test_gains
        self.test_act_vs_pred = test_act_vs_pred
        self.test_residual_plot = test_residual_plot
        self.labels = labels
        self.ids_col = ids_col

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['test_roc'] = self.test_roc.dump()
        d['test_gains'] = self.test_gains.dump()
        d['test_act_vs_pred'] = self.test_act_vs_pred.dump()
        d['test_residual_plot'] = self.test_residual_plot.dump()
        return d

    def clone(self) -> 'AutoDLResult':
        return AutoDLResult(self.log_file_path, self.pickle_path, self.summary_path, self.train_predictions_path, self.valid_predictions_path, self.test_predictions_path, self.unfitted_pipeline_path, self.fitted_model_path, self.scoring_pipeline_path, self.mojo_pipeline_path, self.test_score, self.test_score_sd, self.test_roc, self.test_gains, self.test_act_vs_pred, self.test_residual_plot, self.labels, self.ids_col)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoDLResult':
        d['test_roc'] = ROC.load(d['test_roc'])
        d['test_gains'] = GainLift.load(d['test_gains'])
        d['test_act_vs_pred'] = H2OPlot.load(d['test_act_vs_pred'])
        d['test_residual_plot'] = H2OPlot.load(d['test_residual_plot'])
        return AutoDLResult(**d, validate_toml=validate_toml)


class AutoDLScoresOverview:
    """

    :param path: Path to Markdown document describing scores
    :param checksum: MD5 checksum to check if content was modified
    """
    def __init__(self, path, checksum, *, validate_toml=False) -> None:
        self.path = path
        self.checksum = checksum

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoDLScoresOverview':
        return AutoDLScoresOverview(self.path, self.checksum)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoDLScoresOverview':
        return AutoDLScoresOverview(**d, validate_toml=validate_toml)


class AutoDLNotification:
    """

    :param priority: 0 - low, 1 - medium, 2 - high
    """
    def __init__(self, key, title, content, priority, created, *, validate_toml=False) -> None:
        self.key = key
        self.title = title
        self.content = content
        self.priority = priority
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoDLNotification':
        return AutoDLNotification(self.key, self.title, self.content, self.priority, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoDLNotification':
        return AutoDLNotification(**d, validate_toml=validate_toml)


class MLIProgress:
    """

    """
    def __init__(self, progress, msg, done, *, validate_toml=False) -> None:
        self.progress = progress
        self.msg = msg
        self.done = done

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'MLIProgress':
        return MLIProgress(self.progress, self.msg, self.done)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'MLIProgress':
        return MLIProgress(**d, validate_toml=validate_toml)


class H2OProgress:
    """

    """
    def __init__(self, progress, msg, done, *, validate_toml=False) -> None:
        self.progress = progress
        self.msg = msg
        self.done = done

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'H2OProgress':
        return H2OProgress(self.progress, self.msg, self.done)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'H2OProgress':
        return H2OProgress(**d, validate_toml=validate_toml)


class SystemStats:
    """

    """
    def __init__(self, kind, cpu, mem, per, *, validate_toml=False) -> None:
        self.kind = kind
        self.cpu = cpu
        self.mem = mem
        self.per = per

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['mem'] = self.mem.dump()
        return d

    def clone(self) -> 'SystemStats':
        return SystemStats(self.kind, self.cpu, self.mem, self.per)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SystemStats':
        d['mem'] = MemoryStats.load(d['mem'])
        return SystemStats(**d, validate_toml=validate_toml)


class GPUStats:
    """

    """
    def __init__(self, gpus, mems, types, usages, *, validate_toml=False) -> None:
        self.gpus = gpus
        self.mems = mems
        self.types = types
        self.usages = usages

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'GPUStats':
        return GPUStats(self.gpus, self.mems, self.types, self.usages)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'GPUStats':
        return GPUStats(**d, validate_toml=validate_toml)


class DiskStats:
    """

    """
    def __init__(self, total, available, limit, *, validate_toml=False) -> None:
        self.total = total
        self.available = available
        self.limit = limit

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DiskStats':
        return DiskStats(self.total, self.available, self.limit)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiskStats':
        return DiskStats(**d, validate_toml=validate_toml)


class MemoryStats:
    """

    """
    def __init__(self, total, available, limit, per, *, validate_toml=False) -> None:
        self.total = total
        self.available = available
        self.limit = limit
        self.per = per

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'MemoryStats':
        return MemoryStats(self.total, self.available, self.limit, self.per)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'MemoryStats':
        return MemoryStats(**d, validate_toml=validate_toml)


class ExperimentsStats:
    """

    """
    def __init__(self, total, running, finished, failed, my_total, my_running, my_finished, my_failed, *, validate_toml=False) -> None:
        self.total = total
        self.running = running
        self.finished = finished
        self.failed = failed
        self.my_total = my_total
        self.my_running = my_running
        self.my_finished = my_finished
        self.my_failed = my_failed

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExperimentsStats':
        return ExperimentsStats(self.total, self.running, self.finished, self.failed, self.my_total, self.my_running, self.my_finished, self.my_failed)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExperimentsStats':
        return ExperimentsStats(**d, validate_toml=validate_toml)


class Model:
    """

    :param insights_paths: Paths to insights documents in Markdown format
    :param notifications: List of AutoDLNotification keys
    :param experiment_dir: Path to root of experiment structure
    :param remote: True if the model is only available remotely in Storage.
    :param custom_visualizations: List of custom model visualizations
    """
    def __init__(self, key, description, parameters, log_file_path, pickle_path, autoreport_path, summary_path, train_predictions_path, valid_predictions_path, test_predictions_path, unfitted_pipeline_path, fitted_model_path, scoring_pipeline_path, mojo_pipeline_path, mojo_memory_usage, valid_score, valid_score_sd, valid_roc, valid_gains, valid_act_vs_pred, valid_residual_plot, test_score, test_score_sd, test_roc, test_gains, test_act_vs_pred, test_residual_plot, labels, ids_col, score_f_name, score, iteration_data, insights_paths, scores_overview, trace_events, notifications, training_duration, deprecated, patched_pred_contribs, max_iterations, model_file_size, diagnostic_keys, summary, experiment_dir, remote, custom_visualizations, *, validate_toml=False) -> None:
        self.key = key
        self.description = description
        self.parameters = parameters
        self.log_file_path = log_file_path
        self.pickle_path = pickle_path
        self.autoreport_path = autoreport_path
        self.summary_path = summary_path
        self.train_predictions_path = train_predictions_path
        self.valid_predictions_path = valid_predictions_path
        self.test_predictions_path = test_predictions_path
        self.unfitted_pipeline_path = unfitted_pipeline_path
        self.fitted_model_path = fitted_model_path
        self.scoring_pipeline_path = scoring_pipeline_path
        self.mojo_pipeline_path = mojo_pipeline_path
        self.mojo_memory_usage = mojo_memory_usage
        self.valid_score = valid_score
        self.valid_score_sd = valid_score_sd
        self.valid_roc = valid_roc
        self.valid_gains = valid_gains
        self.valid_act_vs_pred = valid_act_vs_pred
        self.valid_residual_plot = valid_residual_plot
        self.test_score = test_score
        self.test_score_sd = test_score_sd
        self.test_roc = test_roc
        self.test_gains = test_gains
        self.test_act_vs_pred = test_act_vs_pred
        self.test_residual_plot = test_residual_plot
        self.labels = labels
        self.ids_col = ids_col
        self.score_f_name = score_f_name
        self.score = score
        self.iteration_data = iteration_data
        self.insights_paths = insights_paths
        self.scores_overview = scores_overview
        self.trace_events = trace_events
        self.notifications = notifications
        self.training_duration = training_duration
        self.deprecated = deprecated
        self.patched_pred_contribs = patched_pred_contribs
        self.max_iterations = max_iterations
        self.model_file_size = model_file_size
        self.diagnostic_keys = diagnostic_keys
        self.summary = summary
        self.experiment_dir = experiment_dir
        self.remote = remote
        self.custom_visualizations = custom_visualizations

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['parameters'] = self.parameters.dump()
        d['valid_roc'] = self.valid_roc.dump()
        d['valid_gains'] = self.valid_gains.dump()
        d['valid_act_vs_pred'] = self.valid_act_vs_pred.dump()
        d['valid_residual_plot'] = self.valid_residual_plot.dump()
        d['test_roc'] = self.test_roc.dump()
        d['test_gains'] = self.test_gains.dump()
        d['test_act_vs_pred'] = self.test_act_vs_pred.dump()
        d['test_residual_plot'] = self.test_residual_plot.dump()
        d['scores_overview'] = self.scores_overview.dump()
        d['custom_visualizations'] = [a.dump() for a in self.custom_visualizations]
        return d

    def clone(self) -> 'Model':
        return Model(self.key, self.description, self.parameters, self.log_file_path, self.pickle_path, self.autoreport_path, self.summary_path, self.train_predictions_path, self.valid_predictions_path, self.test_predictions_path, self.unfitted_pipeline_path, self.fitted_model_path, self.scoring_pipeline_path, self.mojo_pipeline_path, self.mojo_memory_usage, self.valid_score, self.valid_score_sd, self.valid_roc, self.valid_gains, self.valid_act_vs_pred, self.valid_residual_plot, self.test_score, self.test_score_sd, self.test_roc, self.test_gains, self.test_act_vs_pred, self.test_residual_plot, self.labels, self.ids_col, self.score_f_name, self.score, self.iteration_data, self.insights_paths, self.scores_overview, self.trace_events, self.notifications, self.training_duration, self.deprecated, self.patched_pred_contribs, self.max_iterations, self.model_file_size, self.diagnostic_keys, self.summary, self.experiment_dir, self.remote, self.custom_visualizations)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Model':
        d['parameters'] = ModelParameters.load(d['parameters'])
        d['valid_roc'] = ROC.load(d['valid_roc'])
        d['valid_gains'] = GainLift.load(d['valid_gains'])
        d['valid_act_vs_pred'] = H2OPlot.load(d['valid_act_vs_pred'])
        d['valid_residual_plot'] = H2OPlot.load(d['valid_residual_plot'])
        d['test_roc'] = ROC.load(d['test_roc'])
        d['test_gains'] = GainLift.load(d['test_gains'])
        d['test_act_vs_pred'] = H2OPlot.load(d['test_act_vs_pred'])
        d['test_residual_plot'] = H2OPlot.load(d['test_residual_plot'])
        d['scores_overview'] = AutoDLScoresOverview.load(d['scores_overview'])
        d['custom_visualizations'] = [AutoDLVisualization.load(a) for a in d['custom_visualizations']]
        return Model(**d, validate_toml=validate_toml)


class ModelJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, eta, created, started, worker_info, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.eta = eta
        self.created = created
        self.started = started
        self.worker_info = worker_info

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        d['worker_info'] = self.worker_info.dump()
        return d

    def clone(self) -> 'ModelJob':
        return ModelJob(self.progress, self.status, self.error, self.message, self.entity, self.eta, self.created, self.started, self.worker_info)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelJob':
        d['entity'] = Model.load(d['entity'])
        d['worker_info'] = WorkerID.load(d['worker_info'])
        return ModelJob(**d, validate_toml=validate_toml)


class ImportModelJob:
    """

    """
    def __init__(self, progress, status, error, message, aggregation_status, aggregation_error, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.aggregation_status = aggregation_status
        self.aggregation_error = aggregation_error
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'ImportModelJob':
        return ImportModelJob(self.progress, self.status, self.error, self.message, self.aggregation_status, self.aggregation_error, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ImportModelJob':
        d['entity'] = Model.load(d['entity'])
        return ImportModelJob(**d, validate_toml=validate_toml)


class ModelSummary:
    """

    :param remote: True if the model is only available remotely in Storage.
    """
    def __init__(self, key, description, parameters, log_file_path, pickle_path, summary_path, train_predictions_path, valid_predictions_path, test_predictions_path, progress, status, training_duration, score_f_name, score, test_score, deprecated, model_file_size, diagnostic_keys, remote, scoring_pipeline_size, mojo_pipeline_size, mojo_memory_usage, created, *, validate_toml=False) -> None:
        self.key = key
        self.description = description
        self.parameters = parameters
        self.log_file_path = log_file_path
        self.pickle_path = pickle_path
        self.summary_path = summary_path
        self.train_predictions_path = train_predictions_path
        self.valid_predictions_path = valid_predictions_path
        self.test_predictions_path = test_predictions_path
        self.progress = progress
        self.status = status
        self.training_duration = training_duration
        self.score_f_name = score_f_name
        self.score = score
        self.test_score = test_score
        self.deprecated = deprecated
        self.model_file_size = model_file_size
        self.diagnostic_keys = diagnostic_keys
        self.remote = remote
        self.scoring_pipeline_size = scoring_pipeline_size
        self.mojo_pipeline_size = mojo_pipeline_size
        self.mojo_memory_usage = mojo_memory_usage
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['parameters'] = self.parameters.dump()
        return d

    def clone(self) -> 'ModelSummary':
        return ModelSummary(self.key, self.description, self.parameters, self.log_file_path, self.pickle_path, self.summary_path, self.train_predictions_path, self.valid_predictions_path, self.test_predictions_path, self.progress, self.status, self.training_duration, self.score_f_name, self.score, self.test_score, self.deprecated, self.model_file_size, self.diagnostic_keys, self.remote, self.scoring_pipeline_size, self.mojo_pipeline_size, self.mojo_memory_usage, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelSummary':
        d['parameters'] = ModelParameters.load(d['parameters'])
        return ModelSummary(**d, validate_toml=validate_toml)


class ListModelQueryResponse:
    """

    """
    def __init__(self, models, offset, limit, total_count, *, validate_toml=False) -> None:
        self.models = models
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['models'] = [a.dump() for a in self.models]
        return d

    def clone(self) -> 'ListModelQueryResponse':
        return ListModelQueryResponse(self.models, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListModelQueryResponse':
        d['models'] = [ModelSummary.load(a) for a in d['models']]
        return ListModelQueryResponse(**d, validate_toml=validate_toml)


class InterpretParameters:
    """

    """
    def __init__(self, dai_model, dataset, target_col, prediction_col, use_raw_features, nfolds, klime_cluster_col, weight_col, drop_cols, sample, sample_num_rows, qbin_cols, qbin_count, lime_method, dt_tree_depth, config_overrides, vars_to_pdp, dia_cols, testset, debug_model_errors, debug_model_errors_class, *, validate_toml=False) -> None:
        self.dai_model = dai_model
        self.dataset = dataset
        self.target_col = target_col
        self.prediction_col = prediction_col
        self.use_raw_features = use_raw_features
        self.nfolds = nfolds
        self.klime_cluster_col = klime_cluster_col
        self.weight_col = weight_col
        self.drop_cols = drop_cols
        self.sample = sample
        self.sample_num_rows = sample_num_rows
        self.qbin_cols = qbin_cols
        self.qbin_count = qbin_count
        self.lime_method = lime_method
        self.dt_tree_depth = dt_tree_depth
        self.config_overrides = config_overrides
        self.vars_to_pdp = vars_to_pdp
        self.dia_cols = dia_cols
        self.testset = testset
        self.debug_model_errors = debug_model_errors
        self.debug_model_errors_class = debug_model_errors_class
        if validate_toml:
            validation.validate_toml(config_overrides, 'config_overrides')

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['dai_model'] = self.dai_model.dump()
        d['dataset'] = self.dataset.dump()
        d['testset'] = self.testset.dump()
        return d

    def clone(self) -> 'InterpretParameters':
        return InterpretParameters(self.dai_model, self.dataset, self.target_col, self.prediction_col, self.use_raw_features, self.nfolds, self.klime_cluster_col, self.weight_col, self.drop_cols, self.sample, self.sample_num_rows, self.qbin_cols, self.qbin_count, self.lime_method, self.dt_tree_depth, self.config_overrides, self.vars_to_pdp, self.dia_cols, self.testset, self.debug_model_errors, self.debug_model_errors_class)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'InterpretParameters':
        d['dai_model'] = ModelReference.load(d['dai_model'])
        d['dataset'] = DatasetReference.load(d['dataset'])
        d['testset'] = DatasetReference.load(d['testset'])
        return InterpretParameters(**d, validate_toml=validate_toml)


class InterpretSummary:
    """

    """
    def __init__(self, key, description, parameters, progress, status, training_duration, is_timeseries, *, validate_toml=False) -> None:
        self.key = key
        self.description = description
        self.parameters = parameters
        self.progress = progress
        self.status = status
        self.training_duration = training_duration
        self.is_timeseries = is_timeseries

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['parameters'] = self.parameters.dump()
        return d

    def clone(self) -> 'InterpretSummary':
        return InterpretSummary(self.key, self.description, self.parameters, self.progress, self.status, self.training_duration, self.is_timeseries)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'InterpretSummary':
        d['parameters'] = InterpretParameters.load(d['parameters'])
        return InterpretSummary(**d, validate_toml=validate_toml)


class Prediction:
    """

    """
    def __init__(self, key, model_key, scoring_dataset_key, predictions_csv_path, *, validate_toml=False) -> None:
        self.key = key
        self.model_key = model_key
        self.scoring_dataset_key = scoring_dataset_key
        self.predictions_csv_path = predictions_csv_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Prediction':
        return Prediction(self.key, self.model_key, self.scoring_dataset_key, self.predictions_csv_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Prediction':
        return Prediction(**d, validate_toml=validate_toml)


class PredictionJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, scoring_duration, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.scoring_duration = scoring_duration

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'PredictionJob':
        return PredictionJob(self.progress, self.status, self.error, self.message, self.entity, self.created, self.scoring_duration)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'PredictionJob':
        d['entity'] = Prediction.load(d['entity'])
        return PredictionJob(**d, validate_toml=validate_toml)


class ListPredictionQueryResponse:
    """

    """
    def __init__(self, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['items'] = [a.dump() for a in self.items]
        return d

    def clone(self) -> 'ListPredictionQueryResponse':
        return ListPredictionQueryResponse(self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListPredictionQueryResponse':
        d['items'] = [PredictionJob.load(a) for a in d['items']]
        return ListPredictionQueryResponse(**d, validate_toml=validate_toml)


class AutoReport:
    """

    """
    def __init__(self, key, model_key, report_path, *, validate_toml=False) -> None:
        self.key = key
        self.model_key = model_key
        self.report_path = report_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AutoReport':
        return AutoReport(self.key, self.model_key, self.report_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoReport':
        return AutoReport(**d, validate_toml=validate_toml)


class AutoReportJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'AutoReportJob':
        return AutoReportJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AutoReportJob':
        d['entity'] = AutoReport.load(d['entity'])
        return AutoReportJob(**d, validate_toml=validate_toml)


class Transformation:
    """

    """
    def __init__(self, key, model_key, training_dataset_key, validation_dataset_key, test_dataset_key, validation_split_fraction, seed, fold_column, training_output_csv_path, validation_output_csv_path, test_output_csv_path, *, validate_toml=False) -> None:
        self.key = key
        self.model_key = model_key
        self.training_dataset_key = training_dataset_key
        self.validation_dataset_key = validation_dataset_key
        self.test_dataset_key = test_dataset_key
        self.validation_split_fraction = validation_split_fraction
        self.seed = seed
        self.fold_column = fold_column
        self.training_output_csv_path = training_output_csv_path
        self.validation_output_csv_path = validation_output_csv_path
        self.test_output_csv_path = test_output_csv_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Transformation':
        return Transformation(self.key, self.model_key, self.training_dataset_key, self.validation_dataset_key, self.test_dataset_key, self.validation_split_fraction, self.seed, self.fold_column, self.training_output_csv_path, self.validation_output_csv_path, self.test_output_csv_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Transformation':
        return Transformation(**d, validate_toml=validate_toml)


class TransformationJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'TransformationJob':
        return TransformationJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TransformationJob':
        d['entity'] = Transformation.load(d['entity'])
        return TransformationJob(**d, validate_toml=validate_toml)


class DaiPdIceInterpretationJob:
    """

    """
    def __init__(self, progress, status, error, message, created, finished, mli_key, dai_key, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.created = created
        self.finished = finished
        self.mli_key = mli_key
        self.dai_key = dai_key

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DaiPdIceInterpretationJob':
        return DaiPdIceInterpretationJob(self.progress, self.status, self.error, self.message, self.created, self.finished, self.mli_key, self.dai_key)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DaiPdIceInterpretationJob':
        return DaiPdIceInterpretationJob(**d, validate_toml=validate_toml)


class InterpretTimeSeries:
    """

    """
    def __init__(self, key, description, tmp_dir, parameters, training_duration, test_window_start, test_window_end, holdout_window_start, holdout_window_end, log_file_path, group_metric_file_path, *, validate_toml=False) -> None:
        self.key = key
        self.description = description
        self.tmp_dir = tmp_dir
        self.parameters = parameters
        self.training_duration = training_duration
        self.test_window_start = test_window_start
        self.test_window_end = test_window_end
        self.holdout_window_start = holdout_window_start
        self.holdout_window_end = holdout_window_end
        self.log_file_path = log_file_path
        self.group_metric_file_path = group_metric_file_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['parameters'] = self.parameters.dump()
        return d

    def clone(self) -> 'InterpretTimeSeries':
        return InterpretTimeSeries(self.key, self.description, self.tmp_dir, self.parameters, self.training_duration, self.test_window_start, self.test_window_end, self.holdout_window_start, self.holdout_window_end, self.log_file_path, self.group_metric_file_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'InterpretTimeSeries':
        d['parameters'] = InterpretParameters.load(d['parameters'])
        return InterpretTimeSeries(**d, validate_toml=validate_toml)


class InterpretTimeSeriesJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'InterpretTimeSeriesJob':
        return InterpretTimeSeriesJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'InterpretTimeSeriesJob':
        d['entity'] = InterpretTimeSeries.load(d['entity'])
        return InterpretTimeSeriesJob(**d, validate_toml=validate_toml)


class Interpretation:
    """

    """
    def __init__(self, key, description, tmp_dir, scoring_package_path, binned_list, labels, parameters, training_duration, log_file_path, lime_rc_csv_path, lime_unformatted_rc_csv_path, shapley_rc_csv_path, shapley_orig_rc_csv_path, subtask_keys, dai_target_transformation, prediction_label, lime_mojo_path, *, validate_toml=False) -> None:
        self.key = key
        self.description = description
        self.tmp_dir = tmp_dir
        self.scoring_package_path = scoring_package_path
        self.binned_list = binned_list
        self.labels = labels
        self.parameters = parameters
        self.training_duration = training_duration
        self.log_file_path = log_file_path
        self.lime_rc_csv_path = lime_rc_csv_path
        self.lime_unformatted_rc_csv_path = lime_unformatted_rc_csv_path
        self.shapley_rc_csv_path = shapley_rc_csv_path
        self.shapley_orig_rc_csv_path = shapley_orig_rc_csv_path
        self.subtask_keys = subtask_keys
        self.dai_target_transformation = dai_target_transformation
        self.prediction_label = prediction_label
        self.lime_mojo_path = lime_mojo_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['parameters'] = self.parameters.dump()
        d['subtask_keys'] = [a.dump() for a in self.subtask_keys]
        return d

    def clone(self) -> 'Interpretation':
        return Interpretation(self.key, self.description, self.tmp_dir, self.scoring_package_path, self.binned_list, self.labels, self.parameters, self.training_duration, self.log_file_path, self.lime_rc_csv_path, self.lime_unformatted_rc_csv_path, self.shapley_rc_csv_path, self.shapley_orig_rc_csv_path, self.subtask_keys, self.dai_target_transformation, self.prediction_label, self.lime_mojo_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Interpretation':
        d['parameters'] = InterpretParameters.load(d['parameters'])
        d['subtask_keys'] = [StrArrayEntry.load(a) for a in d['subtask_keys']]
        return Interpretation(**d, validate_toml=validate_toml)


class InterpretationJob:
    """

    """
    def __init__(self, progress, h2oprogress, mliprogress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.h2oprogress = h2oprogress
        self.mliprogress = mliprogress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['h2oprogress'] = self.h2oprogress.dump()
        d['mliprogress'] = self.mliprogress.dump()
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'InterpretationJob':
        return InterpretationJob(self.progress, self.h2oprogress, self.mliprogress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'InterpretationJob':
        d['h2oprogress'] = H2OProgress.load(d['h2oprogress'])
        d['mliprogress'] = MLIProgress.load(d['mliprogress'])
        d['entity'] = Interpretation.load(d['entity'])
        return InterpretationJob(**d, validate_toml=validate_toml)


class ScoringPipeline:
    """

    :param file_size: Pipeline size in bytes
    """
    def __init__(self, model_key, file_path, file_size, *, validate_toml=False) -> None:
        self.model_key = model_key
        self.file_path = file_path
        self.file_size = file_size

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ScoringPipeline':
        return ScoringPipeline(self.model_key, self.file_path, self.file_size)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ScoringPipeline':
        return ScoringPipeline(**d, validate_toml=validate_toml)


class MojoPipeline:
    """

    :param file_size: Pipeline size in bytes
    """
    def __init__(self, model_key, file_path, file_size, *, validate_toml=False) -> None:
        self.model_key = model_key
        self.file_path = file_path
        self.file_size = file_size

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'MojoPipeline':
        return MojoPipeline(self.model_key, self.file_path, self.file_size)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'MojoPipeline':
        return MojoPipeline(**d, validate_toml=validate_toml)


class IndivRecipe:
    """

    """
    def __init__(self, model_key, file_path, *, validate_toml=False) -> None:
        self.model_key = model_key
        self.file_path = file_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'IndivRecipe':
        return IndivRecipe(self.model_key, self.file_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'IndivRecipe':
        return IndivRecipe(**d, validate_toml=validate_toml)


class ScoringPipelineJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'ScoringPipelineJob':
        return ScoringPipelineJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ScoringPipelineJob':
        d['entity'] = ScoringPipeline.load(d['entity'])
        return ScoringPipelineJob(**d, validate_toml=validate_toml)


class MojoPipelineJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'MojoPipelineJob':
        return MojoPipelineJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'MojoPipelineJob':
        d['entity'] = MojoPipeline.load(d['entity'])
        return MojoPipelineJob(**d, validate_toml=validate_toml)


class IndivRecipeJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'IndivRecipeJob':
        return IndivRecipeJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'IndivRecipeJob':
        d['entity'] = IndivRecipe.load(d['entity'])
        return IndivRecipeJob(**d, validate_toml=validate_toml)


class ExperimentArtifact:
    """

    """
    def __init__(self, name, type, size, text, created, *, validate_toml=False) -> None:
        self.name = name
        self.type = type
        self.size = size
        self.text = text
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExperimentArtifact':
        return ExperimentArtifact(self.name, self.type, self.size, self.text, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExperimentArtifact':
        return ExperimentArtifact(**d, validate_toml=validate_toml)


class ExperimentArtifactSummary:
    """

    """
    def __init__(self, artifacts, user_note, location, user, *, validate_toml=False) -> None:
        self.artifacts = artifacts
        self.user_note = user_note
        self.location = location
        self.user = user

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['artifacts'] = [a.dump() for a in self.artifacts]
        return d

    def clone(self) -> 'ExperimentArtifactSummary':
        return ExperimentArtifactSummary(self.artifacts, self.user_note, self.location, self.user)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExperimentArtifactSummary':
        d['artifacts'] = [ExperimentArtifact.load(a) for a in d['artifacts']]
        return ExperimentArtifactSummary(**d, validate_toml=validate_toml)


class ArtifactsExportJob:
    """

    """
    def __init__(self, progress, status, error, message, model_key, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.model_key = model_key
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ArtifactsExportJob':
        return ArtifactsExportJob(self.progress, self.status, self.error, self.message, self.model_key, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ArtifactsExportJob':
        return ArtifactsExportJob(**d, validate_toml=validate_toml)


class ExemplarRowsResponse:
    """

    """
    def __init__(self, exemplar_id, headers, rows, totalRows, *, validate_toml=False) -> None:
        self.exemplar_id = exemplar_id
        self.headers = headers
        self.rows = rows
        self.totalRows = totalRows

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExemplarRowsResponse':
        return ExemplarRowsResponse(self.exemplar_id, self.headers, self.rows, self.totalRows)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExemplarRowsResponse':
        return ExemplarRowsResponse(**d, validate_toml=validate_toml)


class ConfigItem:
    """

    """
    def __init__(self, name, description, comment, type, val, predefined, tags, min_, max_, category, gui_category, gui_subcategory, gui_subcategory_section, gui_filtering_tags, *, validate_toml=False) -> None:
        self.name = name
        self.description = description
        self.comment = comment
        self.type = type
        self.val = val
        self.predefined = predefined
        self.tags = tags
        self.min_ = min_
        self.max_ = max_
        self.category = category
        self.gui_category = gui_category
        self.gui_subcategory = gui_subcategory
        self.gui_subcategory_section = gui_subcategory_section
        self.gui_filtering_tags = gui_filtering_tags

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ConfigItem':
        return ConfigItem(self.name, self.description, self.comment, self.type, self.val, self.predefined, self.tags, self.min_, self.max_, self.category, self.gui_category, self.gui_subcategory, self.gui_subcategory_section, self.gui_filtering_tags)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ConfigItem':
        return ConfigItem(**d, validate_toml=validate_toml)


class ConfigOption:
    """

    """
    def __init__(self, key, value, type, comment, desc, exposed, protected, enum, min, max, tags, *, validate_toml=False) -> None:
        self.key = key
        self.value = value
        self.type = type
        self.comment = comment
        self.desc = desc
        self.exposed = exposed
        self.protected = protected
        self.enum = enum
        self.min = min
        self.max = max
        self.tags = tags

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ConfigOption':
        return ConfigOption(self.key, self.value, self.type, self.comment, self.desc, self.exposed, self.protected, self.enum, self.min, self.max, self.tags)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ConfigOption':
        return ConfigOption(**d, validate_toml=validate_toml)


class ExperimentPreviewResponse:
    """

    """
    def __init__(self, accuracy, time, interpretability, lines, should_use_gpus, *, validate_toml=False) -> None:
        self.accuracy = accuracy
        self.time = time
        self.interpretability = interpretability
        self.lines = lines
        self.should_use_gpus = should_use_gpus

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExperimentPreviewResponse':
        return ExperimentPreviewResponse(self.accuracy, self.time, self.interpretability, self.lines, self.should_use_gpus)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExperimentPreviewResponse':
        return ExperimentPreviewResponse(**d, validate_toml=validate_toml)


class ExperimentPreviewJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'ExperimentPreviewJob':
        return ExperimentPreviewJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExperimentPreviewJob':
        d['entity'] = ExperimentPreviewResponse.load(d['entity'])
        return ExperimentPreviewJob(**d, validate_toml=validate_toml)


class UserInfo:
    """

    """
    def __init__(self, name, *, validate_toml=False) -> None:
        self.name = name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'UserInfo':
        return UserInfo(self.name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'UserInfo':
        return UserInfo(**d, validate_toml=validate_toml)


class TimeSeriesSplitSuggestion:
    """

    """
    def __init__(self, period_ticks, gap_ticks, train_values, valid_values, alpha_values, train_samples, valid_samples, gapped_samples, total_periods, period_size, period_units, default_unit, threshold, test_gap, test_periods, frequency, frequency_unit, *, validate_toml=False) -> None:
        self.period_ticks = period_ticks
        self.gap_ticks = gap_ticks
        self.train_values = train_values
        self.valid_values = valid_values
        self.alpha_values = alpha_values
        self.train_samples = train_samples
        self.valid_samples = valid_samples
        self.gapped_samples = gapped_samples
        self.total_periods = total_periods
        self.period_size = period_size
        self.period_units = period_units
        self.default_unit = default_unit
        self.threshold = threshold
        self.test_gap = test_gap
        self.test_periods = test_periods
        self.frequency = frequency
        self.frequency_unit = frequency_unit

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TimeSeriesSplitSuggestion':
        return TimeSeriesSplitSuggestion(self.period_ticks, self.gap_ticks, self.train_values, self.valid_values, self.alpha_values, self.train_samples, self.valid_samples, self.gapped_samples, self.total_periods, self.period_size, self.period_units, self.default_unit, self.threshold, self.test_gap, self.test_periods, self.frequency, self.frequency_unit)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TimeSeriesSplitSuggestion':
        return TimeSeriesSplitSuggestion(**d, validate_toml=validate_toml)


class TimeSeriesSplitSuggestionJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'TimeSeriesSplitSuggestionJob':
        return TimeSeriesSplitSuggestionJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TimeSeriesSplitSuggestionJob':
        d['entity'] = TimeSeriesSplitSuggestion.load(d['entity'])
        return TimeSeriesSplitSuggestionJob(**d, validate_toml=validate_toml)


class AwsCredentials:
    """
    API for Mojo scorer deployment.
    Credentials for the AWS account to be used for the deployment.

    :param take_from_config: If true, the keys from the config file are used.
    """
    def __init__(self, take_from_config, access_key, secret_key, *, validate_toml=False) -> None:
        self.take_from_config = take_from_config
        self.access_key = access_key
        self.secret_key = secret_key

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AwsCredentials':
        return AwsCredentials(self.take_from_config, self.access_key, self.secret_key)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AwsCredentials':
        return AwsCredentials(**d, validate_toml=validate_toml)


class AwsLambdaParameters:
    """
    Parameters specific for the AWS lambda deployment.

    :param region: AWS region to deploy to.
    :param deployment_name: Unique deployment id. The id is used to name related AWS objects required by the lambda.
    """
    def __init__(self, region, deployment_name, *, validate_toml=False) -> None:
        self.region = region
        self.deployment_name = deployment_name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AwsLambdaParameters':
        return AwsLambdaParameters(self.region, self.deployment_name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AwsLambdaParameters':
        return AwsLambdaParameters(**d, validate_toml=validate_toml)


class LocalRestScorerParameters:
    """
    Parameters specific for local rest scorer deployed in DAI environment

    :param deployment_name: Unique deployment id
    :param port: Port number on which the rest server will be exposed on, default is 8080
    :param heap_size: Max heap size for jvm in GB, should be an integer, ex. 4
    """
    def __init__(self, deployment_name, port, heap_size, *, validate_toml=False) -> None:
        self.deployment_name = deployment_name
        self.port = port
        self.heap_size = heap_size

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'LocalRestScorerParameters':
        return LocalRestScorerParameters(self.deployment_name, self.port, self.heap_size)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'LocalRestScorerParameters':
        return LocalRestScorerParameters(**d, validate_toml=validate_toml)


class ScorerEndpoint:
    """

    :param base_url: Resulting root URL for the scorer API requests.
    :param api_key: Api key required by the scorer API. For AWS deployments, pass this in the x-api-key HTTP header.
    :param model_key: unique model hash from mojo. For local rest scorer deployments.
    """
    def __init__(self, base_url, api_key, model_key, *, validate_toml=False) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model_key = model_key

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ScorerEndpoint':
        return ScorerEndpoint(self.base_url, self.api_key, self.model_key)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ScorerEndpoint':
        return ScorerEndpoint(**d, validate_toml=validate_toml)


class Deployment:
    """
    Represents one of the supported scorer deployment types

    :param key: Unique name of this deployment.
    :param model: Reference to the model this deployment represents.
    :param type: Determines on of the supported deployment types, e.g., AWS_LAMBDA.
    :param status: Status of the deployment, e.g., RUNNING, STOPPED.
    :param parameters: Serialized parameters fro the deployment, e.g., AwsLambdaParameters.
    :param credentials: Serialized credentials for the deployment provider, e.g., AwsCredentials.
    :param endpoint: Connection info for the deployment endpoint.
    :param pid: Process ID for deployments running locally.
    """
    def __init__(self, key, model, type, status, parameters, credentials, endpoint, pid, *, validate_toml=False) -> None:
        self.key = key
        self.model = model
        self.type = type
        self.status = status
        self.parameters = parameters
        self.credentials = credentials
        self.endpoint = endpoint
        self.pid = pid

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['model'] = self.model.dump()
        d['endpoint'] = self.endpoint.dump()
        return d

    def clone(self) -> 'Deployment':
        return Deployment(self.key, self.model, self.type, self.status, self.parameters, self.credentials, self.endpoint, self.pid)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Deployment':
        d['model'] = ModelReference.load(d['model'])
        d['endpoint'] = ScorerEndpoint.load(d['endpoint'])
        return Deployment(**d, validate_toml=validate_toml)


class CreateDeploymentJob:
    """

    :param entity: On success, holds the definition of the deployment.
    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'CreateDeploymentJob':
        return CreateDeploymentJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CreateDeploymentJob':
        d['entity'] = Deployment.load(d['entity'])
        return CreateDeploymentJob(**d, validate_toml=validate_toml)


class DestroyDeploymentJob:
    """

    """
    def __init__(self, progress, status, error, message, deployment_key, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.deployment_key = deployment_key
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DestroyDeploymentJob':
        return DestroyDeploymentJob(self.progress, self.status, self.error, self.message, self.deployment_key, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DestroyDeploymentJob':
        return DestroyDeploymentJob(**d, validate_toml=validate_toml)


class ListDeploymentQueryResponse:
    """

    """
    def __init__(self, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['items'] = [a.dump() for a in self.items]
        return d

    def clone(self) -> 'ListDeploymentQueryResponse':
        return ListDeploymentQueryResponse(self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListDeploymentQueryResponse':
        d['items'] = [Deployment.load(a) for a in d['items']]
        return ListDeploymentQueryResponse(**d, validate_toml=validate_toml)


class ListModelDiagnosticQueryResponse:
    """

    """
    def __init__(self, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['items'] = [a.dump() for a in self.items]
        return d

    def clone(self) -> 'ListModelDiagnosticQueryResponse':
        return ListModelDiagnosticQueryResponse(self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListModelDiagnosticQueryResponse':
        d['items'] = [ModelDiagnosticJob.load(a) for a in d['items']]
        return ListModelDiagnosticQueryResponse(**d, validate_toml=validate_toml)


class ModelDiagnosticJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, training_duration, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.training_duration = training_duration

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'ModelDiagnosticJob':
        return ModelDiagnosticJob(self.progress, self.status, self.error, self.message, self.entity, self.created, self.training_duration)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelDiagnosticJob':
        d['entity'] = ModelDiagnostic.load(d['entity'])
        return ModelDiagnosticJob(**d, validate_toml=validate_toml)


class ModelScore:
    """

    """
    def __init__(self, model_key, score_f_name, score, score_mean, score_sd, *, validate_toml=False) -> None:
        self.model_key = model_key
        self.score_f_name = score_f_name
        self.score = score
        self.score_mean = score_mean
        self.score_sd = score_sd

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ModelScore':
        return ModelScore(self.model_key, self.score_f_name, self.score, self.score_mean, self.score_sd)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelScore':
        return ModelScore(**d, validate_toml=validate_toml)


class ModelDiagnostic:
    """

    """
    def __init__(self, key, name, model, dataset, preds_csv_path, roc, gains, act_vs_pred, residual_plot, residual_loess, residual_hist, scores, scoring_duration, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.model = model
        self.dataset = dataset
        self.preds_csv_path = preds_csv_path
        self.roc = roc
        self.gains = gains
        self.act_vs_pred = act_vs_pred
        self.residual_plot = residual_plot
        self.residual_loess = residual_loess
        self.residual_hist = residual_hist
        self.scores = scores
        self.scoring_duration = scoring_duration

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['model'] = self.model.dump()
        d['dataset'] = self.dataset.dump()
        d['roc'] = self.roc.dump()
        d['gains'] = self.gains.dump()
        d['act_vs_pred'] = self.act_vs_pred.dump()
        d['residual_plot'] = self.residual_plot.dump()
        d['residual_loess'] = self.residual_loess.dump()
        d['residual_hist'] = self.residual_hist.dump()
        d['scores'] = [a.dump() for a in self.scores]
        return d

    def clone(self) -> 'ModelDiagnostic':
        return ModelDiagnostic(self.key, self.name, self.model, self.dataset, self.preds_csv_path, self.roc, self.gains, self.act_vs_pred, self.residual_plot, self.residual_loess, self.residual_hist, self.scores, self.scoring_duration)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelDiagnostic':
        d['model'] = ModelReference.load(d['model'])
        d['dataset'] = DatasetReference.load(d['dataset'])
        d['roc'] = ROC.load(d['roc'])
        d['gains'] = GainLift.load(d['gains'])
        d['act_vs_pred'] = H2OPlot.load(d['act_vs_pred'])
        d['residual_plot'] = H2OPlot.load(d['residual_plot'])
        d['residual_loess'] = H2ORegression.load(d['residual_loess'])
        d['residual_hist'] = ResidualHistogram.load(d['residual_hist'])
        d['scores'] = [ModelScore.load(a) for a in d['scores']]
        return ModelDiagnostic(**d, validate_toml=validate_toml)


class ResidualHistogram:
    """

    """
    def __init__(self, ticks, counts, mean, std, *, validate_toml=False) -> None:
        self.ticks = ticks
        self.counts = counts
        self.mean = mean
        self.std = std

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ResidualHistogram':
        return ResidualHistogram(self.ticks, self.counts, self.mean, self.std)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ResidualHistogram':
        return ResidualHistogram(**d, validate_toml=validate_toml)


class Project:
    """

    """
    def __init__(self, key, name, description, train_datasets, test_datasets, validation_datasets, experiments, status, created, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.description = description
        self.train_datasets = train_datasets
        self.test_datasets = test_datasets
        self.validation_datasets = validation_datasets
        self.experiments = experiments
        self.status = status
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Project':
        return Project(self.key, self.name, self.description, self.train_datasets, self.test_datasets, self.validation_datasets, self.experiments, self.status, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Project':
        return Project(**d, validate_toml=validate_toml)


class ListProjectQueryResponse:
    """

    """
    def __init__(self, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['items'] = [a.dump() for a in self.items]
        return d

    def clone(self) -> 'ListProjectQueryResponse':
        return ListProjectQueryResponse(self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListProjectQueryResponse':
        d['items'] = [Project.load(a) for a in d['items']]
        return ListProjectQueryResponse(**d, validate_toml=validate_toml)


class ProjectSummary:
    """

    """
    def __init__(self, key, name, description, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.description = description

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ProjectSummary':
        return ProjectSummary(self.key, self.name, self.description)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ProjectSummary':
        return ProjectSummary(**d, validate_toml=validate_toml)


class ListStorageProjectQueryResponse:
    """

    """
    def __init__(self, projects, *, validate_toml=False) -> None:
        self.projects = projects

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['projects'] = [a.dump() for a in self.projects]
        return d

    def clone(self) -> 'ListStorageProjectQueryResponse':
        return ListStorageProjectQueryResponse(self.projects)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListStorageProjectQueryResponse':
        d['projects'] = [ProjectSummary.load(a) for a in d['projects']]
        return ListStorageProjectQueryResponse(**d, validate_toml=validate_toml)


class ListProjectExperimentsResponse:
    """

    """
    def __init__(self, model_summaries, *, validate_toml=False) -> None:
        self.model_summaries = model_summaries

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['model_summaries'] = [a.dump() for a in self.model_summaries]
        return d

    def clone(self) -> 'ListProjectExperimentsResponse':
        return ListProjectExperimentsResponse(self.model_summaries)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListProjectExperimentsResponse':
        d['model_summaries'] = [ModelSummaryForProject.load(a) for a in d['model_summaries']]
        return ListProjectExperimentsResponse(**d, validate_toml=validate_toml)


class ModelSummaryWithDiagnostics:
    """

    """
    def __init__(self, summary, diagnostics, *, validate_toml=False) -> None:
        self.summary = summary
        self.diagnostics = diagnostics

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['summary'] = self.summary.dump()
        d['diagnostics'] = [a.dump() for a in self.diagnostics]
        return d

    def clone(self) -> 'ModelSummaryWithDiagnostics':
        return ModelSummaryWithDiagnostics(self.summary, self.diagnostics)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelSummaryWithDiagnostics':
        d['summary'] = ModelSummary.load(d['summary'])
        d['diagnostics'] = [ModelDiagnostic.load(a) for a in d['diagnostics']]
        return ModelSummaryWithDiagnostics(**d, validate_toml=validate_toml)


class ModelSummaryForProject:
    """
    Represents one Model and its diagnostics for the use in Project views.

    :param local: True if the model is available locally project.
    :param remote: True if the model is available remotely in Storage and is linked in the project.
    """
    def __init__(self, summary, diagnostics, local, remote, tags, *, validate_toml=False) -> None:
        self.summary = summary
        self.diagnostics = diagnostics
        self.local = local
        self.remote = remote
        self.tags = tags

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['summary'] = self.summary.dump()
        d['diagnostics'] = [a.dump() for a in self.diagnostics]
        return d

    def clone(self) -> 'ModelSummaryForProject':
        return ModelSummaryForProject(self.summary, self.diagnostics, self.local, self.remote, self.tags)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ModelSummaryForProject':
        d['summary'] = ModelSummary.load(d['summary'])
        d['diagnostics'] = [ModelDiagnostic.load(a) for a in d['diagnostics']]
        return ModelSummaryForProject(**d, validate_toml=validate_toml)


class DatasetSplitJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DatasetSplitJob':
        return DatasetSplitJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetSplitJob':
        return DatasetSplitJob(**d, validate_toml=validate_toml)


class DatasetMergeJob:
    """

    """
    def __init__(self, progress, status, error, message, merge_dataset, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.merge_dataset = merge_dataset
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DatasetMergeJob':
        return DatasetMergeJob(self.progress, self.status, self.error, self.message, self.merge_dataset, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DatasetMergeJob':
        return DatasetMergeJob(**d, validate_toml=validate_toml)


class CreateCsvJob:
    """

    """
    def __init__(self, status, url, *, validate_toml=False) -> None:
        self.status = status
        self.url = url

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['status'] = self.status.dump()
        return d

    def clone(self) -> 'CreateCsvJob':
        return CreateCsvJob(self.status, self.url)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CreateCsvJob':
        d['status'] = JobStatus.load(d['status'])
        return CreateCsvJob(**d, validate_toml=validate_toml)


class CustomRecipeJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'CustomRecipeJob':
        return CustomRecipeJob(self.progress, self.status, self.error, self.message, self.entity, self.created)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CustomRecipeJob':
        d['entity'] = CustomRecipe.load(d['entity'])
        return CustomRecipeJob(**d, validate_toml=validate_toml)


class CustomRecipe:
    """

    :param type: transformers | models | scorers | data | explainer | individuals
    :param models: Freshly added model estimators
    :param scorers: Freshly added scorers
    :param transformers: Freshly added transformers
    :param data_files: Freshly created dataset files
    :param pretransformers: Freshly added pretransformers
    :param datas: Freshly added data recipes
    :param explainers: Freshly created MLI explainers
    :param individuals: Freshly added individuals
    """
    def __init__(self, key, name, fpath, url, data_file, type, models, scorers, transformers, data_files, pretransformers, datas, explainers, individuals, deactivated_recipes, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.fpath = fpath
        self.url = url
        self.data_file = data_file
        self.type = type
        self.models = models
        self.scorers = scorers
        self.transformers = transformers
        self.data_files = data_files
        self.pretransformers = pretransformers
        self.datas = datas
        self.explainers = explainers
        self.individuals = individuals
        self.deactivated_recipes = deactivated_recipes

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['models'] = [a.dump() for a in self.models]
        d['scorers'] = [a.dump() for a in self.scorers]
        d['transformers'] = [a.dump() for a in self.transformers]
        d['pretransformers'] = [a.dump() for a in self.pretransformers]
        d['datas'] = [a.dump() for a in self.datas]
        d['explainers'] = [a.dump() for a in self.explainers]
        d['individuals'] = [a.dump() for a in self.individuals]
        d['deactivated_recipes'] = [a.dump() for a in self.deactivated_recipes]
        return d

    def clone(self) -> 'CustomRecipe':
        return CustomRecipe(self.key, self.name, self.fpath, self.url, self.data_file, self.type, self.models, self.scorers, self.transformers, self.data_files, self.pretransformers, self.datas, self.explainers, self.individuals, self.deactivated_recipes)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CustomRecipe':
        d['models'] = [ModelEstimatorWrapper.load(a) for a in d['models']]
        d['scorers'] = [ScorerWrapper.load(a) for a in d['scorers']]
        d['transformers'] = [TransformerWrapper.load(a) for a in d['transformers']]
        d['pretransformers'] = [PreTransformerWrapper.load(a) for a in d['pretransformers']]
        d['datas'] = [DataWrapper.load(a) for a in d['datas']]
        d['explainers'] = [ExplainerDescriptor.load(a) for a in d['explainers']]
        d['individuals'] = [IndividualWrapper.load(a) for a in d['individuals']]
        d['deactivated_recipes'] = [PersistentCustomRecipe.load(a) for a in d['deactivated_recipes']]
        return CustomRecipe(**d, validate_toml=validate_toml)


class OriginalShapleyJob:
    """
    Original Shapley

    """
    def __init__(self, mli_key, progress, status, error, message, entity, created, training_duration, *, validate_toml=False) -> None:
        self.mli_key = mli_key
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.training_duration = training_duration

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'OriginalShapleyJob':
        return OriginalShapleyJob(self.mli_key, self.progress, self.status, self.error, self.message, self.entity, self.created, self.training_duration)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'OriginalShapleyJob':
        d['entity'] = OriginalShapley.load(d['entity'])
        return OriginalShapleyJob(**d, validate_toml=validate_toml)


class OriginalShapley:
    """

    """
    def __init__(self, key, name, mli_key, shapley_orig_rc_csv_path, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.mli_key = mli_key
        self.shapley_orig_rc_csv_path = shapley_orig_rc_csv_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'OriginalShapley':
        return OriginalShapley(self.key, self.name, self.mli_key, self.shapley_orig_rc_csv_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'OriginalShapley':
        return OriginalShapley(**d, validate_toml=validate_toml)


class OriginalShapleyParameters:
    """

    """
    def __init__(self, model_key, mli_key, orig_shap_key, config_overrides, model_path, tmp_dir_path, dataset_path, mli_dir_path, classes, intr_params, orig_shap_entity, mojo_zip_path, wait_for_mojo, labels, actual_col, id_cols, *, validate_toml=False) -> None:
        self.model_key = model_key
        self.mli_key = mli_key
        self.orig_shap_key = orig_shap_key
        self.config_overrides = config_overrides
        self.model_path = model_path
        self.tmp_dir_path = tmp_dir_path
        self.dataset_path = dataset_path
        self.mli_dir_path = mli_dir_path
        self.classes = classes
        self.intr_params = intr_params
        self.orig_shap_entity = orig_shap_entity
        self.mojo_zip_path = mojo_zip_path
        self.wait_for_mojo = wait_for_mojo
        self.labels = labels
        self.actual_col = actual_col
        self.id_cols = id_cols
        if validate_toml:
            validation.validate_toml(config_overrides, 'config_overrides')

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['intr_params'] = self.intr_params.dump()
        d['orig_shap_entity'] = self.orig_shap_entity.dump()
        return d

    def clone(self) -> 'OriginalShapleyParameters':
        return OriginalShapleyParameters(self.model_key, self.mli_key, self.orig_shap_key, self.config_overrides, self.model_path, self.tmp_dir_path, self.dataset_path, self.mli_dir_path, self.classes, self.intr_params, self.orig_shap_entity, self.mojo_zip_path, self.wait_for_mojo, self.labels, self.actual_col, self.id_cols)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'OriginalShapleyParameters':
        d['intr_params'] = InterpretParameters.load(d['intr_params'])
        d['orig_shap_entity'] = OriginalShapley.load(d['orig_shap_entity'])
        return OriginalShapleyParameters(**d, validate_toml=validate_toml)


class DecisionTreeSurrogateJob:
    """
    Decision Tree Surrogate Model for MLI

    """
    def __init__(self, mli_key, progress, status, error, message, entity, created, training_duration, *, validate_toml=False) -> None:
        self.mli_key = mli_key
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.training_duration = training_duration

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'DecisionTreeSurrogateJob':
        return DecisionTreeSurrogateJob(self.mli_key, self.progress, self.status, self.error, self.message, self.entity, self.created, self.training_duration)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DecisionTreeSurrogateJob':
        d['entity'] = DecisionTreeSurrogate.load(d['entity'])
        return DecisionTreeSurrogateJob(**d, validate_toml=validate_toml)


class DecisionTreeSurrogate:
    """

    """
    def __init__(self, key, name, mli_key, dt_rules_zip_path, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.mli_key = mli_key
        self.dt_rules_zip_path = dt_rules_zip_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DecisionTreeSurrogate':
        return DecisionTreeSurrogate(self.key, self.name, self.mli_key, self.dt_rules_zip_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DecisionTreeSurrogate':
        return DecisionTreeSurrogate(**d, validate_toml=validate_toml)


class DecisionTreeSurrogateParameters:
    """

    """
    def __init__(self, model_key, mli_key, dt_surrogate_key, config_overrides, model_path, tmp_dir_path, dataset_path, mli_dir_path, classes, intr_params, dt_surrogate_entity, mojo_zip_path, wait_for_mojo, labels, actual_col, predict_col, weights_col, dropped_cols, qbin_cols, qbin_count, debug_model_errors, debug_model_errors_class, unfitted_pipeline_path, cat_encoder, *, validate_toml=False) -> None:
        self.model_key = model_key
        self.mli_key = mli_key
        self.dt_surrogate_key = dt_surrogate_key
        self.config_overrides = config_overrides
        self.model_path = model_path
        self.tmp_dir_path = tmp_dir_path
        self.dataset_path = dataset_path
        self.mli_dir_path = mli_dir_path
        self.classes = classes
        self.intr_params = intr_params
        self.dt_surrogate_entity = dt_surrogate_entity
        self.mojo_zip_path = mojo_zip_path
        self.wait_for_mojo = wait_for_mojo
        self.labels = labels
        self.actual_col = actual_col
        self.predict_col = predict_col
        self.weights_col = weights_col
        self.dropped_cols = dropped_cols
        self.qbin_cols = qbin_cols
        self.qbin_count = qbin_count
        self.debug_model_errors = debug_model_errors
        self.debug_model_errors_class = debug_model_errors_class
        self.unfitted_pipeline_path = unfitted_pipeline_path
        self.cat_encoder = cat_encoder
        if validate_toml:
            validation.validate_toml(config_overrides, 'config_overrides')

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['intr_params'] = self.intr_params.dump()
        d['dt_surrogate_entity'] = self.dt_surrogate_entity.dump()
        return d

    def clone(self) -> 'DecisionTreeSurrogateParameters':
        return DecisionTreeSurrogateParameters(self.model_key, self.mli_key, self.dt_surrogate_key, self.config_overrides, self.model_path, self.tmp_dir_path, self.dataset_path, self.mli_dir_path, self.classes, self.intr_params, self.dt_surrogate_entity, self.mojo_zip_path, self.wait_for_mojo, self.labels, self.actual_col, self.predict_col, self.weights_col, self.dropped_cols, self.qbin_cols, self.qbin_count, self.debug_model_errors, self.debug_model_errors_class, self.unfitted_pipeline_path, self.cat_encoder)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DecisionTreeSurrogateParameters':
        d['intr_params'] = InterpretParameters.load(d['intr_params'])
        d['dt_surrogate_entity'] = DecisionTreeSurrogate.load(d['dt_surrogate_entity'])
        return DecisionTreeSurrogateParameters(**d, validate_toml=validate_toml)


class DisparateImpactAnalysisJob:
    """
    DISPARATE IMPACT ANALYSIS

    """
    def __init__(self, mli_key, progress, status, error, message, entity, created, training_duration, *, validate_toml=False) -> None:
        self.mli_key = mli_key
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.training_duration = training_duration

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'DisparateImpactAnalysisJob':
        return DisparateImpactAnalysisJob(self.mli_key, self.progress, self.status, self.error, self.message, self.entity, self.created, self.training_duration)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DisparateImpactAnalysisJob':
        d['entity'] = DisparateImpactAnalysis.load(d['entity'])
        return DisparateImpactAnalysisJob(**d, validate_toml=validate_toml)


class DisparateImpactAnalysis:
    """

    :param global_conf_matrix: binomial
    """
    def __init__(self, key, name, mli_key, path, problem_type, summary, feature_summaries, global_conf_matrix, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.mli_key = mli_key
        self.path = path
        self.problem_type = problem_type
        self.summary = summary
        self.feature_summaries = feature_summaries
        self.global_conf_matrix = global_conf_matrix

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['summary'] = self.summary.dump()
        d['feature_summaries'] = [a.dump() for a in self.feature_summaries]
        d['global_conf_matrix'] = self.global_conf_matrix.dump()
        return d

    def clone(self) -> 'DisparateImpactAnalysis':
        return DisparateImpactAnalysis(self.key, self.name, self.mli_key, self.path, self.problem_type, self.summary, self.feature_summaries, self.global_conf_matrix)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DisparateImpactAnalysis':
        d['summary'] = DisparateImpactAnalysisSummary.load(d['summary'])
        d['feature_summaries'] = [DisparateImpactAnalysisFeatureSummary.load(a) for a in d['feature_summaries']]
        d['global_conf_matrix'] = DisparateImpactAnalysisNumericTable.load(d['global_conf_matrix'])
        return DisparateImpactAnalysis(**d, validate_toml=validate_toml)


class DisparateImpactAnalysisSummary:
    """

    :param max_metric: binomial
    :param cut_off: binomial
    :param rmse: regression
    :param r2: regression
    """
    def __init__(self, max_metric, cut_off, rmse, r2, *, validate_toml=False) -> None:
        self.max_metric = max_metric
        self.cut_off = cut_off
        self.rmse = rmse
        self.r2 = r2

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DisparateImpactAnalysisSummary':
        return DisparateImpactAnalysisSummary(self.max_metric, self.cut_off, self.rmse, self.r2)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DisparateImpactAnalysisSummary':
        return DisparateImpactAnalysisSummary(**d, validate_toml=validate_toml)


class DisparateImpactAnalysisFeatureSummary:
    """

    """
    def __init__(self, feature_name, ref_levels, *, validate_toml=False) -> None:
        self.feature_name = feature_name
        self.ref_levels = ref_levels

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['feature_name'] = self.feature_name.dump()
        return d

    def clone(self) -> 'DisparateImpactAnalysisFeatureSummary':
        return DisparateImpactAnalysisFeatureSummary(self.feature_name, self.ref_levels)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DisparateImpactAnalysisFeatureSummary':
        d['feature_name'] = BoolEntry.load(d['feature_name'])
        return DisparateImpactAnalysisFeatureSummary(**d, validate_toml=validate_toml)


class DisparateImpactAnalysisNumericTable:
    """

    """
    def __init__(self, name, col_names, row_names, values, *, validate_toml=False) -> None:
        self.name = name
        self.col_names = col_names
        self.row_names = row_names
        self.values = values

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DisparateImpactAnalysisNumericTable':
        return DisparateImpactAnalysisNumericTable(self.name, self.col_names, self.row_names, self.values)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DisparateImpactAnalysisNumericTable':
        return DisparateImpactAnalysisNumericTable(**d, validate_toml=validate_toml)


class DiaSummary:
    """
    Disparate Impact Analysis Summary Domain Object

    """
    def __init__(self, dia_features, mli_key, dia_key, problem_type, global_confusion_matrix, *, validate_toml=False) -> None:
        self.dia_features = dia_features
        self.mli_key = mli_key
        self.dia_key = dia_key
        self.problem_type = problem_type
        self.global_confusion_matrix = global_confusion_matrix

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['dia_features'] = [a.dump() for a in self.dia_features]
        d['global_confusion_matrix'] = self.global_confusion_matrix.dump()
        return d

    def clone(self) -> 'DiaSummary':
        return DiaSummary(self.dia_features, self.mli_key, self.dia_key, self.problem_type, self.global_confusion_matrix)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaSummary':
        d['dia_features'] = [BoolEntry.load(a) for a in d['dia_features']]
        d['global_confusion_matrix'] = DiaMatrix.load(d['global_confusion_matrix'])
        return DiaSummary(**d, validate_toml=validate_toml)


class DiaAvp:
    """
    Disparate Impact Analysis AvP Domain Object

    """
    def __init__(self, category_summary, metrics, avp, *, validate_toml=False) -> None:
        self.category_summary = category_summary
        self.metrics = metrics
        self.avp = avp

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['category_summary'] = [a.dump() for a in self.category_summary]
        d['metrics'] = [a.dump() for a in self.metrics]
        d['avp'] = [a.dump() for a in self.avp]
        return d

    def clone(self) -> 'DiaAvp':
        return DiaAvp(self.category_summary, self.metrics, self.avp)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaAvp':
        d['category_summary'] = [DiaCategorySummary.load(a) for a in d['category_summary']]
        d['metrics'] = [DiaMetric.load(a) for a in d['metrics']]
        d['avp'] = [DiaAvpEntry.load(a) for a in d['avp']]
        return DiaAvp(**d, validate_toml=validate_toml)


class DiaCategorySummary:
    """

    """
    def __init__(self, name, count, value, *, validate_toml=False) -> None:
        self.name = name
        self.count = count
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DiaCategorySummary':
        return DiaCategorySummary(self.name, self.count, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaCategorySummary':
        return DiaCategorySummary(**d, validate_toml=validate_toml)


class DiaMetric:
    """

    """
    def __init__(self, name, levels, *, validate_toml=False) -> None:
        self.name = name
        self.levels = levels

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['levels'] = [a.dump() for a in self.levels]
        return d

    def clone(self) -> 'DiaMetric':
        return DiaMetric(self.name, self.levels)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaMetric':
        d['levels'] = [FloatEntry.load(a) for a in d['levels']]
        return DiaMetric(**d, validate_toml=validate_toml)


class DiaAvpEntry:
    """

    """
    def __init__(self, actual, predicted, category, *, validate_toml=False) -> None:
        self.actual = actual
        self.predicted = predicted
        self.category = category

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DiaAvpEntry':
        return DiaAvpEntry(self.actual, self.predicted, self.category)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaAvpEntry':
        return DiaAvpEntry(**d, validate_toml=validate_toml)


class Dia:
    """
    Disparate Impact Analysis Domain Object

    """
    def __init__(self, summary, confusion_matrices, group_metrics, group_disparity, group_me_smd, group_parity, current_page, max_rows, *, validate_toml=False) -> None:
        self.summary = summary
        self.confusion_matrices = confusion_matrices
        self.group_metrics = group_metrics
        self.group_disparity = group_disparity
        self.group_me_smd = group_me_smd
        self.group_parity = group_parity
        self.current_page = current_page
        self.max_rows = max_rows

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['summary'] = self.summary.dump()
        d['confusion_matrices'] = [a.dump() for a in self.confusion_matrices]
        d['group_metrics'] = self.group_metrics.dump()
        d['group_disparity'] = [a.dump() for a in self.group_disparity]
        d['group_me_smd'] = [a.dump() for a in self.group_me_smd]
        d['group_parity'] = [a.dump() for a in self.group_parity]
        return d

    def clone(self) -> 'Dia':
        return Dia(self.summary, self.confusion_matrices, self.group_metrics, self.group_disparity, self.group_me_smd, self.group_parity, self.current_page, self.max_rows)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Dia':
        d['summary'] = DiaFeatureSummary.load(d['summary'])
        d['confusion_matrices'] = [DiaNamedMatrix.load(a) for a in d['confusion_matrices']]
        d['group_metrics'] = DiaMatrix.load(d['group_metrics'])
        d['group_disparity'] = [DiaNamedMatrix.load(a) for a in d['group_disparity']]
        d['group_me_smd'] = [DiaNamedMatrix.load(a) for a in d['group_me_smd']]
        d['group_parity'] = [DiaNamedMatrix.load(a) for a in d['group_parity']]
        return Dia(**d, validate_toml=validate_toml)


class DiaNamedMatrix:
    """

    """
    def __init__(self, name, matrix, *, validate_toml=False) -> None:
        self.name = name
        self.matrix = matrix

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['matrix'] = self.matrix.dump()
        return d

    def clone(self) -> 'DiaNamedMatrix':
        return DiaNamedMatrix(self.name, self.matrix)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaNamedMatrix':
        d['matrix'] = DiaMatrix.load(d['matrix'])
        return DiaNamedMatrix(**d, validate_toml=validate_toml)


class DiaFeatureSummary:
    """

    """
    def __init__(self, dia_experiment, maximized_metric, cut_off, rmse, r2, ref_levels, *, validate_toml=False) -> None:
        self.dia_experiment = dia_experiment
        self.maximized_metric = maximized_metric
        self.cut_off = cut_off
        self.rmse = rmse
        self.r2 = r2
        self.ref_levels = ref_levels

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DiaFeatureSummary':
        return DiaFeatureSummary(self.dia_experiment, self.maximized_metric, self.cut_off, self.rmse, self.r2, self.ref_levels)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaFeatureSummary':
        return DiaFeatureSummary(**d, validate_toml=validate_toml)


class DiaMatrix:
    """

    """
    def __init__(self, matrix, *, validate_toml=False) -> None:
        self.matrix = matrix

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['matrix'] = [a.dump() for a in self.matrix]
        return d

    def clone(self) -> 'DiaMatrix':
        return DiaMatrix(self.matrix)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaMatrix':
        d['matrix'] = [DiaTableRow.load(a) for a in d['matrix']]
        return DiaMatrix(**d, validate_toml=validate_toml)


class DiaTableRow:
    """

    """
    def __init__(self, values, *, validate_toml=False) -> None:
        self.values = values

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['values'] = [a.dump() for a in self.values]
        return d

    def clone(self) -> 'DiaTableRow':
        return DiaTableRow(self.values)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaTableRow':
        d['values'] = [DiaTableColumn.load(a) for a in d['values']]
        return DiaTableRow(**d, validate_toml=validate_toml)


class DiaTableColumn:
    """

    """
    def __init__(self, col_name, col_value, *, validate_toml=False) -> None:
        self.col_name = col_name
        self.col_value = col_value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'DiaTableColumn':
        return DiaTableColumn(self.col_name, self.col_value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DiaTableColumn':
        return DiaTableColumn(**d, validate_toml=validate_toml)


class FloatEntry:
    """

    """
    def __init__(self, name, value, *, validate_toml=False) -> None:
        self.name = name
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'FloatEntry':
        return FloatEntry(self.name, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FloatEntry':
        return FloatEntry(**d, validate_toml=validate_toml)


class BoolEntry:
    """

    """
    def __init__(self, name, value, *, validate_toml=False) -> None:
        self.name = name
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'BoolEntry':
        return BoolEntry(self.name, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'BoolEntry':
        return BoolEntry(**d, validate_toml=validate_toml)


class StrEntry:
    """

    """
    def __init__(self, name, value, *, validate_toml=False) -> None:
        self.name = name
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'StrEntry':
        return StrEntry(self.name, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'StrEntry':
        return StrEntry(**d, validate_toml=validate_toml)


class StrArrayEntry:
    """

    """
    def __init__(self, name, value, *, validate_toml=False) -> None:
        self.name = name
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'StrArrayEntry':
        return StrArrayEntry(self.name, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'StrArrayEntry':
        return StrArrayEntry(**d, validate_toml=validate_toml)


class MliNlpJob:
    """
    MLI NLP

    """
    def __init__(self, mli_key, progress, status, error, message, entity, created, training_duration, *, validate_toml=False) -> None:
        self.mli_key = mli_key
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.training_duration = training_duration

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'MliNlpJob':
        return MliNlpJob(self.mli_key, self.progress, self.status, self.error, self.message, self.entity, self.created, self.training_duration)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'MliNlpJob':
        d['entity'] = MliNlp.load(d['entity'])
        return MliNlpJob(**d, validate_toml=validate_toml)


class MliNlp:
    """

    """
    def __init__(self, mli_nlp_key, mli_nlp_name, mli_key, mli_nlp_path, *, validate_toml=False) -> None:
        self.mli_nlp_key = mli_nlp_key
        self.mli_nlp_name = mli_nlp_name
        self.mli_key = mli_key
        self.mli_nlp_path = mli_nlp_path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'MliNlp':
        return MliNlp(self.mli_nlp_key, self.mli_nlp_name, self.mli_key, self.mli_nlp_path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'MliNlp':
        return MliNlp(**d, validate_toml=validate_toml)


class DataPreviewJob:
    """

    """
    def __init__(self, progress, status, error, message, created, entity, recipe_path, dataset_key, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.created = created
        self.entity = entity
        self.recipe_path = recipe_path
        self.dataset_key = dataset_key

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'DataPreviewJob':
        return DataPreviewJob(self.progress, self.status, self.error, self.message, self.created, self.entity, self.recipe_path, self.dataset_key)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DataPreviewJob':
        d['entity'] = ExemplarRowsResponse.load(d['entity'])
        return DataPreviewJob(**d, validate_toml=validate_toml)


class DisparateImpactAnalysisParameters:
    """
    Used internally for do_dia job parameters

    """
    def __init__(self, model_key, mli_key, dia_key, config_overrides, model_path, tmp_dir_path, dataset_path, mli_dir_path, classes, intr_params, dia_entity, roc, labels, cut_off, path, actual_col, predict_column, maximize_metric, use_holdout_preds, *, validate_toml=False) -> None:
        self.model_key = model_key
        self.mli_key = mli_key
        self.dia_key = dia_key
        self.config_overrides = config_overrides
        self.model_path = model_path
        self.tmp_dir_path = tmp_dir_path
        self.dataset_path = dataset_path
        self.mli_dir_path = mli_dir_path
        self.classes = classes
        self.intr_params = intr_params
        self.dia_entity = dia_entity
        self.roc = roc
        self.labels = labels
        self.cut_off = cut_off
        self.path = path
        self.actual_col = actual_col
        self.predict_column = predict_column
        self.maximize_metric = maximize_metric
        self.use_holdout_preds = use_holdout_preds
        if validate_toml:
            validation.validate_toml(config_overrides, 'config_overrides')

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['intr_params'] = self.intr_params.dump()
        d['dia_entity'] = self.dia_entity.dump()
        d['roc'] = self.roc.dump()
        return d

    def clone(self) -> 'DisparateImpactAnalysisParameters':
        return DisparateImpactAnalysisParameters(self.model_key, self.mli_key, self.dia_key, self.config_overrides, self.model_path, self.tmp_dir_path, self.dataset_path, self.mli_dir_path, self.classes, self.intr_params, self.dia_entity, self.roc, self.labels, self.cut_off, self.path, self.actual_col, self.predict_column, self.maximize_metric, self.use_holdout_preds)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'DisparateImpactAnalysisParameters':
        d['intr_params'] = InterpretParameters.load(d['intr_params'])
        d['dia_entity'] = DisparateImpactAnalysis.load(d['dia_entity'])
        d['roc'] = ROC.load(d['roc'])
        return DisparateImpactAnalysisParameters(**d, validate_toml=validate_toml)


class MliVarImpTable:
    """

    """
    def __init__(self, global_imp, local_imp, *, validate_toml=False) -> None:
        self.global_imp = global_imp
        self.local_imp = local_imp

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['global_imp'] = self.global_imp.dump()
        d['local_imp'] = self.local_imp.dump()
        return d

    def clone(self) -> 'MliVarImpTable':
        return MliVarImpTable(self.global_imp, self.local_imp)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'MliVarImpTable':
        d['global_imp'] = VarImpTable.load(d['global_imp'])
        d['local_imp'] = VarImpTable.load(d['local_imp'])
        return MliVarImpTable(**d, validate_toml=validate_toml)


class SensitivityAnalysisJob:
    """
    Sensitivity analysis fork/join job.

    """
    def __init__(self, mli_key, progress, status, error, message, entity, created, training_duration, *, validate_toml=False) -> None:
        self.mli_key = mli_key
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.training_duration = training_duration

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'SensitivityAnalysisJob':
        return SensitivityAnalysisJob(self.mli_key, self.progress, self.status, self.error, self.message, self.entity, self.created, self.training_duration)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SensitivityAnalysisJob':
        d['entity'] = SensitivityAnalysis.load(d['entity'])
        return SensitivityAnalysisJob(**d, validate_toml=validate_toml)


class SensitivityAnalysis:
    """
    Sensitivity analysis fork/join entity.

    """
    def __init__(self, key, name, mli_key, dai_key, *, validate_toml=False) -> None:
        self.key = key
        self.name = name
        self.mli_key = mli_key
        self.dai_key = dai_key

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SensitivityAnalysis':
        return SensitivityAnalysis(self.key, self.name, self.mli_key, self.dai_key)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SensitivityAnalysis':
        return SensitivityAnalysis(**d, validate_toml=validate_toml)


class SaDatasetSummary:
    """
    Sensitivity analysis dataset summary.

    """
    def __init__(self, name, size, rows, cols, types, features_meta, experiment_name, experiment_type, sampled_dataset, *, validate_toml=False) -> None:
        self.name = name
        self.size = size
        self.rows = rows
        self.cols = cols
        self.types = types
        self.features_meta = features_meta
        self.experiment_name = experiment_name
        self.experiment_type = experiment_type
        self.sampled_dataset = sampled_dataset

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['features_meta'] = [a.dump() for a in self.features_meta]
        return d

    def clone(self) -> 'SaDatasetSummary':
        return SaDatasetSummary(self.name, self.size, self.rows, self.cols, self.types, self.features_meta, self.experiment_name, self.experiment_type, self.sampled_dataset)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaDatasetSummary':
        d['features_meta'] = [SaFeatureMeta.load(a) for a in d['features_meta']]
        return SaDatasetSummary(**d, validate_toml=validate_toml)


class SaWorkingSetSummary:
    """
    Sensitivity analysis working set summary.

    """
    def __init__(self, name, size, rows, cols, types, experiment_name, experiment_type, sampled_dataset, *, validate_toml=False) -> None:
        self.name = name
        self.size = size
        self.rows = rows
        self.cols = cols
        self.types = types
        self.experiment_name = experiment_name
        self.experiment_type = experiment_type
        self.sampled_dataset = sampled_dataset

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaWorkingSetSummary':
        return SaWorkingSetSummary(self.name, self.size, self.rows, self.cols, self.types, self.experiment_name, self.experiment_type, self.sampled_dataset)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaWorkingSetSummary':
        return SaWorkingSetSummary(**d, validate_toml=validate_toml)


class SaPredsEntry:
    """
    Sensitivity analysis predictions entry. Category gives main chart color.

    """
    def __init__(self, actual, predicted, category, *, validate_toml=False) -> None:
        self.actual = actual
        self.predicted = predicted
        self.category = category

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaPredsEntry':
        return SaPredsEntry(self.actual, self.predicted, self.category)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaPredsEntry':
        return SaPredsEntry(**d, validate_toml=validate_toml)


class SaWorkingSetPreds:
    """
    Sensitivity analysis predictions.

    """
    def __init__(self, preds, *, validate_toml=False) -> None:
        self.preds = preds

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['preds'] = [a.dump() for a in self.preds]
        return d

    def clone(self) -> 'SaWorkingSetPreds':
        return SaWorkingSetPreds(self.preds)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaWorkingSetPreds':
        d['preds'] = [SaPredsEntry.load(a) for a in d['preds']]
        return SaWorkingSetPreds(**d, validate_toml=validate_toml)


class SaFeatureMeta:
    """
    Sensitivity analysis features metadata.

    """
    def __init__(self, name, type, min, max, mean, mode, sd, unique, importance, *, validate_toml=False) -> None:
        self.name = name
        self.type = type
        self.min = min
        self.max = max
        self.mean = mean
        self.mode = mode
        self.sd = sd
        self.unique = unique
        self.importance = importance

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaFeatureMeta':
        return SaFeatureMeta(self.name, self.type, self.min, self.max, self.mean, self.mode, self.sd, self.unique, self.importance)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaFeatureMeta':
        return SaFeatureMeta(**d, validate_toml=validate_toml)


class SaWorkingSetCell:
    """
    Sensitivity analysis working set (table) cell.
    TODO value:any type didn't worked (proto serializer failed) > string

    """
    def __init__(self, feature, value, *, validate_toml=False) -> None:
        self.feature = feature
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaWorkingSetCell':
        return SaWorkingSetCell(self.feature, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaWorkingSetCell':
        return SaWorkingSetCell(**d, validate_toml=validate_toml)


class SaWorkingSetRow:
    """
    Sensitivity analysis working set (table) row.

    """
    def __init__(self, index, category, cells, *, validate_toml=False) -> None:
        self.index = index
        self.category = category
        self.cells = cells

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['cells'] = [a.dump() for a in self.cells]
        return d

    def clone(self) -> 'SaWorkingSetRow':
        return SaWorkingSetRow(self.index, self.category, self.cells)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaWorkingSetRow':
        d['cells'] = [SaWorkingSetCell.load(a) for a in d['cells']]
        return SaWorkingSetRow(**d, validate_toml=validate_toml)


class SaWorkingSet:
    """
    Sensitivity analysis working set (table).

    """
    def __init__(self, frame, *, validate_toml=False) -> None:
        self.frame = frame

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['frame'] = [a.dump() for a in self.frame]
        return d

    def clone(self) -> 'SaWorkingSet':
        return SaWorkingSet(self.frame)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaWorkingSet':
        d['frame'] = [SaWorkingSetRow.load(a) for a in d['frame']]
        return SaWorkingSet(**d, validate_toml=validate_toml)


class SaShape:
    """
    Sensitivity analysis working set shape.

    """
    def __init__(self, rows, cols, *, validate_toml=False) -> None:
        self.rows = rows
        self.cols = cols

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaShape':
        return SaShape(self.rows, self.cols)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaShape':
        return SaShape(**d, validate_toml=validate_toml)


class SaStatistics:
    """
    Sensitivity analysis predictions statistics (last, absolute/relative change)

    """
    def __init__(self, score, last_score, score_change, mode_prediction, *, validate_toml=False) -> None:
        self.score = score
        self.last_score = last_score
        self.score_change = score_change
        self.mode_prediction = mode_prediction

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaStatistics':
        return SaStatistics(self.score, self.last_score, self.score_change, self.mode_prediction)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaStatistics':
        return SaStatistics(**d, validate_toml=validate_toml)


class SaHistoryItem:
    """
    Sensitivity analysis history item.

    """
    def __init__(self, idx, in_progress, action, feature, scope, value, *, validate_toml=False) -> None:
        self.idx = idx
        self.in_progress = in_progress
        self.action = action
        self.feature = feature
        self.scope = scope
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaHistoryItem':
        return SaHistoryItem(self.idx, self.in_progress, self.action, self.feature, self.scope, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaHistoryItem':
        return SaHistoryItem(**d, validate_toml=validate_toml)


class SaHistory:
    """
    Sensitivity analysis history.

    """
    def __init__(self, history, *, validate_toml=False) -> None:
        self.history = history

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['history'] = [a.dump() for a in self.history]
        return d

    def clone(self) -> 'SaHistory':
        return SaHistory(self.history)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaHistory':
        d['history'] = [SaHistoryItem.load(a) for a in d['history']]
        return SaHistory(**d, validate_toml=validate_toml)


class SaPredsHistoryChartDataPoint:
    """
    Sensitivity analysis history chart point.

    """
    def __init__(self, x, y, *, validate_toml=False) -> None:
        self.x = x
        self.y = y

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaPredsHistoryChartDataPoint':
        return SaPredsHistoryChartDataPoint(self.x, self.y)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaPredsHistoryChartDataPoint':
        return SaPredsHistoryChartDataPoint(**d, validate_toml=validate_toml)


class SaPredsHistoryChartData:
    """
    Sensitivity analysis history chart data (points).

    """
    def __init__(self, points, *, validate_toml=False) -> None:
        self.points = points

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['points'] = [a.dump() for a in self.points]
        return d

    def clone(self) -> 'SaPredsHistoryChartData':
        return SaPredsHistoryChartData(self.points)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaPredsHistoryChartData':
        d['points'] = [SaPredsHistoryChartDataPoint.load(a) for a in d['points']]
        return SaPredsHistoryChartData(**d, validate_toml=validate_toml)


class SaMainChartDataPoint:
    """
    Sensitivity analysis main chart point. Structure field names are frontend
    driven to avoid conversion: x is prediction, y is feature value, cluster is
    category.

    """
    def __init__(self, x, y, cluster, ws_row, *, validate_toml=False) -> None:
        self.x = x
        self.y = y
        self.cluster = cluster
        self.ws_row = ws_row

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'SaMainChartDataPoint':
        return SaMainChartDataPoint(self.x, self.y, self.cluster, self.ws_row)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaMainChartDataPoint':
        return SaMainChartDataPoint(**d, validate_toml=validate_toml)


class SaMainChartData:
    """
    Sensitivity analysis main chart data (points).

    """
    def __init__(self, cut_off, feature, points, *, validate_toml=False) -> None:
        self.cut_off = cut_off
        self.feature = feature
        self.points = points

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['points'] = [a.dump() for a in self.points]
        return d

    def clone(self) -> 'SaMainChartData':
        return SaMainChartData(self.cut_off, self.feature, self.points)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'SaMainChartData':
        d['points'] = [SaMainChartDataPoint.load(a) for a in d['points']]
        return SaMainChartData(**d, validate_toml=validate_toml)


class Sa:
    """
    Sensitivity analysis snapshot structure

    """
    def __init__(self, hist_entry, dataset_summary, summary_row, main_chart, preds_history_chart, working_set_summary, working_set, stats, history, *, validate_toml=False) -> None:
        self.hist_entry = hist_entry
        self.dataset_summary = dataset_summary
        self.summary_row = summary_row
        self.main_chart = main_chart
        self.preds_history_chart = preds_history_chart
        self.working_set_summary = working_set_summary
        self.working_set = working_set
        self.stats = stats
        self.history = history

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['dataset_summary'] = self.dataset_summary.dump()
        d['summary_row'] = self.summary_row.dump()
        d['main_chart'] = self.main_chart.dump()
        d['preds_history_chart'] = self.preds_history_chart.dump()
        d['working_set_summary'] = self.working_set_summary.dump()
        d['working_set'] = self.working_set.dump()
        d['stats'] = self.stats.dump()
        d['history'] = self.history.dump()
        return d

    def clone(self) -> 'Sa':
        return Sa(self.hist_entry, self.dataset_summary, self.summary_row, self.main_chart, self.preds_history_chart, self.working_set_summary, self.working_set, self.stats, self.history)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Sa':
        d['dataset_summary'] = SaDatasetSummary.load(d['dataset_summary'])
        d['summary_row'] = SaWorkingSetRow.load(d['summary_row'])
        d['main_chart'] = SaMainChartData.load(d['main_chart'])
        d['preds_history_chart'] = SaPredsHistoryChartData.load(d['preds_history_chart'])
        d['working_set_summary'] = SaWorkingSetSummary.load(d['working_set_summary'])
        d['working_set'] = SaWorkingSet.load(d['working_set'])
        d['stats'] = SaStatistics.load(d['stats'])
        d['history'] = SaHistory.load(d['history'])
        return Sa(**d, validate_toml=validate_toml)


class Task:
    """

    """
    def __init__(self, key, kind, owner, *, validate_toml=False) -> None:
        self.key = key
        self.kind = kind
        self.owner = owner

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Task':
        return Task(self.key, self.kind, self.owner)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Task':
        return Task(**d, validate_toml=validate_toml)


class Worker:
    """

    :param status: running, finished
    :param remote_tasks: only for large tasks
    :param non_experiment_tasks: for non experiment tasks
    :param remote_processors: only for large tasks
    """
    def __init__(self, healthy, ip, name, total_gpus, last_modified, status, remote_tasks, non_experiment_tasks, remote_processors, *, validate_toml=False) -> None:
        self.healthy = healthy
        self.ip = ip
        self.name = name
        self.total_gpus = total_gpus
        self.last_modified = last_modified
        self.status = status
        self.remote_tasks = remote_tasks
        self.non_experiment_tasks = non_experiment_tasks
        self.remote_processors = remote_processors

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['remote_tasks'] = [a.dump() for a in self.remote_tasks]
        d['non_experiment_tasks'] = [a.dump() for a in self.non_experiment_tasks]
        return d

    def clone(self) -> 'Worker':
        return Worker(self.healthy, self.ip, self.name, self.total_gpus, self.last_modified, self.status, self.remote_tasks, self.non_experiment_tasks, self.remote_processors)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Worker':
        d['remote_tasks'] = [Task.load(a) for a in d['remote_tasks']]
        d['non_experiment_tasks'] = [Task.load(a) for a in d['non_experiment_tasks']]
        return Worker(**d, validate_toml=validate_toml)


class WorkerHealth:
    """

    :param status: running, finished
    :param remote_tasks: only for large tasks
    :param non_experiment_tasks: for non experiment tasks
    :param remote_processors: only for large tasks
    :param bytes_sent: total bytes sent on all interfaces
    :param bytes_received: total bytes received on all interfaces
    :param upload_speed: upload speed based on just the last check
    :param download_speed: download speed based on just the last check
    :param process_stats_time: time process stats were collected
    :param process_stats: process stats
    """
    def __init__(self, healthy, ip, name, total_gpus, last_modified, status, remote_tasks, non_experiment_tasks, remote_processors, bytes_sent, bytes_received, upload_speed, download_speed, process_stats_time, process_stats, *, validate_toml=False) -> None:
        self.healthy = healthy
        self.ip = ip
        self.name = name
        self.total_gpus = total_gpus
        self.last_modified = last_modified
        self.status = status
        self.remote_tasks = remote_tasks
        self.non_experiment_tasks = non_experiment_tasks
        self.remote_processors = remote_processors
        self.bytes_sent = bytes_sent
        self.bytes_received = bytes_received
        self.upload_speed = upload_speed
        self.download_speed = download_speed
        self.process_stats_time = process_stats_time
        self.process_stats = process_stats

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['remote_tasks'] = [a.dump() for a in self.remote_tasks]
        d['non_experiment_tasks'] = [a.dump() for a in self.non_experiment_tasks]
        return d

    def clone(self) -> 'WorkerHealth':
        return WorkerHealth(self.healthy, self.ip, self.name, self.total_gpus, self.last_modified, self.status, self.remote_tasks, self.non_experiment_tasks, self.remote_processors, self.bytes_sent, self.bytes_received, self.upload_speed, self.download_speed, self.process_stats_time, self.process_stats)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'WorkerHealth':
        d['remote_tasks'] = [Task.load(a) for a in d['remote_tasks']]
        d['non_experiment_tasks'] = [Task.load(a) for a in d['non_experiment_tasks']]
        return WorkerHealth(**d, validate_toml=validate_toml)


class WorkerID:
    """

    """
    def __init__(self, worker_ip, worker_name, *, validate_toml=False) -> None:
        self.worker_ip = worker_ip
        self.worker_name = worker_name

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'WorkerID':
        return WorkerID(self.worker_ip, self.worker_name)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'WorkerID':
        return WorkerID(**d, validate_toml=validate_toml)


class ExecutionAffinityInfo:
    """

    """
    def __init__(self, worker, kind, key, *, validate_toml=False) -> None:
        self.worker = worker
        self.kind = kind
        self.key = key

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['worker'] = self.worker.dump()
        return d

    def clone(self) -> 'ExecutionAffinityInfo':
        return ExecutionAffinityInfo(self.worker, self.kind, self.key)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExecutionAffinityInfo':
        d['worker'] = WorkerID.load(d['worker'])
        return ExecutionAffinityInfo(**d, validate_toml=validate_toml)


class HealthResponse:
    """

    :param local_task_queue_size: Active tasks for each task queue
    """
    def __init__(self, healthy, local_task_queue_size, cpu_task_queue_size, gpu_task_queue_size, workers, worker_mode, *, validate_toml=False) -> None:
        self.healthy = healthy
        self.local_task_queue_size = local_task_queue_size
        self.cpu_task_queue_size = cpu_task_queue_size
        self.gpu_task_queue_size = gpu_task_queue_size
        self.workers = workers
        self.worker_mode = worker_mode

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['workers'] = [a.dump() for a in self.workers]
        return d

    def clone(self) -> 'HealthResponse':
        return HealthResponse(self.healthy, self.local_task_queue_size, self.cpu_task_queue_size, self.gpu_task_queue_size, self.workers, self.worker_mode)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HealthResponse':
        d['workers'] = [WorkerHealth.load(a) for a in d['workers']]
        return HealthResponse(**d, validate_toml=validate_toml)


class TaskQueueResponse:
    """

    """
    def __init__(self, gpu_queue, cpu_queue, *, validate_toml=False) -> None:
        self.gpu_queue = gpu_queue
        self.cpu_queue = cpu_queue

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TaskQueueResponse':
        return TaskQueueResponse(self.gpu_queue, self.cpu_queue)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TaskQueueResponse':
        return TaskQueueResponse(**d, validate_toml=validate_toml)


class EntitySortQuery:
    """

    :param path: Path to nested field in entity, e.g. $.entity.file_size
    :param type: Type of field: 'value', 'array' or 'reference'
    :param reference_type: Kind of entity which is referenced, e.g. Model. Must be defined in `Kind` enum
    """
    def __init__(self, path, type, reference_type, *, validate_toml=False) -> None:
        self.path = path
        self.type = type
        self.reference_type = reference_type

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'EntitySortQuery':
        return EntitySortQuery(self.path, self.type, self.reference_type)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'EntitySortQuery':
        return EntitySortQuery(**d, validate_toml=validate_toml)


class PendingJobsListItem:
    """
    Entity used by frontend to persist content of side panel pending items.
    Pending item is understood as item which may require some kind of action, like click to download, or click to navigate to MLI

    :param key: Pending item key
    :param is_pending: If the job to which this pending item corresponds is still running
    :param title: Display name
    :param description: Longer job description
    :param job_key: Job key for polling function
    :param url: URL to page where pending item is running (e.g. experiment link, or prediction csv link)
    :param remotePollingProcedure: Procedure for polling progress of Async Job
    :param remoteAbortProcedure: Procedure to abort Async Job
    """
    def __init__(self, key, is_pending, title, description, job_key, url, remotePollingProcedure, remoteAbortProcedure, *, validate_toml=False) -> None:
        self.key = key
        self.is_pending = is_pending
        self.title = title
        self.description = description
        self.job_key = job_key
        self.url = url
        self.remotePollingProcedure = remotePollingProcedure
        self.remoteAbortProcedure = remoteAbortProcedure

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'PendingJobsListItem':
        return PendingJobsListItem(self.key, self.is_pending, self.title, self.description, self.job_key, self.url, self.remotePollingProcedure, self.remoteAbortProcedure)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'PendingJobsListItem':
        return PendingJobsListItem(**d, validate_toml=validate_toml)


class FeatureDotPlot:
    """
    
    MLI BYOR
    

    """
    def __init__(self, data, columns, *, validate_toml=False) -> None:
        self.data = data
        self.columns = columns

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'FeatureDotPlot':
        return FeatureDotPlot(self.data, self.columns)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FeatureDotPlot':
        return FeatureDotPlot(**d, validate_toml=validate_toml)


class BarChartPlot:
    """

    """
    def __init__(self, data, columns, *, validate_toml=False) -> None:
        self.data = data
        self.columns = columns

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'BarChartPlot':
        return BarChartPlot(self.data, self.columns)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'BarChartPlot':
        return BarChartPlot(**d, validate_toml=validate_toml)


class ExplanationDescriptor:
    """

    """
    def __init__(self, explanation_type, name, category, scope, has_local, formats, *, validate_toml=False) -> None:
        self.explanation_type = explanation_type
        self.name = name
        self.category = category
        self.scope = scope
        self.has_local = has_local
        self.formats = formats

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExplanationDescriptor':
        return ExplanationDescriptor(self.explanation_type, self.name, self.category, self.scope, self.has_local, self.formats)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplanationDescriptor':
        return ExplanationDescriptor(**d, validate_toml=validate_toml)


class ExplainerDescriptor:
    """

    """
    def __init__(self, id, name, description, model_types, can_explain, explanation_scopes, explanations, parameters, keywords, *, validate_toml=False) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.model_types = model_types
        self.can_explain = can_explain
        self.explanation_scopes = explanation_scopes
        self.explanations = explanations
        self.parameters = parameters
        self.keywords = keywords

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['explanations'] = [a.dump() for a in self.explanations]
        d['parameters'] = [a.dump() for a in self.parameters]
        return d

    def clone(self) -> 'ExplainerDescriptor':
        return ExplainerDescriptor(self.id, self.name, self.description, self.model_types, self.can_explain, self.explanation_scopes, self.explanations, self.parameters, self.keywords)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplainerDescriptor':
        d['explanations'] = [ExplanationDescriptor.load(a) for a in d['explanations']]
        d['parameters'] = [ConfigItem.load(a) for a in d['parameters']]
        return ExplainerDescriptor(**d, validate_toml=validate_toml)


class ExplainerRunJob:
    """

    """
    def __init__(self, progress, status, error, message, entity, created, duration, child_explainers_job_keys, *, validate_toml=False) -> None:
        self.progress = progress
        self.status = status
        self.error = error
        self.message = message
        self.entity = entity
        self.created = created
        self.duration = duration
        self.child_explainers_job_keys = child_explainers_job_keys

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['entity'] = self.entity.dump()
        return d

    def clone(self) -> 'ExplainerRunJob':
        return ExplainerRunJob(self.progress, self.status, self.error, self.message, self.entity, self.created, self.duration, self.child_explainers_job_keys)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplainerRunJob':
        d['entity'] = ExplainerDescriptor.load(d['entity'])
        return ExplainerRunJob(**d, validate_toml=validate_toml)


class ExplainersRunJob:
    """

    """
    def __init__(self, explainer_job_keys, mli_key, created, duration, status, progress, *, validate_toml=False) -> None:
        self.explainer_job_keys = explainer_job_keys
        self.mli_key = mli_key
        self.created = created
        self.duration = duration
        self.status = status
        self.progress = progress

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExplainersRunJob':
        return ExplainersRunJob(self.explainer_job_keys, self.mli_key, self.created, self.duration, self.status, self.progress)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplainersRunJob':
        return ExplainersRunJob(**d, validate_toml=validate_toml)


class CommonExplainerParameters:
    """
    subset of InterpretParameters relevant to generic rML BYOR explainer

    :param prediction_col: no model explanation
    :param sample_num_rows: >0 to sample, -1 to skip sampling
    """
    def __init__(self, target_col, weight_col, prediction_col, drop_cols, sample_num_rows, *, validate_toml=False) -> None:
        self.target_col = target_col
        self.weight_col = weight_col
        self.prediction_col = prediction_col
        self.drop_cols = drop_cols
        self.sample_num_rows = sample_num_rows

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'CommonExplainerParameters':
        return CommonExplainerParameters(self.target_col, self.weight_col, self.prediction_col, self.drop_cols, self.sample_num_rows)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CommonExplainerParameters':
        return CommonExplainerParameters(**d, validate_toml=validate_toml)


class CommonDaiExplainerParameters:
    """
    parameters (atop common params) of generic Driverless AI related rML BYOR explainers

    """
    def __init__(self, common_params, model, dataset, validset, testset, use_raw_features, config_overrides, sequential_execution, debug_model_errors, debug_model_errors_class, *, validate_toml=False) -> None:
        self.common_params = common_params
        self.model = model
        self.dataset = dataset
        self.validset = validset
        self.testset = testset
        self.use_raw_features = use_raw_features
        self.config_overrides = config_overrides
        self.sequential_execution = sequential_execution
        self.debug_model_errors = debug_model_errors
        self.debug_model_errors_class = debug_model_errors_class

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['common_params'] = self.common_params.dump()
        d['model'] = self.model.dump()
        d['dataset'] = self.dataset.dump()
        d['validset'] = self.validset.dump()
        d['testset'] = self.testset.dump()
        return d

    def clone(self) -> 'CommonDaiExplainerParameters':
        return CommonDaiExplainerParameters(self.common_params, self.model, self.dataset, self.validset, self.testset, self.use_raw_features, self.config_overrides, self.sequential_execution, self.debug_model_errors, self.debug_model_errors_class)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'CommonDaiExplainerParameters':
        d['common_params'] = CommonExplainerParameters.load(d['common_params'])
        d['model'] = ModelReference.load(d['model'])
        d['dataset'] = DatasetReference.load(d['dataset'])
        d['validset'] = DatasetReference.load(d['validset'])
        d['testset'] = DatasetReference.load(d['testset'])
        return CommonDaiExplainerParameters(**d, validate_toml=validate_toml)


class Explainer:
    """

    :param explainer_id: explainer ID
    :param explainer_params: declared explainer parameters as JSon string
    """
    def __init__(self, explainer_id, explainer_params, *, validate_toml=False) -> None:
        self.explainer_id = explainer_id
        self.explainer_params = explainer_params

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'Explainer':
        return Explainer(self.explainer_id, self.explainer_params)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'Explainer':
        return Explainer(**d, validate_toml=validate_toml)


class ExplainersRunSummary:
    """
    complete explainers runs descriptor (RPC API)

    """
    def __init__(self, common_params, explainers, explainer_run_jobs, *, validate_toml=False) -> None:
        self.common_params = common_params
        self.explainers = explainers
        self.explainer_run_jobs = explainer_run_jobs

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['common_params'] = self.common_params.dump()
        d['explainers'] = [a.dump() for a in self.explainers]
        d['explainer_run_jobs'] = [a.dump() for a in self.explainer_run_jobs]
        return d

    def clone(self) -> 'ExplainersRunSummary':
        return ExplainersRunSummary(self.common_params, self.explainers, self.explainer_run_jobs)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplainersRunSummary':
        d['common_params'] = CommonExplainerParameters.load(d['common_params'])
        d['explainers'] = [Explainer.load(a) for a in d['explainers']]
        d['explainer_run_jobs'] = [ExplainerRunJob.load(a) for a in d['explainer_run_jobs']]
        return ExplainersRunSummary(**d, validate_toml=validate_toml)


class ExplainerJobStatus:
    """

    """
    def __init__(self, mli_key, explainer_job_key, explainer_job, *, validate_toml=False) -> None:
        self.mli_key = mli_key
        self.explainer_job_key = explainer_job_key
        self.explainer_job = explainer_job

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['explainer_job'] = self.explainer_job.dump()
        return d

    def clone(self) -> 'ExplainerJobStatus':
        return ExplainerJobStatus(self.mli_key, self.explainer_job_key, self.explainer_job)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplainerJobStatus':
        d['explainer_job'] = ExplainerRunJob.load(d['explainer_job'])
        return ExplainerJobStatus(**d, validate_toml=validate_toml)


class FilterEntry:
    """

    """
    def __init__(self, filter_by, value, *, validate_toml=False) -> None:
        self.filter_by = filter_by
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'FilterEntry':
        return FilterEntry(self.filter_by, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FilterEntry':
        return FilterEntry(**d, validate_toml=validate_toml)


class ExplainerResultData:
    """

    """
    def __init__(self, explainer_name, data, data_type, data_format, *, validate_toml=False) -> None:
        self.explainer_name = explainer_name
        self.data = data
        self.data_type = data_type
        self.data_format = data_format

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExplainerResultData':
        return ExplainerResultData(self.explainer_name, self.data, self.data_type, self.data_format)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplainerResultData':
        return ExplainerResultData(**d, validate_toml=validate_toml)


class ExplainerResultHelp:
    """

    """
    def __init__(self, explainer_name, help, *, validate_toml=False) -> None:
        self.explainer_name = explainer_name
        self.help = help

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExplainerResultHelp':
        return ExplainerResultHelp(self.explainer_name, self.help)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplainerResultHelp':
        return ExplainerResultHelp(**d, validate_toml=validate_toml)


class ExplainerResultDataArgs:
    """

    """
    def __init__(self, param_name, value, *, validate_toml=False) -> None:
        self.param_name = param_name
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ExplainerResultDataArgs':
        return ExplainerResultDataArgs(self.param_name, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ExplainerResultDataArgs':
        return ExplainerResultDataArgs(**d, validate_toml=validate_toml)


class FramePath:
    """

    """
    def __init__(self, name, path, *, validate_toml=False) -> None:
        self.name = name
        self.path = path

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'FramePath':
        return FramePath(self.name, self.path)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'FramePath':
        return FramePath(**d, validate_toml=validate_toml)


class ColumnQuery:
    """

    :param value: Value of the column, case insensitive!
    """
    def __init__(self, column_name, value, *, validate_toml=False) -> None:
        self.column_name = column_name
        self.value = value

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ColumnQuery':
        return ColumnQuery(self.column_name, self.value)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ColumnQuery':
        return ColumnQuery(**d, validate_toml=validate_toml)


class RuntimeTaskInformation:
    """

    """
    def __init__(self, cpu_tasks, gpu_tasks, local_tasks, *, validate_toml=False) -> None:
        self.cpu_tasks = cpu_tasks
        self.gpu_tasks = gpu_tasks
        self.local_tasks = local_tasks

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['cpu_tasks'] = [a.dump() for a in self.cpu_tasks]
        d['gpu_tasks'] = [a.dump() for a in self.gpu_tasks]
        d['local_tasks'] = [a.dump() for a in self.local_tasks]
        return d

    def clone(self) -> 'RuntimeTaskInformation':
        return RuntimeTaskInformation(self.cpu_tasks, self.gpu_tasks, self.local_tasks)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'RuntimeTaskInformation':
        d['cpu_tasks'] = [TaskInfo.load(a) for a in d['cpu_tasks']]
        d['gpu_tasks'] = [TaskInfo.load(a) for a in d['gpu_tasks']]
        d['local_tasks'] = [TaskInfo.load(a) for a in d['local_tasks']]
        return RuntimeTaskInformation(**d, validate_toml=validate_toml)


class TaskInfo:
    """

    """
    def __init__(self, key, queue, queue_order, user, procedure, worker, *, validate_toml=False) -> None:
        self.key = key
        self.queue = queue
        self.queue_order = queue_order
        self.user = user
        self.procedure = procedure
        self.worker = worker

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TaskInfo':
        return TaskInfo(self.key, self.queue, self.queue_order, self.user, self.procedure, self.worker)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TaskInfo':
        return TaskInfo(**d, validate_toml=validate_toml)


class HealthAPIResponse:
    """

    :param application_id: Server instance ID
    """
    def __init__(self, api_version, server_version, application_id, timestamp, last_system_interaction, active_users, is_idle, resources, tasks, utilization, workers, *, validate_toml=False) -> None:
        self.api_version = api_version
        self.server_version = server_version
        self.application_id = application_id
        self.timestamp = timestamp
        self.last_system_interaction = last_system_interaction
        self.active_users = active_users
        self.is_idle = is_idle
        self.resources = resources
        self.tasks = tasks
        self.utilization = utilization
        self.workers = workers

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['resources'] = self.resources.dump()
        d['tasks'] = self.tasks.dump()
        d['utilization'] = self.utilization.dump()
        d['workers'] = [a.dump() for a in self.workers]
        return d

    def clone(self) -> 'HealthAPIResponse':
        return HealthAPIResponse(self.api_version, self.server_version, self.application_id, self.timestamp, self.last_system_interaction, self.active_users, self.is_idle, self.resources, self.tasks, self.utilization, self.workers)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HealthAPIResponse':
        d['resources'] = HealthAPIResourcesResponse.load(d['resources'])
        d['tasks'] = HealthAPITasksResponse.load(d['tasks'])
        d['utilization'] = HealthAPIUtilizationResponse.load(d['utilization'])
        d['workers'] = [HealthAPIWorkerResponse.load(a) for a in d['workers']]
        return HealthAPIResponse(**d, validate_toml=validate_toml)


class HealthAPIResourcesResponse:
    """

    """
    def __init__(self, cpu_cores, gpus, nodes, *, validate_toml=False) -> None:
        self.cpu_cores = cpu_cores
        self.gpus = gpus
        self.nodes = nodes

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'HealthAPIResourcesResponse':
        return HealthAPIResourcesResponse(self.cpu_cores, self.gpus, self.nodes)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HealthAPIResourcesResponse':
        return HealthAPIResourcesResponse(**d, validate_toml=validate_toml)


class HealthAPITasksResponse:
    """

    """
    def __init__(self, running, running_gpu, running_cpu, running_non_experiment, scheduled, scheduled_on_gpu, scheduled_on_cpu, *, validate_toml=False) -> None:
        self.running = running
        self.running_gpu = running_gpu
        self.running_cpu = running_cpu
        self.running_non_experiment = running_non_experiment
        self.scheduled = scheduled
        self.scheduled_on_gpu = scheduled_on_gpu
        self.scheduled_on_cpu = scheduled_on_cpu

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'HealthAPITasksResponse':
        return HealthAPITasksResponse(self.running, self.running_gpu, self.running_cpu, self.running_non_experiment, self.scheduled, self.scheduled_on_gpu, self.scheduled_on_cpu)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HealthAPITasksResponse':
        return HealthAPITasksResponse(**d, validate_toml=validate_toml)


class HealthAPIWorkerResponse:
    """

    """
    def __init__(self, name, running_tasks, running_tasks_gpu, running_tasks_cpu, running_tasks_local, scheduled_tasks, is_local, have_gpus, processors_count, local_processors_count, startup_id, cpu, memory, total_memory, available_memory, total_gpus, total_disk_size, available_disk_size, disk_limit_gb, *, validate_toml=False) -> None:
        self.name = name
        self.running_tasks = running_tasks
        self.running_tasks_gpu = running_tasks_gpu
        self.running_tasks_cpu = running_tasks_cpu
        self.running_tasks_local = running_tasks_local
        self.scheduled_tasks = scheduled_tasks
        self.is_local = is_local
        self.have_gpus = have_gpus
        self.processors_count = processors_count
        self.local_processors_count = local_processors_count
        self.startup_id = startup_id
        self.cpu = cpu
        self.memory = memory
        self.total_memory = total_memory
        self.available_memory = available_memory
        self.total_gpus = total_gpus
        self.total_disk_size = total_disk_size
        self.available_disk_size = available_disk_size
        self.disk_limit_gb = disk_limit_gb

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'HealthAPIWorkerResponse':
        return HealthAPIWorkerResponse(self.name, self.running_tasks, self.running_tasks_gpu, self.running_tasks_cpu, self.running_tasks_local, self.scheduled_tasks, self.is_local, self.have_gpus, self.processors_count, self.local_processors_count, self.startup_id, self.cpu, self.memory, self.total_memory, self.available_memory, self.total_gpus, self.total_disk_size, self.available_disk_size, self.disk_limit_gb)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HealthAPIWorkerResponse':
        return HealthAPIWorkerResponse(**d, validate_toml=validate_toml)


class HealthAPIUtilizationResponse:
    """

    """
    def __init__(self, cpu, gpu, memory, *, validate_toml=False) -> None:
        self.cpu = cpu
        self.gpu = gpu
        self.memory = memory

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'HealthAPIUtilizationResponse':
        return HealthAPIUtilizationResponse(self.cpu, self.gpu, self.memory)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'HealthAPIUtilizationResponse':
        return HealthAPIUtilizationResponse(**d, validate_toml=validate_toml)


class ListEntityQueryResponse:
    """

    """
    def __init__(self, kind, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.kind = kind
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'ListEntityQueryResponse':
        return ListEntityQueryResponse(self.kind, self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListEntityQueryResponse':
        return ListEntityQueryResponse(**d, validate_toml=validate_toml)


class UsersInsightsResponse:
    """

    """
    def __init__(self, user, datasets, experiments, directory_size_in_bytes, *, validate_toml=False) -> None:
        self.user = user
        self.datasets = datasets
        self.experiments = experiments
        self.directory_size_in_bytes = directory_size_in_bytes

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'UsersInsightsResponse':
        return UsersInsightsResponse(self.user, self.datasets, self.experiments, self.directory_size_in_bytes)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'UsersInsightsResponse':
        return UsersInsightsResponse(**d, validate_toml=validate_toml)


class AdditionalUserInfo:
    """

    """
    def __init__(self, username_claim, user_info, token_info, *, validate_toml=False) -> None:
        self.username_claim = username_claim
        self.user_info = user_info
        self.token_info = token_info

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'AdditionalUserInfo':
        return AdditionalUserInfo(self.username_claim, self.user_info, self.token_info)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'AdditionalUserInfo':
        return AdditionalUserInfo(**d, validate_toml=validate_toml)


class TritonModel:
    """

    :param host: Triton hostname
    :param model_name: model name
    :param model_desc: model description
    :param state: READY/UNAVAIL
    :param versions: all available versions
    :param platform: python/c++/java
    :param reason: unknown use
    """
    def __init__(self, host, model_name, model_desc, state, versions, platform, reason, inputs, outputs, *, validate_toml=False) -> None:
        self.host = host
        self.model_name = model_name
        self.model_desc = model_desc
        self.state = state
        self.versions = versions
        self.platform = platform
        self.reason = reason
        self.inputs = inputs
        self.outputs = outputs

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TritonModel':
        return TritonModel(self.host, self.model_name, self.model_desc, self.state, self.versions, self.platform, self.reason, self.inputs, self.outputs)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TritonModel':
        return TritonModel(**d, validate_toml=validate_toml)


class ListTritonModelQueryResponse:
    """

    """
    def __init__(self, items, offset, limit, total_count, *, validate_toml=False) -> None:
        self.items = items
        self.offset = offset
        self.limit = limit
        self.total_count = total_count

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        d['items'] = [a.dump() for a in self.items]
        return d

    def clone(self) -> 'ListTritonModelQueryResponse':
        return ListTritonModelQueryResponse(self.items, self.offset, self.limit, self.total_count)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'ListTritonModelQueryResponse':
        d['items'] = [TritonModel.load(a) for a in d['items']]
        return ListTritonModelQueryResponse(**d, validate_toml=validate_toml)


class LogFileDetails:
    """

    """
    def __init__(self, filename, resource_url, size, ctime, mtime, size_str, ctime_str, mtime_str, *, validate_toml=False) -> None:
        self.filename = filename
        self.resource_url = resource_url
        self.size = size
        self.ctime = ctime
        self.mtime = mtime
        self.size_str = size_str
        self.ctime_str = ctime_str
        self.mtime_str = mtime_str

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'LogFileDetails':
        return LogFileDetails(self.filename, self.resource_url, self.size, self.ctime, self.mtime, self.size_str, self.ctime_str, self.mtime_str)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'LogFileDetails':
        return LogFileDetails(**d, validate_toml=validate_toml)


class TelemetryData:
    """

    """
    def __init__(self, user, time_ns, text, action, data, *, validate_toml=False) -> None:
        self.user = user
        self.time_ns = time_ns
        self.text = text
        self.action = action
        self.data = data

    def dump(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d

    def clone(self) -> 'TelemetryData':
        return TelemetryData(self.user, self.time_ns, self.text, self.action, self.data)

    @staticmethod
    def load(d: dict, *, validate_toml=False) -> 'TelemetryData':
        return TelemetryData(**d, validate_toml=validate_toml)

