import warnings
from typing import List, Literal, Optional, Union

import pandas as pd
from sgqlc.operation import Operation

from ML_management.dataset_loader.dataset_loader_pattern_to_methods_map import DatasetLoaderMethodName
from ML_management.graphql import schema
from ML_management.graphql.schema import (
    DatasetLoaderInfo,
    DatasetLoaderVersionInfo,
    ObjectFilterSettings,
    ObjectVersionFilterSettings,
    TagFilterSettings,
    TimestampInterval,
)
from ML_management.graphql.send_graphql_request import send_graphql_request
from ML_management.mlmanagement.model_type import ModelType
from ML_management.mlmanagement.visibility_options import VisibilityOptions
from ML_management.sdk.object import (
    delete_object,
    delete_object_tag,
    delete_object_version,
    delete_object_version_tag,
    reset_object_tags,
    reset_object_version_tags,
    set_object_description,
    set_object_tags,
    set_object_version_description,
    set_object_version_tags,
    set_object_version_visibility,
    set_object_visibility,
)
from ML_management.sdk.sdk import _entity, _print_params_by_schema, _to_datetime


def get_dataset_loader_from_name(name: str) -> DatasetLoaderInfo:
    """
    Get dataset_loader.

    Parameters
    ----------
    name: str
        Name of the dataset_loader.

    Returns
    -------
    DatasetLoaderInfo
        DatasetLoaderInfo instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    dataset_loader_from_name = op.dataset_loader_from_name(name=name)
    _entity(dataset_loader_from_name)
    dataset_loader = send_graphql_request(op=op, json_response=False).dataset_loader_from_name
    return dataset_loader


def list_dataset_loader() -> pd.DataFrame:
    """
    List available dataset_loaders.

    Returns
    -------
    pd.DataFrame
        Pandas dataframe with list of available dataset_loaders.
    """
    op = Operation(schema.Query)
    _entity(op.list_dataset_loader)
    json_data = send_graphql_request(op)
    df = pd.DataFrame.from_dict(json_data["listDatasetLoader"])
    if not df.empty:
        df = _to_datetime(df, ["creationTimestamp", "lastUpdatedTimestamp"])
    return df


def set_dataset_loader_tags(name: str, key: str, values: list[str]) -> DatasetLoaderInfo:
    """
    Set dataset loader tags.

    Parameters
    ----------
    name: str
        Name of the model.
    key: str
        Key tag.
    values: list[str]
        Value tag.

    Returns
    -------
    DatasetLoaderInfo
        DatasetLoader instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_tags is DEPRECATED and will be REMOVED in future releases. Use set_object_tags",
        DeprecationWarning,
    )
    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return set_object_tags(aggr_id=aggr_id, key=key, values=values, model_type=ModelType.DATASET_LOADER)


def reset_dataset_loader_tags(
    name: str, key: str, values: list[str], new_key: Optional[str] = None
) -> DatasetLoaderInfo:
    """
    Reset dataset loader tags.

    Parameters
    ----------
    name: str
        Name of the model.
    key: str
        Key tag.
    values: list[str]
        Value tag.
    new_key: Optional[str] = None
        New key of a tag.


    Returns
    -------
    DatasetLoaderInfo
        DatasetLoader instance with meta information.
    """
    warnings.warn(
        "Function reset_dataset_loader_tags is DEPRECATED and will be REMOVED in future releases. "
        "Use reset_object_tags",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return reset_object_tags(
        aggr_id=aggr_id, key=key, values=values, new_key=new_key, model_type=ModelType.DATASET_LOADER
    )


def delete_dataset_loader_tag(name: str, key: str, value: Optional[str] = None) -> DatasetLoaderInfo:
    """
    Delete dataset loader tag.

    Parameters
    ----------
    name: str
        Name of the model.
    key: str
        Key tag.
    value: Optional[str]=None
        value tag.
    Returns
    -------
    DatasetLoaderInfo
        DatasetLoader instance with meta information.
    """
    warnings.warn(
        "Function delete_dataset_loader_tag is DEPRECATED and will be REMOVED in future releases. "
        "Use delete_object_tag",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return delete_object_tag(aggr_id=aggr_id, key=key, value=value, model_type=ModelType.DATASET_LOADER)


def set_dataset_loader_description(name: str, description: str) -> DatasetLoaderInfo:
    """
    Set dataset loader description.

    Parameters
    ----------
    name: str
        Name of the model.
    description: str
        Description model.

    Returns
    -------
    DatasetLoaderInfo
        DatasetLoader instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_description is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_description",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return set_object_description(aggr_id=aggr_id, description=description, model_type=ModelType.DATASET_LOADER)


def set_dataset_loader_visibility(
    name: str, visibility: Union[Literal["private", "public"], VisibilityOptions]
) -> DatasetLoaderInfo:
    """
    Set dataset loader visibility.

    Parameters
    ----------
    name: str
        Name of the dataset loader.
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        Visibility of the dataset loader.

    Returns
    -------
    DatasetLoaderInfo
        DatasetLoader instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_visibility",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return set_object_visibility(aggr_id=aggr_id, visibility=visibility, model_type=ModelType.DATASET_LOADER)


def list_dataset_loader_version(name: str) -> pd.DataFrame:
    """
    List available versions of the dataset_loader with such name.

    Parameters
    ----------
    name: str
        Name of the DatasetLoader.

    Returns
    -------
    pd.DataFrame
        Pandas dataframe with a list of available dataset_loader versions.
    """
    warnings.warn(
        "Function set_dataset_loader_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_visibility",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    base_query = op.dataset_loader_from_name(name=name).list_dataset_loader_version
    base_query.version()
    base_query.creation_timestamp()
    base_query.name()
    json_data = send_graphql_request(op)

    df = pd.DataFrame.from_dict(json_data["datasetLoaderFromName"]["listDatasetLoaderVersion"])
    df = _to_datetime(df, ["creationTimestamp"])

    return df.sort_values(by=["version"], ignore_index=True)


def delete_dataset_loader(dataset_loader_name: str) -> bool:
    """
    Delete dataset loader and all of it's versions.

    Parameters
    ----------
    dataset_loader_name: str
        Name of the dataset loader to delete.

    Returns
    -------
    bool
        Operation success status.
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )
    aggr_id = get_dataset_loader_from_name(dataset_loader_name).aggr_id
    return delete_object(aggr_id, ModelType.DATASET_LOADER)


def delete_dataset_loader_version(dataset_loader_name: str, dataset_loader_version: int):
    """
    Delete version of a dataset loader.

    Parameters
    ----------
    dataset_loader_name: str
        The name of the dataset loader.
    dataset_loader_version: int
        The version of the dataset loader.

    Returns
    -------
    None
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )
    aggr_id = get_dataset_loader_from_name(dataset_loader_name).aggr_id
    return delete_object_version(aggr_id, dataset_loader_version, ModelType.DATASET_LOADER)


def print_dataset_loader_schema(name: str, version: Optional[int] = None) -> None:
    """
    Print DatasetLoader schema.

    Parameters
    ----------
    name: str
        Name of the DatasetLoader.
    version: Optional[int] = None
        Version of the DatasetLoader. Default: None, "latest" version is used.
    """
    op = Operation(schema.Query)
    _datasetloader_version = schema.ObjectVersionOptionalInput(name=name, version=version)
    base_query = op.dataset_loader_version_from_name_version(dataset_loader_version=_datasetloader_version)
    base_query.dataset_loader_method_schemas()
    json_data = send_graphql_request(op)
    json_data = json_data["datasetLoaderVersionFromNameVersion"]["datasetLoaderMethodSchemas"]
    print(f"DatasetLoader {name} version {version} json-schema:")
    for method_name, schema_ in json_data.items():
        _print_params_by_schema(json_schema=schema_, schema_type=DatasetLoaderMethodName(method_name).name)


def set_dataset_loader_version_description(name: str, version: int, description: str) -> DatasetLoaderVersionInfo:
    """
    Set dataset loader version description.

    Parameters
    ----------
    name: str
        Name of the dataset loader.
    version: int
        Version of the dataset loader.
    description: str
        Description dataset loader version.

    Returns
    -------
    DatasetLoaderVersionInfo
        Dataset loader version instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_version_description is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_description",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return set_object_version_description(
        aggr_id=aggr_id, version=version, description=description, model_type=ModelType.DATASET_LOADER
    )


def set_dataset_loader_version_visibility(
    name: str,
    version: int,
    visibility: Union[Literal["private", "public"], VisibilityOptions],
) -> DatasetLoaderVersionInfo:
    """
    Set dataset loader version visibility.

    Parameters
    ----------
    name: str
        Name of the dataset loader.
    version: int
        Version of the dataset loader.
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        Visibility dataset loader version.

    Returns
    -------
    DatasetLoaderVersionInfo
        Dataset loader version instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return set_object_version_visibility(
        aggr_id=aggr_id, version=version, visibility=visibility, model_type=ModelType.DATASET_LOADER
    )


def set_dataset_loader_version_tags(name: str, version: int, key: str, values: list[str]) -> DatasetLoaderVersionInfo:
    """
    Set dataset loader version tags.

    Parameters
    ----------
    name: str
        Name of the dataset loader.
    version: int
        Version of the dataset loader.
    key: str
        Key tag.
    values: list[str]
        Value tag.

    Returns
    -------
    DatasetLoaderVersionInfo
        Dataset loader version instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_version_tags is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_tags",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return set_object_version_tags(
        aggr_id=aggr_id, version=version, key=key, values=values, model_type=ModelType.DATASET_LOADER
    )


def reset_dataset_loader_version_tags(
    name: str, version: int, key: str, values: list[str], new_key: Optional[str] = None
) -> DatasetLoaderVersionInfo:
    """
    Reset dataset loader version tags.

    Parameters
    ----------
    name: str
        Name of the dataset loader.
    version: int
        Version of the dataset loader.
    key: str
        Key tag.
    values: list[str]
        Value tag.
    new_key: Optional[str] = None
        New key of a tag.

    Returns
    -------
    DatasetLoaderVersionInfo
        Dataset loader version instance with meta information.
    """
    warnings.warn(
        "Function reset_dataset_loader_version_tags is DEPRECATED and will be REMOVED in future releases. "
        "Use reset_object_version_tags",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return reset_object_version_tags(
        aggr_id=aggr_id, version=version, key=key, values=values, new_key=new_key, model_type=ModelType.DATASET_LOADER
    )


def delete_dataset_loader_version_tag(
    name: str, version: int, key: str, value: Optional[str] = None
) -> DatasetLoaderVersionInfo:
    """
    Delete dataset loader version tag.

    Parameters
    ----------
    name: str
        Name of the dataset loader.
    version: int
        Version of the dataset loader.
    key: str
        Key tag.
    value: Optional[str]=None
        value tag.

    Returns
    -------
    DatasetLoaderVersionInfo
        Dataset loader version instance with meta information.
    """
    warnings.warn(
        "Function delete_dataset_loader_version_tag is DEPRECATED and will be REMOVED in future releases. "
        "Use delete_object_version_tag",
        DeprecationWarning,
    )

    aggr_id = get_dataset_loader_from_name(name).aggr_id
    return delete_object_version_tag(
        aggr_id=aggr_id, version=version, key=key, value=value, model_type=ModelType.DATASET_LOADER
    )


def get_dataset_loader_version(name: str, version: Optional[int] = None) -> DatasetLoaderVersionInfo:
    """
    Meta information about the dataset loader version by the dataset loader name and version.

    Parameters
    ----------
    name: str
        Name of the model.
    version: Optional[int] = None
        Version of the dataset loader. Default: None, "latest" version is used.

    Returns
    -------
    DatasetLoaderVersionInfo
        DatasetLoaderVersion instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    dataset_loader_version_choice = schema.ObjectVersionOptionalInput(name=name, version=version)
    base_query = op.dataset_loader_version_from_name_version(dataset_loader_version=dataset_loader_version_choice)
    base_query.name()
    base_query.version()
    base_query.tags()
    base_query.description()
    base_query.creation_timestamp()
    data = send_graphql_request(op, json_response=False)
    return data.dataset_loader_version_from_name_version


def get_dataset_loader_version_conda_env(name: str, version: int) -> dict:
    """
    Condas configuration for the dataset loader version by the dataset loader name and version.

    Parameters
    ----------
    name: str
        Name of the dataset loader.
    version: Optional[int] = None
        Version of the dataset loader. Default: None, "latest" version is used.

    Returns
    -------
    Dict
        Dict with conda configuration.
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    _model_version = schema.ObjectVersionOptionalInput(name=name, version=version)
    base_query = op.dataset_loader_version_from_name_version(dataset_loader_version=_model_version)
    base_query.get_conda_env()
    model_version = send_graphql_request(op, json_response=False)
    return model_version.dataset_loader_version_from_name_version.get_conda_env


def get_dataset_loader_version_requirements(name: str, version: int) -> list:
    """
    Requirements for the dataset loader version by the dataset loader name and version.

    Parameters
    ----------
    name: str
        Name of the dataset loader.
    version: Optional[int] = None
        Version of the dataset loader. Default: None, "latest" version is used.

    Returns
    -------
    List
        List of requirements.
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    _model_version = schema.ObjectVersionOptionalInput(name=name, version=version)
    base_query = op.dataset_loader_version_from_name_version(dataset_loader_version=_model_version)
    base_query.list_requirements()
    model_version = send_graphql_request(op, json_response=False)
    return model_version.dataset_loader_version_from_name_version.list_requirements


def get_latest_dataset_loader_version(name: str) -> DatasetLoaderVersionInfo:
    """
    Latest dataset loader version by the dataset loader name.

    Parameters
    ----------
    name: str
        Name of the dataset loader.

    Returns
    -------
    DatasetLoaderVersionInfo
        DatasetLoaderVersion instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )
    return get_dataset_loader_version(name)


def get_initial_dataset_loader_version(name: str) -> DatasetLoaderVersionInfo:
    """
    Initial dataset loader version by the dataset loader name.

    Parameters
    ----------
    name: str
        Name of the dataset loader.

    Returns
    -------
    DatasetLoaderVersionInfo
        DatasetLoaderVersion instance with meta information.
    """
    warnings.warn(
        "Function set_dataset_loader_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    version = op.dataset_loader_from_name(name=name).init_dataset_loader_version()
    version.name()
    version.version()
    version.tags()
    version.description()
    dataset_loader_version = send_graphql_request(op, json_response=False)
    return dataset_loader_version.dataset_loader_from_name.init_dataset_loader_version


def pagination_dataset_loader(
    name: Optional[str] = None,
    tag_key: Optional[str] = None,
    tag_value: Optional[str] = None,
    description: Optional[str] = None,
    visibility: Optional[VisibilityOptions] = None,
    owner_ids: Optional[list[str]] = None,
    creation_from: Optional[int] = None,
    creation_to: Optional[int] = None,
    last_updated_from: Optional[int] = None,
    last_updated_to: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[DatasetLoaderInfo]:
    """
    Search dataset loaders.

    Parameters
    ----------
    name: Optional[str]=None
        Name of the dataset loader.
    tag_key: Optional[str]=None
        Key of the dataset loader tag.
    tag_value: Optional[str]=None
        Value of the dataset loader tag.
    description: Optional[str]=None
        Description of the dataset loader.
    visibility: Optional[str]=None
        Visibility of dataset loader.
    owner_ids: Optional[list[str]]=None
        Ids of the dataset loader owner.
    creation_from: Optional[int]=None
        Creation timestamp from of the dataset loader.
    creation_to: Optional[int]=None
        Creation timestamp from of the dataset loader.
    last_updated_from: Optional[int]=None
        Last updated timestamp from of the dataset loader.
    last_updated_to: Optional[int]=None
        Last updated timestamp from of the dataset loader.
    limit: Optional[int] = None
        The maximum number of records that will be returned as a result.
    offset: Optional[int] = None
        The number of records that will be skipped before starting the selection.


    Returns
    -------
    List[DatasetLoaderInfo]
        List of DatasetLoaderInfo instance with meta information.
    """
    op = Operation(schema.Query)
    base_query = op.pagination_dataset_loader(
        limit=limit,
        offset=offset,
        filter_settings=ObjectFilterSettings(
            name=name,
            description=description,
            visibility=visibility,
            owner_ids=owner_ids,
            tag=TagFilterSettings(key=tag_key, value=tag_value),
            creation_interval=TimestampInterval(start=creation_from, end=creation_to),
            last_updated_interval=TimestampInterval(start=last_updated_from, end=last_updated_to),
        ),
    ).list_dataset_loader
    _entity(base_query)

    return send_graphql_request(op, json_response=False).pagination_dataset_loader.list_dataset_loader


def pagination_dataset_loader_version(
    name: str,
    version: Optional[int] = None,
    tag_key: Optional[str] = None,
    tag_value: Optional[str] = None,
    description: Optional[str] = None,
    visibility: Optional[VisibilityOptions] = None,
    owner_ids: Optional[list[str]] = None,
    creation_from: Optional[int] = None,
    creation_to: Optional[int] = None,
    last_updated_from: Optional[int] = None,
    last_updated_to: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[DatasetLoaderVersionInfo]:
    """
    Search dataset loader versions.

    Parameters
    ----------
    name: Optional[str]=None
        Name of the dataset loader version.
    version: Optional[int] = None
        Version of the dataset loader version.
    tag_key: Optional[str]=None
        Key of the dataset loader version tag.
    tag_value: Optional[str]=None
        Value of the dataset loader version tag.
    description: Optional[str]=None
        Description of the dataset loader version.
    visibility: Optional[str]=None
        Visibility of dataset loader version.
    owner_ids: Optional[list[str]]=None
        Ids of the dataset loader version owner.
    creation_from: Optional[int]=None
        Creation timestamp from of the dataset loader version.
    creation_to: Optional[int]=None
        Creation timestamp from of the dataset loader version.
    last_updated_from: Optional[int]=None
        Last updated timestamp from of the dataset loader version.
    last_updated_to: Optional[int]=None
        Last updated timestamp from of the dataset loader version.
    limit: Optional[int] = None
        The maximum number of records that will be returned as a result.
    offset: Optional[int] = None
        The number of records that will be skipped before starting the selection

    Returns
    -------
    List[DatasetLoaderVersionInfo]
        List of DatasetLoaderVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function pagination_dataset_loader_version is DEPRECATED and will be REMOVED in future releases. "
        "Use pagination_dataset_loader_version_from_id",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    base_query = (
        op.dataset_loader_from_name(name=name)
        .pagination_dataset_loader_version(
            limit=limit,
            offset=offset,
            filter_settings=ObjectVersionFilterSettings(
                version=version,
                description=description,
                visibility=visibility,
                owner_ids=owner_ids,
                tag=TagFilterSettings(key=tag_key, value=tag_value),
                creation_interval=TimestampInterval(start=creation_from, end=creation_to),
                last_updated_interval=TimestampInterval(start=last_updated_from, end=last_updated_to),
            ),
        )
        .list_dataset_loader_version
    )
    base_query.name()
    base_query.version()
    base_query.tags()
    base_query.description()
    return send_graphql_request(
        op, json_response=False
    ).dataset_loader_from_name.pagination_dataset_loader_version.list_dataset_loader_version


def pagination_dataset_loader_version_from_id(
    aggr_id: int,
    version: Optional[int] = None,
    tag_key: Optional[str] = None,
    tag_value: Optional[str] = None,
    description: Optional[str] = None,
    visibility: Optional[VisibilityOptions] = None,
    owner_ids: Optional[list[str]] = None,
    creation_from: Optional[int] = None,
    creation_to: Optional[int] = None,
    last_updated_from: Optional[int] = None,
    last_updated_to: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[DatasetLoaderVersionInfo]:
    """
    Search dataset loader versions.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: Optional[int] = None
        Version of the dataset loader version.
    tag_key: Optional[str]=None
        Key of the dataset loader version tag.
    tag_value: Optional[str]=None
        Value of the dataset loader version tag.
    description: Optional[str]=None
        Description of the dataset loader version.
    visibility: Optional[str]=None
        Visibility of dataset loader version.
    owner_ids: Optional[list[str]]=None
        Ids of the dataset loader version owner.
    creation_from: Optional[int]=None
        Creation timestamp from of the dataset loader version.
    creation_to: Optional[int]=None
        Creation timestamp from of the dataset loader version.
    last_updated_from: Optional[int]=None
        Last updated timestamp from of the dataset loader version.
    last_updated_to: Optional[int]=None
        Last updated timestamp from of the dataset loader version.
    limit: Optional[int] = None
        The maximum number of records that will be returned as a result.
    offset: Optional[int] = None
        The number of records that will be skipped before starting the selection

    Returns
    -------
    List[DatasetLoaderVersionInfo]
        List of DatasetLoaderVersionInfo instance with meta information.
    """
    op = Operation(schema.Query)
    base_query = (
        op.dataset_loader_from_id(aggr_id=aggr_id)
        .pagination_dataset_loader_version(
            limit=limit,
            offset=offset,
            filter_settings=ObjectVersionFilterSettings(
                version=version,
                description=description,
                visibility=visibility,
                owner_ids=owner_ids,
                tag=TagFilterSettings(key=tag_key, value=tag_value),
                creation_interval=TimestampInterval(start=creation_from, end=creation_to),
                last_updated_interval=TimestampInterval(start=last_updated_from, end=last_updated_to),
            ),
        )
        .list_dataset_loader_version
    )
    base_query.name()
    base_query.version()
    base_query.tags()
    base_query.description()
    return send_graphql_request(
        op, json_response=False
    ).dataset_loader_from_id.pagination_dataset_loader_version.list_dataset_loader_version
