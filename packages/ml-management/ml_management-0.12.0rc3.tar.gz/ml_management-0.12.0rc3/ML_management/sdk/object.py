from typing import Literal, Optional, Union

import pandas as pd
from sgqlc.operation import Operation

from ML_management.graphql.schema import (
    DatasetLoaderInfo,
    DatasetLoaderVersionInfo,
    ExecutorInfo,
    ExecutorVersionInfo,
    ModelInfo,
    ModelVersionInfo,
    UpdateObjectForm,
    UpdateObjectVersionForm,
    schema,
)
from ML_management.graphql.send_graphql_request import send_graphql_request
from ML_management.mlmanagement.model_type import ModelType
from ML_management.mlmanagement.visibility_options import VisibilityOptions
from ML_management.sdk.sdk import _entity, _to_datetime

_object_map = {
    ModelType.MODEL: ModelInfo,
    ModelType.DATASET_LOADER: DatasetLoaderInfo,
    ModelType.EXECUTOR: ExecutorInfo,
}

_object_version_map = {
    ModelType.MODEL: ModelVersionInfo,
    ModelType.DATASET_LOADER: DatasetLoaderVersionInfo,
    ModelType.EXECUTOR: ExecutorVersionInfo,
}


def _base_get_version(op, aggr_id, version, model_type):
    _version = schema.ObjectIdVersionOptionalInput(aggr_id=aggr_id, version=version)

    if model_type == ModelType.MODEL:
        base_query = op.model_version_from_aggr_id_version(model_version=_version)

    elif model_type == ModelType.EXECUTOR:
        base_query = op.executor_version_from_aggr_id_version(executor_version=_version)

    else:
        base_query = op.dataset_loader_version_from_aggr_id_version(dataset_loader_version=_version)

    return base_query


def get_object(
    aggr_id: int, model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL
) -> ModelInfo | ExecutorInfo | DatasetLoaderInfo:
    """
    Get object.

    Parameters
    ----------
    aggr_id: int
        Id of the object.

    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER

    Returns
    -------
    ModelInfo|ExecutorInfo|DatasetLoaderInfo
        Instance with meta information.
    """
    op = Operation(schema.Query)
    if model_type == ModelType.MODEL:
        model_from_id = op.model_from_id(aggr_id=aggr_id)
        _entity(model_from_id)
        model = send_graphql_request(op=op, json_response=False).model_from_id
        return model
    elif model_type == ModelType.EXECUTOR:
        executor_from_name = op.executor_from_id(aggr_id=aggr_id)
        _entity(executor_from_name)
        executor = send_graphql_request(op=op, json_response=False).executor_from_id
        return executor
    else:
        dataset_loader_from_name = op.dataset_loader_from_id(aggr_id=aggr_id)
        _entity(dataset_loader_from_name)
        dataset_loader = send_graphql_request(op=op, json_response=False).dataset_loader_from_id
        return dataset_loader


def list_object_version(
    aggr_id: int, model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL
) -> pd.DataFrame:
    """
    List available versions of the object with such aggr_id.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER

    Returns
    -------
    pd.DataFrame
        Pandas dataframe with a list of available object versions.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Query)

    if model_type == ModelType.MODEL:
        base_query = op.model_from_id(aggr_id=aggr_id).list_model_version

    elif model_type == ModelType.EXECUTOR:
        base_query = op.executor_from_id(aggr_id=aggr_id).list_executor_version

    else:
        base_query = op.dataset_loader_from_id(aggr_id=aggr_id).list_dataset_loader_version

    base_query.version()
    base_query.creation_timestamp()
    base_query.name()
    json_data = send_graphql_request(op)

    if model_type == ModelType.MODEL:
        df = pd.DataFrame.from_dict(json_data["modelFromId"]["listModelVersion"])

    elif model_type == ModelType.EXECUTOR:
        df = pd.DataFrame.from_dict(json_data["executorFromId"]["listExecutorVersion"])

    else:
        df = pd.DataFrame.from_dict(json_data["datasetLoaderFromId"]["listDatasetLoaderVersion"])

    df = _to_datetime(df, ["creationTimestamp"])

    return df.sort_values(by=["version"], ignore_index=True)


def get_object_version(
    aggr_id: int,
    version: Optional[int] = None,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> ModelVersionInfo | ExecutorVersionInfo | DatasetLoaderVersionInfo:
    """
    Meta information about the version by the aggr_id and version.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: Optional[int] = None
        Version of the object. Default: None, "latest" version is used.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER

    Returns
    -------
    ModelVersionInfo|ExecutorVersionInfo|DatasetLoaderVersionInfo
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Query)

    base_query = _base_get_version(op, aggr_id, version, model_type)

    if model_type == ModelType.MODEL:
        base_query.build_job.status()
        base_query.build_job.build_object_name()
        base_query.available_executor_versions.name()
        base_query.available_executor_versions.version()

    base_query.name()
    base_query.aggr_id()
    base_query.tags()
    base_query.version()
    base_query.git_info()

    model_version = send_graphql_request(op, json_response=False)

    if model_type == ModelType.MODEL:
        return model_version.model_version_from_aggr_id_version

    elif model_type == ModelType.EXECUTOR:
        return model_version.executor_version_from_aggr_id_version

    else:
        return model_version.dataset_loader_version_from_aggr_id_version


def get_object_version_conda_env(
    aggr_id: int,
    version: Optional[int] = None,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> dict:
    """
    Condas configuration for the object version by the aggr_id and version.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: Optional[int] = None
        Version of the object. Default: None, "latest" version is used.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER

    Returns
    -------
    Dict
        Dict with conda configuration.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Query)

    base_query = _base_get_version(op, aggr_id, version, model_type)
    base_query.get_conda_env()
    model_version = send_graphql_request(op, json_response=False)

    if model_type == ModelType.MODEL:
        return model_version.model_version_from_aggr_id_version.get_conda_env

    elif model_type == ModelType.EXECUTOR:
        return model_version.executor_version_from_aggr_id_version.get_conda_env

    else:
        return model_version.dataset_loader_version_from_aggr_id_version.get_conda_env


def get_object_version_requirements(
    aggr_id: int,
    version: int,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> list:
    """
    Requirements for the object version by the aggr_id and version.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: Optional[int] = None
        Version of the object. Default: None, "latest" version is used.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER

    Returns
    -------
    List
        List of requirements.
    """
    op = Operation(schema.Query)
    base_query = _base_get_version(op, aggr_id, version, model_type)

    base_query.list_requirements()
    model_version = send_graphql_request(op, json_response=False)

    if model_type == ModelType.MODEL:
        return model_version.model_version_from_aggr_id_version.list_requirements

    elif model_type == ModelType.EXECUTOR:
        return model_version.executor_version_from_aggr_id_version.list_requirements

    else:
        return model_version.dataset_loader_version_from_aggr_id_version.list_requirements


def get_initial_object_version(
    aggr_id: int, model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL
) -> ModelVersionInfo | ExecutorVersionInfo | DatasetLoaderVersionInfo:
    """
    Initial object version by the aggr_id.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER

    Returns
    -------
    ModelVersionInfo|ExecutorVersionInfo|DatasetLoaderVersionInfo
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Query)

    if model_type == ModelType.MODEL:
        base_query = op.model_from_id(aggr_id=aggr_id).init_model_version()

    elif model_type == ModelType.EXECUTOR:
        base_query = op.executor_from_id(aggr_id=aggr_id).init_executor_version()

    else:
        base_query = op.dataset_loader_from_id(aggr_id=aggr_id).init_dataset_loader_version()
    version = base_query
    version.name()
    version.version()
    version.tags()
    version.description()

    if model_type == ModelType.MODEL:
        model_version = send_graphql_request(op, json_response=False).model_from_id.init_model_version

    elif model_type == ModelType.EXECUTOR:
        model_version = send_graphql_request(op, json_response=False).executor_from_id.init_executor_version

    else:
        model_version = send_graphql_request(op, json_response=False).dataset_loader_from_id.init_dataset_loader_version

    return model_version


def set_object_tags(
    aggr_id: int,
    key: str,
    values: list[str],
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> Union[ModelInfo, DatasetLoaderInfo, ExecutorInfo]:
    """
    Set object tags.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    key: str
        Key tag.
    values: list[str]
        Value tags.

    Returns
    -------
    ModelInfo|DatasetLoaderInfo|ExecutorInfo
        Instance with meta information.
    """
    model_type = ModelType(model_type)
    op = Operation(schema.Mutation)
    set_tag = op.set_object_tags(aggr_id=aggr_id, key=key, values=values, model_type=model_type.name).__as__(
        _object_map[model_type]
    )
    _entity(set_tag)
    object_tags = send_graphql_request(op=op, json_response=False).set_object_tags
    return object_tags


def reset_object_tags(
    aggr_id: int,
    key: str,
    values: list[str],
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
    new_key: Optional[str] = None,
) -> Union[ModelInfo, DatasetLoaderInfo, ExecutorInfo]:
    """
    Reset object tags.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    key: str
        Key tag.
    values: list[str]
        Value tag.
    new_key: Optional[str] = None
        New key of a tag.


    Returns
    -------
    ModelInfo|DatasetLoaderInfo|ExecutorInfo
        Instance with meta information.
    """
    model_type = ModelType(model_type)
    op = Operation(schema.Mutation)
    set_tag = op.reset_object_tags(
        aggr_id=aggr_id, key=key, values=values, new_key=new_key, model_type=model_type.name
    ).__as__(_object_map[model_type])
    _entity(set_tag)
    object_tags = send_graphql_request(op=op, json_response=False).reset_object_tags
    return object_tags


def delete_object_tag(
    aggr_id: int,
    key: str,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
    value: Optional[str] = None,
) -> Union[ModelInfo, DatasetLoaderInfo, ExecutorInfo]:
    """
    Delete object tag.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    key: str
        Key tag.
    value: Optional[str]=None
        value tag.
    Returns
    -------
    ModelInfo|DatasetLoaderInfo|ExecutorInfo
        Instance with meta information.
    """
    model_type = ModelType(model_type)
    op = Operation(schema.Mutation)
    delete_tag = op.delete_object_tag(aggr_id=aggr_id, key=key, value=value, model_type=model_type.name).__as__(
        _object_map[model_type]
    )
    _entity(delete_tag)
    object_tag = send_graphql_request(op=op, json_response=False).delete_object_tag
    return object_tag


def set_object_description(
    aggr_id: int,
    description: str,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> Union[ModelInfo, DatasetLoaderInfo, ExecutorInfo]:
    """
    Set object description.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    description: str
        Description model.

    Returns
    -------
    ModelInfo|DatasetLoaderInfo|ExecutorInfo
        Instance with meta information.
    """
    model_type = ModelType(model_type)
    op = Operation(schema.Mutation)
    set_description = op.update_object(
        aggr_id=aggr_id,
        update_object_form=UpdateObjectForm(new_description=description),
        model_type=model_type.name,
    ).__as__(_object_map[model_type])
    _entity(set_description)

    update_object = send_graphql_request(op=op, json_response=False).update_object
    return update_object


def set_object_visibility(
    aggr_id: int,
    visibility: Union[Literal["private", "public"], VisibilityOptions],
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> Union[ModelInfo, DatasetLoaderInfo, ExecutorInfo]:
    """
    Set object visibility.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        visibility model.

    Returns
    -------
    ModelInfo|DatasetLoaderInfo|ExecutorInfo
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    set_visibility = op.update_object(
        aggr_id=aggr_id,
        model_type=model_type.name,
        update_object_form=UpdateObjectForm(new_visibility=VisibilityOptions(visibility).name),
    ).__as__(_object_map[model_type])
    _entity(set_visibility)

    update_object = send_graphql_request(op=op, json_response=False).update_object
    return update_object


def rename_object(
    aggr_id: int,
    new_name: str,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> Union[ModelInfo, DatasetLoaderInfo, ExecutorInfo]:
    """
    Rename object.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    new_name: str
        new_name object.

    Returns
    -------
    ModelInfo|DatasetLoaderInfo|ExecutorInfo
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    set_visibility = op.update_object(
        aggr_id=aggr_id,
        model_type=model_type.name,
        update_object_form=UpdateObjectForm(new_name=new_name),
    ).__as__(_object_map[model_type])
    _entity(set_visibility)

    update_object = send_graphql_request(op=op, json_response=False).update_object
    return update_object


def set_object_version_description(
    aggr_id: int,
    version: int,
    description: str,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> Union[ModelVersionInfo, ExecutorVersionInfo, DatasetLoaderVersionInfo]:
    """
    Set object version description.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: int
        Version of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER

    description: str
        Description model version.

    Returns
    -------
    Union[ ModelVersionInfo , ExecutorVersionInfo , DatasetLoaderVersionInfo]:
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    choice = schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version)
    set_description = op.update_object_version(
        object_version=choice,
        update_object_version_form=UpdateObjectVersionForm(new_description=description),
        model_type=model_type.name,
    ).__as__(_object_version_map[model_type])
    set_description.name()
    set_description.version()
    set_description.description()

    update_object = send_graphql_request(op=op, json_response=False).update_object_version
    return update_object


def set_object_version_visibility(
    aggr_id: int,
    version: int,
    visibility: Union[Literal["private", "public"], VisibilityOptions],
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> Union[ModelVersionInfo, ExecutorVersionInfo, DatasetLoaderVersionInfo]:
    """
    Set object version visibility.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: int
        Version of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        visibility model version.

    Returns
    -------
    Union[ ModelVersionInfo , ExecutorVersionInfo , DatasetLoaderVersionInfo]
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    choice = schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version)
    set_visibility = op.update_object_version(
        object_version=choice,
        update_object_version_form=UpdateObjectVersionForm(new_visibility=VisibilityOptions(visibility).name),
        model_type=model_type.name,
    ).__as__(_object_version_map[model_type])
    set_visibility.name()
    set_visibility.version()
    set_visibility.visibility()

    model = send_graphql_request(op=op, json_response=False).update_object_version
    return model


def set_object_version_tags(
    aggr_id: int,
    version: int,
    key: str,
    values: list[str],
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
) -> Union[ModelVersionInfo, ExecutorVersionInfo, DatasetLoaderVersionInfo]:
    """
    Set object version tags.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: int
        Version of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    key: str
        Key tag.
    values: list[str]
        Value tag.

    Returns
    -------
    Union[ ModelVersionInfo , ExecutorVersionInfo , DatasetLoaderVersionInfo]
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    choice = schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version)
    set_tag = op.set_object_version_tags(
        object_version=choice, key=key, values=values, model_type=model_type.name
    ).__as__(_object_version_map[model_type])
    set_tag.name()
    set_tag.version()
    set_tag.tags()
    model = send_graphql_request(op=op, json_response=False).set_object_version_tags
    return model


def reset_object_version_tags(
    aggr_id: int,
    version: int,
    key: str,
    values: list[str],
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
    new_key: Optional[str] = None,
) -> Union[ModelVersionInfo, ExecutorVersionInfo, DatasetLoaderVersionInfo]:
    """
    Reset object version tags.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: int
        Version of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    key: str
        Key tag.
    values: list[str]
        Value tag.
    new_key: Optional[str] = None
        New key of a tag.

    Returns
    -------
    Union[ ModelVersionInfo , ExecutorVersionInfo , DatasetLoaderVersionInfo]
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    choice = schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version)
    set_tag = op.reset_object_version_tags(
        object_version=choice, key=key, values=values, new_key=new_key, model_type=model_type.name
    ).__as__(_object_version_map[model_type])
    set_tag.name()
    set_tag.version()
    set_tag.tags()
    model = send_graphql_request(op=op, json_response=False).reset_object_version_tags
    return model


def delete_object_version_tag(
    aggr_id: int,
    version: int,
    key: str,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
    value: Optional[str] = None,
) -> Union[ModelVersionInfo, ExecutorVersionInfo, DatasetLoaderVersionInfo]:
    """
    Delete object version tag.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: int
        Version of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    key: str
        Key tag.
    value: Optional[str]=None
        value tag.

    Returns
    -------
    ModelVersion
        Instance with meta information.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    choice = schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version)
    delete_tag = op.delete_object_version_tag(
        object_version=choice, key=key, value=value, model_type=model_type.name
    ).__as__(_object_version_map[model_type])
    delete_tag.name()
    delete_tag.version()
    delete_tag.tags()
    model = send_graphql_request(op=op, json_response=False).delete_object_version_tag
    return model


def delete_object(
    aggr_id: int, model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL
) -> bool:
    """
    Delete object and all of it's versions.

    Parameters
    ----------
    aggr_id: int
        Name of the object to delete.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    Returns
    -------
    bool
        Operation success status.
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    op.delete_objects(aggr_ids=[aggr_id], model_type=model_type.name)
    return send_graphql_request(op)["deleteObjects"]


def delete_object_version(
    aggr_id: int,
    version: int,
    model_type: Union[Literal["model", "executor", "dataset_loader"], ModelType] = ModelType.MODEL,
):
    """
    Delete version of a object.

    Parameters
    ----------
    aggr_id: int
        The name of the object.
    version: int
        The version of the object.
    model_type: Union[Literal['model', 'executor', 'dataset_loader'] , ModelType]
        Type of the entity. Possible values: ModelType.MODEL | ModelType.EXECUTOR | ModelType.DATASET_LOADER
    Returns
    -------
    None
    """
    model_type = ModelType(model_type)

    op = Operation(schema.Mutation)
    op.delete_object_versions(aggr_id=aggr_id, versions=[version], model_type=model_type.name).__as__(
        _object_map[model_type]
    ).name()
    send_graphql_request(op, json_response=False)
