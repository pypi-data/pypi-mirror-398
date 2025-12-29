import warnings
from typing import List, Literal, Optional, Union

import pandas as pd
from sgqlc.operation import Operation

from ML_management.graphql import schema
from ML_management.graphql.schema import (
    ModelInfo,
    ModelVersionInfo,
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
from ML_management.sdk.sdk import _entity, _to_datetime


def get_model_from_name(name: str) -> ModelInfo:
    """
    Get model.

    Parameters
    ----------
    name: str
        Name of the model.

    Returns
    -------
    ModelInfo
        ModelInfo instance with meta information.
    """
    warnings.warn(
        "Function get_model_from_name is DEPRECATED and will be REMOVED in future releases. "
        "Use get_object_from_name",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    model_from_name = op.model_from_name(name=name)
    _entity(model_from_name)
    model = send_graphql_request(op=op, json_response=False).model_from_name
    return model


def list_model() -> pd.DataFrame:
    """
    List available models.

    Returns
    -------
    pd.DataFrame
        Pandas dataframe with list of available models.
    """
    op = Operation(schema.Query)
    _entity(op.list_model)

    json_data = send_graphql_request(op)
    df = pd.DataFrame.from_dict(json_data["listModel"])
    if not df.empty:
        df = _to_datetime(df, ["creationTimestamp", "lastUpdatedTimestamp"])
    return df


def delete_model(model_name: str) -> bool:
    """
    Delete model and all of it's versions.

    Parameters
    ----------
    model_name: str
        Name of the model to delete.

    Returns
    -------
    bool
        Operation success status.
    """
    warnings.warn(
        "Function delete_model is DEPRECATED and will be REMOVED in future releases. Use delete_object",
        DeprecationWarning,
    )
    aggr_id = get_model_from_name(model_name).aggr_id

    return delete_object(aggr_id, ModelType.MODEL)


def set_model_tags(name: str, key: str, values: list[str]) -> ModelInfo:
    """
    Set model tags.

    Parameters
    ----------
    name: str
        Name of the model.
    key: str
        Key tag.
    values: list[str]
        Value tags.

    Returns
    -------
    ModelInfo
        ModelInfo instance with meta information.
    """
    warnings.warn(
        "Function set_model_tags is DEPRECATED and will be REMOVED in future releases. Use set_object_tags",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id
    return set_object_tags(aggr_id=aggr_id, key=key, values=values, model_type=ModelType.MODEL)


def reset_model_tags(name: str, key: str, values: list[str], new_key: Optional[str] = None) -> ModelInfo:
    """
    Reset model tags.

    Parameters
    ----------
    name: str
        Name of the model.
    key: str
        Key tag.
    values: list[str]
        Value tags.
    new_key: Optional[str] = None
        New key of a tag.


    Returns
    -------
    ModelInfo
        ModelInfo instance with meta information.
    """
    warnings.warn(
        "Function reset_model_tags is DEPRECATED and will be REMOVED in future releases. Use reset_object_tags",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id
    return reset_object_tags(aggr_id=aggr_id, key=key, values=values, new_key=new_key, model_type=ModelType.MODEL)


def delete_model_tag(name: str, key: str, value: Optional[str] = None) -> ModelInfo:
    """
    Delete model tag.

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
    ModelInfo
        ModelInfo instance with meta information.
    """
    warnings.warn(
        "Function delete_model_tag is DEPRECATED and will be REMOVED in future releases. Use delete_object_tag",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id
    return delete_object_tag(aggr_id=aggr_id, key=key, value=value, model_type=ModelType.MODEL)


def set_model_description(name: str, description: str) -> ModelInfo:
    """
    Set model description.

    Parameters
    ----------
    name: str
        Name of the model.
    description: str
        Description model.

    Returns
    -------
    ModelInfo
        ModelInfo instance with meta information.
    """
    warnings.warn(
        "Function set_model_description is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_description",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id
    return set_object_description(aggr_id=aggr_id, description=description, model_type=ModelType.MODEL)


def set_model_visibility(name: str, visibility: Union[Literal["private", "public"], VisibilityOptions]) -> ModelInfo:
    """
    Set model visibility.

    Parameters
    ----------
    name: str
        Name of the model.
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        visibility model.

    Returns
    -------
    ModelInfo
        ModelInfo instance with meta information.
    """
    warnings.warn(
        "Function set_model_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_visibility",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id
    return set_object_visibility(aggr_id=aggr_id, model_type=ModelType.MODEL, visibility=visibility)


def list_model_version(name: str) -> pd.DataFrame:
    """
    List available versions of the model with such name.

    Parameters
    ----------
    name: str
        Name of the model.

    Returns
    -------
    pd.DataFrame
        Pandas dataframe with a list of available model versions.
    """
    warnings.warn(
        "Function list_model_version is DEPRECATED and will be REMOVED in future releases. Use list_object_version",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    base_query = op.model_from_name(name=name).list_model_version
    base_query.version()
    base_query.creation_timestamp()
    base_query.name()
    json_data = send_graphql_request(op)

    df = pd.DataFrame.from_dict(json_data["modelFromName"]["listModelVersion"])
    df = _to_datetime(df, ["creationTimestamp"])

    return df.sort_values(by=["version"], ignore_index=True)


def get_model_version(name: str, version: Optional[int] = None) -> ModelVersionInfo:
    """
    Meta information about the model version by the model name and version.

    Parameters
    ----------
    name: str
        Name of the model.
    version: Optional[int] = None
        Version of the model. Default: None, "latest" version is used.

    Returns
    -------
    ModelVersionInfo
        ModelVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function get_model_version is DEPRECATED and will be REMOVED in future releases. Use get_object_version",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    _model_version = schema.ObjectVersionOptionalInput(name=name, version=version)
    base_query = op.model_version_from_name_version(model_version=_model_version)
    base_query.name()
    base_query.aggr_id()
    base_query.tags()
    base_query.version()
    base_query.build_job.status()
    base_query.build_job.build_object_name()
    base_query.available_executor_versions.name()
    base_query.available_executor_versions.version()
    model_version = send_graphql_request(op, json_response=False)
    return model_version.model_version_from_name_version


def rebuild_model_version_image(aggr_id: int, version: int) -> str:
    """
    Start building new docker image for specified model version.

    Parameters
    ----------
    aggr_id: int
        Id of the model.
    version: int
        Version of the model

    Returns
    -------
    str
        name of new docker image for specified model version.
    """
    op = Operation(schema.Mutation)
    _model_version = schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version)
    op.rebuild_model_version_image(model_version=_model_version)
    result = send_graphql_request(op=op)
    return result["rebuildModelVersionImage"]


def cancel_venv_build_job_for_model_version(aggr_id: int, model_version: int) -> bool:
    """
    Cancel running or planned build job of model's environment.

    Parameters
    ----------
    aggr_id: int
        Id of the model.
    model_version: int
        The version of the model.

    Returns
    -------
    bool
        Operation success status.
    """
    op = Operation(schema.Mutation)
    op.cancel_venv_build_job_for_model_version(aggr_id=aggr_id, version=model_version)
    return send_graphql_request(op)["cancelVenvBuildJobForModelVersion"]


def cancel_build_job_for_model_version(aggr_id: int, model_version: int) -> bool:
    """
    Cancel running or planned build job of model image.

    Parameters
    ----------
    aggr_id: int
        Id of the model.
    model_version: int
        The version of the model.

    Returns
    -------
    bool
        Operation success status.
    """
    op = Operation(schema.Mutation)
    op.cancel_build_job_for_model_version(aggr_id=aggr_id, version=model_version)
    return send_graphql_request(op)["cancelBuildJobForModelVersion"]


def delete_model_version(model_name: str, model_version: int):
    """
    Delete version of a model.

    Parameters
    ----------
    model_name: str
        The name of the model.
    model_version: int
        The version of the model.

    Returns
    -------
    None
    """
    warnings.warn(
        "Function delete_model_version is DEPRECATED and will be REMOVED in future releases. "
        "Use delete_object_version",
        DeprecationWarning,
    )
    aggr_id = get_model_from_name(model_name).aggr_id
    return delete_object_version(aggr_id, model_version, ModelType.MODEL)


def get_latest_model_version(name: str) -> ModelVersionInfo:
    """
    Latest model version by the model name.

    Parameters
    ----------
    name: str
        Name of the model.

    Returns
    -------
    ModelVersionInfo
        ModelVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function get_latest_model_version is DEPRECATED and will be REMOVED in future releases. "
        "Use get_latest_object_version",
        DeprecationWarning,
    )
    return get_model_version(name)


def get_initial_model_version(name: str) -> ModelVersionInfo:
    """
    Initial model version by the model name.

    Parameters
    ----------
    name: str
        Name of the model.

    Returns
    -------
    ModelVersionInfo
        ModelVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function get_initial_model_version is DEPRECATED and will be REMOVED in future releases. "
        "Use get_initial_object_version",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    version = op.model_from_name(name=name).init_model_version()
    version.name()
    version.version()
    version.tags()
    version.description()
    model_version = send_graphql_request(op, json_response=False).model_from_name.init_model_version
    return model_version


def serve_model(aggr_id: int, version: int, gpu: bool = False) -> str:
    """
    Start model serving in triton service.

    Parameters
    ----------
    aggr_id: int
        Name of the model.
    version: Optional[int] = None
        Version of the model. Default: None, "latest" version is used.
    gpu: bool
        Determine which device will be used: GPU or CPU. Default: False, CPU is used.

    Returns
    -------
    str:
        endpoint path to make inference requests for model version.
    """
    op = Operation(schema.Mutation)
    serving_parameters = schema.ModelServingInput(
        model_version=schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version), gpu=gpu
    )
    op.serve_model(serving_parameters=serving_parameters)
    send_graphql_request(op, timeout=None)
    return f"/v2/models/{aggr_id}/versions/{version}/infer"


def stop_model_serving(aggr_id: int, version: int) -> None:
    """
    Stop model serving in triton service.

    Parameters
    ----------
    name: str
        Name of the model.
    version: Optional[int] = None
        Version of the model. Default: None, "latest" version is used.
    """
    op = Operation(schema.Mutation)
    op.stop_model_serving(model_version=schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version))
    send_graphql_request(op=op, timeout=None)
    print("Serving has been successfully stopped.")


def check_inference_model_readiness(aggr_id: int, version: Optional[int] = None) -> Optional[str]:
    """
    Check if the model is ready to accept requests.

    Parameters
    ----------
    aggr_id: int
        Aggr_id of the model.
    version: Optional[int] = None
        Version of the model. Default: None, "latest" version is used.

    Returns
    -------
    Optional[str]:
        endpoint path to make requests if model is ready else None
    """
    op = Operation(schema.Query)
    op.is_inference_model_ready(model_version=schema.ObjectIdVersionInput(aggr_id=aggr_id, version=version))
    json_data = send_graphql_request(op=op)
    result = f"/v2/models/{aggr_id}/versions/{version}/infer" if json_data["isInferenceModelReady"] else None
    return result


def set_model_version_description(name: str, version: int, description: str) -> ModelVersionInfo:
    """
    Set model version description.

    Parameters
    ----------
    name: str
        Name of the model.
    version: int
        Version of the model.
    description: str
        Description model version.

    Returns
    -------
    ModelVersionInfo
        ModelVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function set_model_version_description is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_description",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id
    return set_object_version_description(aggr_id, version, description, ModelType.MODEL)


def set_model_version_visibility(
    name: str,
    version: int,
    visibility: Union[Literal["private", "public"], VisibilityOptions],
) -> ModelVersionInfo:
    """
    Set model version visibility.

    Parameters
    ----------
    name: str
        Name of the model.
    version: int
        Version of the model.
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        visibility model version.

    Returns
    -------
    ModelVersionInfo
        ModelVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function set_model_version_visibility is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_visibility",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id

    return set_object_version_visibility(
        aggr_id=aggr_id, version=version, visibility=visibility, model_type=ModelType.MODEL
    )


def set_model_version_tags(name: str, version: int, key: str, values: list[str]) -> ModelVersionInfo:
    """
    Set model version tags.

    Parameters
    ----------
    name: str
        Name of the model.
    version: int
        Version of the model.
    key: str
        Key tag.
    values: list[str]
        Value tag.

    Returns
    -------
    ModelVersionInfo
        ModelVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function set_model_version_tags is DEPRECATED and will be REMOVED in future releases. "
        "Use set_object_version_tags",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id

    return set_object_version_tags(aggr_id=aggr_id, version=version, key=key, values=values, model_type=ModelType.MODEL)


def reset_model_version_tags(
    name: str, version: int, key: str, values: list[str], new_key: Optional[str] = None
) -> ModelVersionInfo:
    """
    Reset model version tags.

    Parameters
    ----------
    name: str
        Name of the model.
    version: int
        Version of the model.
    key: str
        Key tag.
    values: list[str]
        Value tag.
    new_key: Optional[str] = None
        New key of a tag.

    Returns
    -------
    ModelVersionInfo
        ModelVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function reset_model_version_tags is DEPRECATED and will be REMOVED in future releases. "
        "Use reset_object_version_tags",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id

    return reset_object_version_tags(
        aggr_id=aggr_id, version=version, key=key, values=values, new_key=new_key, model_type=ModelType.MODEL
    )


def delete_model_version_tag(name: str, version: int, key: str, value: Optional[str] = None) -> ModelVersionInfo:
    """
    Delete model version tag.

    Parameters
    ----------
    name: str
        Name of the model.
    version: int
        Version of the model.
    key: str
        Key tag.
    value: Optional[str]=None
        value tag.

    Returns
    -------
    ModelVersion
        Model version instance with meta information.
    """
    warnings.warn(
        "Function delete_model_version_tag is DEPRECATED and will be REMOVED in future releases. "
        "Use delete_object_version_tag",
        DeprecationWarning,
    )

    aggr_id = get_model_from_name(name).aggr_id

    return delete_object_version_tag(aggr_id=aggr_id, version=version, key=key, value=value, model_type=ModelType.MODEL)


def get_model_version_conda_env(name: str, version: int) -> dict:
    """
    Condas configuration for the model version by the model name and version.

    Parameters
    ----------
    name: str
        Name of the model.
    version: Optional[int] = None
        Version of the model. Default: None, "latest" version is used.

    Returns
    -------
    Dict
        Dict with conda configuration.
    """
    warnings.warn(
        "Function get_model_version_conda_env is DEPRECATED and will be REMOVED in future releases. "
        "Use get_object_version_conda_env",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    _model_version = schema.ObjectVersionOptionalInput(name=name, version=version)
    base_query = op.model_version_from_name_version(model_version=_model_version)
    base_query.get_conda_env()
    model_version = send_graphql_request(op, json_response=False)
    return model_version.model_version_from_name_version.get_conda_env


def get_model_version_requirements(name: str, version: int) -> list:
    """
    Requirements for the model version by the model name and version.

    Parameters
    ----------
    name: str
        Name of the model.
    version: Optional[int] = None
        Version of the model. Default: None, "latest" version is used.

    Returns
    -------
    List
        List of requirements.
    """
    warnings.warn(
        "Function get_model_version_requirements is DEPRECATED and will be REMOVED in future releases. "
        "Use get_object_version_requirements",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    _model_version = schema.ObjectVersionOptionalInput(name=name, version=version)
    base_query = op.model_version_from_name_version(model_version=_model_version)
    base_query.list_requirements()
    model_version = send_graphql_request(op, json_response=False)
    return model_version.model_version_from_name_version.list_requirements


def pagination_model(
    name: Optional[str] = None,
    tag_key: Optional[str] = None,
    tag_value: Optional[str] = None,
    description: Optional[str] = None,
    visibility: Optional[Union[Literal["private", "public"], VisibilityOptions]] = None,
    owner_ids: Optional[list[str]] = None,
    creation_from: Optional[int] = None,
    creation_to: Optional[int] = None,
    last_updated_from: Optional[int] = None,
    last_updated_to: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[ModelInfo]:
    """
    Search models.

    Parameters
    ----------
    name: Optional[str]=None
        Name of the model.
    tag_key: Optional[str]=None
        Key of the model tag.
    tag_value: Optional[str]=None
        Value of the model tag.
    description: Optional[str]=None
        Description of the model.
    visibility: Optional[Union[Literal['private', 'public'], VisibilityOptions]]=None
        Visibility of model.
    owner_ids: Optional[list[str]]=None
        Ids of the model owner.
    creation_from: Optional[int]=None
        Creation timestamp from of the model.
    creation_to: Optional[int]=None
        Creation timestamp from of the model.
    last_updated_from: Optional[int]=None
        Last updated timestamp from of the model.
    last_updated_to: Optional[int]=None
        Last updated timestamp from of the model.
    limit: Optional[int] = None
        The maximum number of records that will be returned as a result.
    offset: Optional[int] = None
        The number of records that will be skipped before starting the selection.

    Returns
    -------
    List[ModelInfo]
        List of ModelInfo instance with meta information.
    """
    visibility = VisibilityOptions(visibility) if visibility else visibility
    op = Operation(schema.Query)
    base_query = op.pagination_model(
        filter_settings=ObjectFilterSettings(
            name=name,
            description=description,
            visibility=visibility,
            owner_ids=owner_ids,
            tag=TagFilterSettings(key=tag_key, value=tag_value),
            creation_interval=TimestampInterval(start=creation_from, end=creation_to),
            last_updated_interval=TimestampInterval(start=last_updated_from, end=last_updated_to),
        ),
        limit=limit,
        offset=offset,
    ).list_model
    _entity(base_query)

    return send_graphql_request(op, json_response=False).pagination_model.list_model


def pagination_model_version(
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
) -> List[ModelVersionInfo]:
    """
    Search model versions.

    Parameters
    ----------
    name: Optional[str]=None
        Name of the model version.
    version: Optional[int] = None
        Version of the model version.
    tag_key: Optional[str]=None
        Key of the model version tag.
    tag_value: Optional[str]=None
        Value of the model version tag.
    description: Optional[str]=None
        Description of the model version.
    visibility: Optional[str]=None
        Visibility of model version.
    owner_ids: Optional[list[str]]=None
        Ids of the model owner.
    creation_from: Optional[int]=None
        Creation timestamp from of the model version.
    creation_to: Optional[int]=None
        Creation timestamp from of the model version.
    last_updated_from: Optional[int]=None
        Last updated timestamp from of the model version.
    last_updated_to: Optional[int]=None
        Last updated timestamp from of the model version.
    limit: Optional[int] = None
        The maximum number of records that will be returned as a result.
    offset: Optional[int] = None
        The number of records that will be skipped before starting the selection.

    Returns
    -------
    List[ModelVersionInfo]
        List of ModelVersionInfo instance with meta information.
    """
    warnings.warn(
        "Function pagination_model_version is DEPRECATED and will be REMOVED in future releases. "
        "Use pagination_model_version_from_id",
        DeprecationWarning,
    )
    op = Operation(schema.Query)
    base_query = (
        op.model_from_name(name=name)
        .pagination_model_version(
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
        .list_model_version
    )
    base_query.name()
    base_query.version()
    base_query.tags()
    base_query.description()
    return send_graphql_request(op, json_response=False).model_from_name.pagination_model_version.list_model_version


def pagination_model_version_from_id(
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
) -> List[ModelVersionInfo]:
    """
    Search model versions.

    Parameters
    ----------
    aggr_id: int
        Id of the object.
    version: Optional[int] = None
        Version of the model version.
    tag_key: Optional[str]=None
        Key of the model version tag.
    tag_value: Optional[str]=None
        Value of the model version tag.
    description: Optional[str]=None
        Description of the model version.
    visibility: Optional[str]=None
        Visibility of model version.
    owner_ids: Optional[list[str]]=None
        Ids of the model owner.
    creation_from: Optional[int]=None
        Creation timestamp from of the model version.
    creation_to: Optional[int]=None
        Creation timestamp from of the model version.
    last_updated_from: Optional[int]=None
        Last updated timestamp from of the model version.
    last_updated_to: Optional[int]=None
        Last updated timestamp from of the model version.
    limit: Optional[int] = None
        The maximum number of records that will be returned as a result.
    offset: Optional[int] = None
        The number of records that will be skipped before starting the selection.

    Returns
    -------
    List[ModelVersionInfo]
        List of ModelVersionInfo instance with meta information.
    """
    op = Operation(schema.Query)
    base_query = (
        op.model_from_id(aggr_id=aggr_id)
        .pagination_model_version(
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
        .list_model_version
    )
    base_query.name()
    base_query.version()
    base_query.tags()
    base_query.description()
    return send_graphql_request(op, json_response=False).model_from_id.pagination_model_version.list_model_version
